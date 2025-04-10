# Copyright notice:
#
# Copyright (C) CERN 2013-2015
#
# Copyright (C) Members of the EMI Collaboration, 2010-2013.
#   See www.eu-emi.eu for details on the copyright holders
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime, timedelta
from django.db import connection, connections, transaction
from django.views.decorators.cache import cache_page

from ftsmon.models import OptimizerEvolution
from ftsmon.views.jobs import setup_filters
from libs.jsonify import jsonify
from libs.util import get_order_by, paged

import settings
import threading
import time
import socket
import logging

log = logging.getLogger(__name__)

def _seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6

def update_overview_cache(cursor_write_cache, cursor_read, now):
    query_read = """
    SELECT COUNT(file_state) AS count, file_state, source_se, dest_se, vo_name
    FROM t_file
    WHERE file_state IN ('SUBMITTED', 'ACTIVE', 'READY', 'STAGING', 'STARTED', 'ARCHIVING')
    GROUP BY file_state, source_se, dest_se, vo_name
    ORDER BY NULL
    """

    query_write = """
    INSERT INTO t_webmon_overview_cache(count, file_state, source_se, dest_se, vo_name, timestamp)
    VALUES(%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        count = %s,
        file_state = %s,
        source_se = %s,
        dest_se = %s,
        vo_name = %s,
        timestamp = %s
    """

    query_delete = """
    DELETE FROM t_webmon_overview_cache WHERE timestamp != %s
    """

    cursor_read.execute(query_read)
    for row in cursor_read.fetchall():
        cursor_write_cache.execute(query_write,
            [
                row[0], row[1], row[2], row[3], row[4], now.strftime('%Y-%m-%d %H:%M:%S'),
                row[0], row[1], row[2], row[3], row[4], now.strftime('%Y-%m-%d %H:%M:%S')
            ]
        )
    cursor_write_cache.execute(query_delete, [now.strftime('%Y-%m-%d %H:%M:%S')])

def refresh_overview_cache():
    with connections["overview_write_cache"].cursor() as cursor_write_cache:
        # Ensure synchronization row always exists
        cursor_write_cache.execute("""
            INSERT INTO t_webmon_overview_cache_control(id)
            VALUES (1)
            ON DUPLICATE KEY UPDATE id = id
        """)

    try:
        with transaction.atomic(using="overview_write_cache"):
            with (
                connections["overview_write_cache"].cursor() as cursor_write_cache,
                connection.cursor() as cursor_read
            ):
                # Synchronize different nodes using "SELECT FOR UPDATE"
                cursor_write_cache.execute("""
                    SELECT * 
                    FROM t_webmon_overview_cache_control
                    WHERE id = 1
                    FOR UPDATE SKIP LOCKED
                """)
                row = cursor_write_cache.fetchone()
                # We've acquired the lock
                if row:
                    log.info("OverviewCacheRefresh:: Acquired the lock!")
                    now = datetime.now()
                    start = time.perf_counter()
                    update_overview_cache(cursor_write_cache, cursor_read, now)
                    elapsed = round(time.perf_counter() - start, 2)

                    cursor_write_cache.execute("""
                        UPDATE t_webmon_overview_cache_control
                        SET 
                            update_duration = %s,
                            updated_at = %s,
                            update_host = %s
                        WHERE id = 1
                    """, [elapsed,
                          now.strftime('%Y-%m-%d %H:%M:%S'),
                          socket.getfqdn()])
                    log.info(f"OverviewCacheRefresh:: updated overview cache "
                             f"at=\"{now.strftime('%Y-%m-%d %H:%M:%S')}\" "
                             f"stale_at=\"{(now + timedelta(seconds=settings.OVERVIEW_PAGE_CACHE_LIFETIME)).strftime('%Y-%m-%d %H:%M:%S')}\" "
                             f"elapsed={elapsed}s"
                    )
                else:
                    log.info("OverviewCacheRefresh:: Update already in progress (skip-locked)")
    except Exception as ex:
        log.exception(f"OverviewCacheRefresh:: Encountered exception: {ex}")


class OverviewExtended(object):
    """
    Wraps the return of overview, so when iterating, we can retrieve
    additional information.
    This way we avoid doing it for all items. Only those displayed will be queried
    (i.e. paging)
    """

    def __init__(self, not_before, objects, cursor):
        self.objects = objects
        self.not_before = not_before
        self.cursor = cursor

    def __len__(self):
        return len(self.objects)

    def _get_throughput(self, source, destination, vo):
        """
        Calculate throughput (in MiB) over this pair + vo over the last minute
        """
        try:
            time_window = timedelta(hours=int(http_request.GET['time_window']))
            not_before = datetime.utcnow() - time_window
        except:
            not_before = datetime.utcnow() - timedelta(minutes=30)


        oe = OptimizerEvolution.objects.filter(source_se=source, dest_se=destination)\
            .values('throughput', 'filesize_avg', 'active')\
            .filter(datetime__gte=not_before)\
            .order_by('-datetime')[0:1]
        if len(oe) == 0:
            return 0.0

        return oe[0]['throughput'] / 1024**2

    def __getitem__(self, indexes):
        if isinstance(indexes, slice):
            return_list = self.objects[indexes]
            for item in return_list:
                item['current'] = self._get_throughput(item['source_se'], item['dest_se'], item['vo_name'])
            return return_list
        else:
            return self.objects[indexes]

