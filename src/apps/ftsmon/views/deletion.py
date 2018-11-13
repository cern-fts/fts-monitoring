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
from django.db import connection
from django.views.decorators.cache import cache_page

from jobs_del import setup_filters
from jsonify import jsonify
from overview import OverviewExtendedDel
from util import get_order_by, paged

@jsonify
def get_deletion(http_request):
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
    if filters['vo']:
        pairs_filter += " AND vo_name = %s "
        se_params.append(filters['vo'])
    

    # Result
    triplets = dict()
   
    # Non terminal
    query = """
    SELECT COUNT(file_state) as count, file_state, source_se, vo_name
    FROM t_dm
    WHERE file_state in ('DELETE', 'STARTED') %s
    GROUP BY file_state, source_se, vo_name order by NULL
    """ % pairs_filter
    cursor.execute(query, se_params)
    for row in cursor.fetchall():
        triplet_key = (row[2], row[3])
        triplet = triplets.get(triplet_key, dict())
        triplet[row[1].lower()] = row[0]
        triplets[triplet_key] = triplet
    
    # Terminal
    query = """
    SELECT COUNT(file_state) as count, file_state, source_se, vo_name
    FROM t_dm
    WHERE file_state in ('FINISHED', 'FAILED', 'CANCELED') %s
        AND finish_time > %%s
    GROUP BY file_state, source_se, vo_name order by NULL
    """ % pairs_filter
    cursor.execute(query, se_params + [not_before.strftime('%Y-%m-%d %H:%M:%S')])
    for row in cursor.fetchall():
        triplet_key = (row[2], row[3]) # source_se, vo_name
        triplet = triplets.get(triplet_key, dict()) # source_se:______, vo_name:_____
        triplet[row[1].lower()] = row[0]

        triplets[triplet_key] = triplet



    # Transform into a list
    objs = [] 
    for (triplet, obj) in triplets.iteritems():
        obj['source_se'] = triplet[0]
        obj['vo_name'] = triplet[1]
        failed = obj.get('failed', 0)
        finished = obj.get('finished', 0)
        total = failed + finished
        if total > 0:
            obj['rate'] = (finished * 100.0) / total
        else:
            obj['rate'] = None
        objs.append(obj)
    # Ordering
    (order_by, order_desc) = get_order_by(http_request)

    if order_by == 'active':
        sorting_method = lambda o: (o.get('started', 0), o.get('delete', 0))
    elif order_by == 'finished':
        sorting_method = lambda o: (o.get('finished', 0), o.get('failed', 0))
    elif order_by == 'failed':
        sorting_method = lambda o: (o.get('failed', 0), o.get('finished', 0))
    elif order_by == 'canceled':
        sorting_method = lambda o: (o.get('canceled', 0), o.get('finished', 0))
    elif order_by == 'rate':
        sorting_method = lambda o: (o.get('rate', 0), o.get('finished', 0))
    else:
        sorting_method = lambda o: (o.get('delete', 0), o.get('active', 0))

    # Generate summary - sum of all values
    summary = {
        'submitted': sum(map(lambda o: o.get('delete', 0), objs), 0),
        'active': sum(map(lambda o: o.get('started', 0), objs), 0),
        'finished': sum(map(lambda o: o.get('finished', 0), objs), 0),
        'failed': sum(map(lambda o: o.get('failed', 0), objs), 0),
        'canceled': sum(map(lambda o: o.get('canceled', 0), objs), 0),
    }
    if summary['finished'] > 0 or summary['failed'] > 0:
        summary['rate'] = (float(summary['finished']) / (summary['finished'] + summary['failed'])) * 100

    # Return
    # tables - list of job
    return {
        'overview': paged(
            OverviewExtendedDel(not_before, sorted(objs, key=sorting_method, reverse=order_desc), cursor=cursor),
            http_request
        ),
    # sum of values (Generate summary)
        'summary': summary
    }