@jsonify
def get_overview(http_request):
    filters = setup_filters(http_request)
    if filters['time_window']:
        not_before = datetime.utcnow() - timedelta(hours=filters['time_window'])
    else:
        not_before = datetime.utcnow() - timedelta(hours=1)

    cursor = connection.cursor()

    # Get all pairs first
    pairs_filter = ""
    se_params = []
    if filters['source_se']:
        pairs_filter += " AND source_se = %s "
        se_params.append(filters['source_se'])
    if filters['dest_se']:
        pairs_filter += " AND dest_se = %s "
        se_params.append(filters['dest_se'])
    if filters['vo']:
        pairs_filter += " AND vo_name = %s "
        se_params.append(filters['vo'])

    # Result
    triplets = dict()
    using_cache = False
    cache_stale = False
    cache_updated_at = None
    cache_update_duration = None

    if filters['only_summary']:
        # Non terminal
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            query = """
            SELECT COUNT(file_state) as count, file_state,  vo_name
            FROM t_file
            WHERE file_state in ('SUBMITTED', 'ACTIVE', 'READY', 'STAGING', 'STARTED', 'ARCHIVING') %s
            GROUP BY file_state, vo_name order by NULL
            """ % pairs_filter
            cursor.execute(query, se_params)
        else:
            query = """
            SELECT COUNT(file_state) as count, file_state,  vo_name
            FROM t_file
            WHERE file_state in ('SUBMITTED', 'ACTIVE', 'READY', 'STAGING', 'STARTED', 'ARCHIVING') %s
            GROUP BY file_state, vo_name
            """ % pairs_filter
            cursor.execute(query, se_params)
        for row in cursor.fetchall():
            key = row[2]
            triplet = triplets.get(key, dict())
            triplet[row[1].lower()] = row[0]
            triplets[key] = triplet

        # Terminal
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            query = """
            SELECT COUNT(file_state) as count, file_state,  vo_name
            FROM t_file
            WHERE file_state in ('FINISHED', 'FAILED', 'CANCELED') %s
            AND finish_time > %%s
            GROUP BY file_state,  vo_name  order by NULL
            """ % pairs_filter
        else:
            query = """
            SELECT COUNT(file_state) as count, file_state,  vo_name
            FROM t_file
            WHERE file_state in ('FINISHED', 'FAILED', 'CANCELED') %s
            AND finish_time > %%s
            GROUP BY file_state,  vo_name
            """ % pairs_filter
        cursor.execute(query, se_params + [not_before.strftime('%Y-%m-%d %H:%M:%S')])
        for row in cursor.fetchall():
           key = row[2]
           triplet = triplets.get(key, dict())
           triplet[row[1].lower()] = row[0]
           triplets[key] = triplet
    else:
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            if settings.OVERVIEW_PAGE_CACHE:
                query = """
                SELECT count, file_state, source_se, dest_se, vo_name
                FROM t_webmon_overview_cache
                WHERE file_state IS NOT NULL %s
                """ % pairs_filter
                using_cache = True
            else:
                query = """
                SELECT COUNT(file_state) as count, file_state, source_se, dest_se, vo_name
                FROM t_file
                WHERE file_state in ('SUBMITTED', 'ACTIVE', 'READY', 'STAGING', 'STARTED', 'ARCHIVING') %s
                GROUP BY file_state, source_se, dest_se, vo_name order by NULL
                """ % pairs_filter
        else:
            query = """
            SELECT COUNT(file_state) as count, file_state, source_se, dest_se, vo_name
            FROM t_file
            WHERE file_state in ('SUBMITTED', 'ACTIVE', 'READY', 'STAGING', 'STARTED', 'ARCHIVING') %s
            GROUP BY file_state, source_se, dest_se, vo_name
            """ % pairs_filter
        cursor.execute(query, se_params)
        for row in cursor.fetchall():
            triplet_key = (row[2], row[3], row[4])
            triplet = triplets.get(triplet_key, dict())
            triplet[row[1].lower()] = row[0]
            triplets[triplet_key] = triplet

        if settings.OVERVIEW_PAGE_CACHE:
            query = """SELECT updated_at, update_duration FROM t_webmon_overview_cache_control WHERE id = 1"""
            cursor.execute(query)
            row = cursor.fetchone()
            cache_updated_at = row[0] if row else None
            cache_update_duration = row[1] if row else None
            if (
                    cache_updated_at is None or
                    cache_updated_at + timedelta(seconds=settings.OVERVIEW_PAGE_CACHE_LIFETIME) <= datetime.now()
            ):
                threading.Thread(target=refresh_overview_cache, daemon=True).start()
                cache_stale = True

        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            query = """
            SELECT COUNT(file_state) as count, file_state, source_se, dest_se, vo_name
            FROM t_file
            WHERE file_state in ('FINISHED', 'FAILED', 'CANCELED') %s
            AND finish_time > %%s
            GROUP BY file_state, source_se, dest_se, vo_name  order by NULL
            """ % pairs_filter
        else:
            query = """
            SELECT COUNT(file_state) as count, file_state, source_se, dest_se, vo_name
            FROM t_file
            WHERE file_state in ('FINISHED', 'FAILED', 'CANCELED') %s
            AND finish_time > %%s
            GROUP BY file_state, source_se, dest_se, vo_name
            """ % pairs_filter
        cursor.execute(query, se_params + [not_before.strftime('%Y-%m-%d %H:%M:%S')])
        for row in cursor.fetchall():
            triplet_key = (row[2], row[3], row[4])
            triplet = triplets.get(triplet_key, dict())
            triplet[row[1].lower()] = row[0]
            triplets[triplet_key] = triplet
    
    # Transform into a list
    objs = []
    for (triplet, obj) in iter(triplets.items()):
        if filters['only_summary']:
            obj['vo_name'] = triplet[0]
        else:
            obj['source_se'] = triplet[0]
            obj['dest_se'] = triplet[1]
            obj['vo_name'] = triplet[2]
            if 'current' not in obj and 'active' in obj:
                obj['current'] = 0
            failed = obj.get('failed', 0)
            finished = obj.get('finished', 0)
            total = failed + finished
            if total > 0:
                obj['rate'] = (finished * 100.0) / total
            else:
                obj['rate'] = 0
        objs.append(obj)

    # Ordering
    (order_by, order_desc) = get_order_by(http_request)

    if order_by == 'active':
        sorting_method = lambda o: (o.get('active', 0), o.get('submitted', 0))
    elif order_by == 'finished':
        sorting_method = lambda o: (o.get('finished', 0), o.get('failed', 0))
    elif order_by == 'failed':
        sorting_method = lambda o: (o.get('failed', 0), o.get('finished', 0))
    elif order_by == 'canceled':
        sorting_method = lambda o: (o.get('canceled', 0), o.get('finished', 0))
    elif order_by == 'staging':
        sorting_method = lambda o: (o.get('staging', 0), o.get('started', 0))
    elif order_by == 'started':
        sorting_method = lambda o: (o.get('started', 0), o.get('staging', 0))
    elif order_by == 'archiving':
        sorting_method = lambda o: (o.get('archiving', 0), o.get('staging', 0))
    elif order_by == 'rate':
        sorting_method = lambda o: (o.get('rate', 0), o.get('finished', 0))
    else:
        sorting_method = lambda o: (o.get('submitted', 0), o.get('active', 0))

    # Generate summary
    summary = {
        'submitted': sum(map(lambda o: o.get('submitted', 0), objs), 0),
        'active': sum(map(lambda o: o.get('active', 0), objs), 0),
        'ready': sum(map(lambda o: o.get('ready', 0), objs), 0),
        'finished': sum(map(lambda o: o.get('finished', 0), objs), 0),
        'failed': sum(map(lambda o: o.get('failed', 0), objs), 0),
        'canceled': sum(map(lambda o: o.get('canceled', 0), objs), 0),
        'current': sum(map(lambda o: o.get('current', 0), objs), 0),
        'staging': sum(map(lambda o: o.get('staging', 0), objs), 0),
        'started': sum(map(lambda o: o.get('started', 0), objs), 0),
        'archiving': sum(map(lambda o: o.get('archiving', 0), objs), 0),
    }
    if summary['finished'] > 0 or summary['failed'] > 0:
        summary['rate'] = (float(summary['finished']) / (summary['finished'] + summary['failed'])) * 100

    # Generate results response
    response = {
        'summary': summary
    }

    if not filters['only_summary']:
        response['overview'] = paged(
            OverviewExtended(not_before, sorted(objs, key=sorting_method, reverse=order_desc), cursor=cursor),
            http_request
        )

    if settings.OVERVIEW_PAGE_CACHE:
        response['overview_cache'] = {
            'using_cache': using_cache,
            'cache_stale': cache_stale,
            'cache_updated_at': cache_updated_at.strftime(
                '%Y-%m-%d %H:%M:%S') if cache_updated_at else None,
            'cache_update_duration': cache_update_duration,
        }

    return response
