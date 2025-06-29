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

from django.db import connection
from django.db.models import Q, Count
from django.http import Http404
from datetime import datetime, timedelta

from libs.util import ACTIVE_STATES, ON_HOLD_STATES
from ftsmon.models import Job, File, RetryError, DmFile, Token
from libs.util import get_order_by, ordered_field, paged, log_link
from libs.diagnosis import JobDiagnosis
from libs.jsonify import jsonify, jsonify_paged

import settings


def setup_filters(http_request):
    # Default values
    filters = {
        'state': None,
        'time_window': 1,
        'vo': None,
        'source_se': None,
        'dest_se': None,
        'source_surl': None,
        'dest_surl': None,
        'metadata': None,
        'activity': None,
        'hostname': None,
        'reason': None,
        'with_file': None,
        'diagnosis': False,
        'with_debug': False,
        'multireplica': False,
        'only_summary': False
    }

    for key in filters.keys():
        try:
            if key in http_request.GET:
                if key == 'time_window':
                    filters[key] = int(http_request.GET[key])
                elif key == 'state' or key == 'with_file':
                    if http_request.GET[key]:
                        filters[key] = http_request.GET[key].split(',')
                elif key == 'diagnosis':
                    filters[key] = http_request.GET[key] not in ('0', 'false')
                elif key == 'with_debug':
                    filters[key] = http_request.GET[key] not in ('0', 'false')
                elif key == 'multireplica':
                    filters[key] = http_request.GET[key] not in ('0', 'false')
                else:
                    filters[key] = http_request.GET[key]
        except:
            pass

    return filters


class JobListDecorator(object):
    """
    Wraps the list of jobs and appends additional information, as
    file count per state
    This way we only do it for the number that is being actually sent
    """

    def __init__(self, job_ids):
        self.job_ids = job_ids
        self.cursor = connection.cursor()

    def __len__(self):
        return len(list(self.job_ids))

    def get_job(self, job_id):
        job = {'job_id': job_id}
        self.cursor.execute(
            "SELECT submit_time, job_state, vo_name, source_se, dest_se, job_type, priority, space_token, job_finished "
            "FROM t_job WHERE job_id = %s", [job_id])
        job_desc = self.cursor.fetchall()[0]
        job['submit_time'] = job_desc[0]
        job['job_state'] = job_desc[1]
        job['vo_name'] = job_desc[2]
        job['source_se'] = job_desc[3]
        job['dest_se'] = job_desc[4]
        job['job_type'] = job_desc[5]
        job['priority'] = job_desc[6]
        job['space_token'] = job_desc[7]
        job['job_finished'] = job_desc[8]
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            self.cursor.execute(
                """SELECT file_state, COUNT(file_id), SUM(log_file_debug), MAX(file_index)
                   FROM t_file WHERE job_id = %s GROUP BY file_state ORDER BY NULL
                """,
                [job_id])
        else:
            self.cursor.execute(
                """SELECT file_state, COUNT(file_id), SUM(log_file_debug), MAX(file_index)
                   FROM t_file WHERE job_id = %s GROUP BY file_state
                """,
                [job_id])
        result = self.cursor.fetchall()
        count = dict()
        with_debug = 0
        n_replicas = 0
        total = 0
        for r in result:
            count[r[0]] = r[1]
            total += r[1]
            with_debug += r[2] if r[2] else 0
            n_replicas = max(n_replicas, r[3])
        job['files'] = count
        job['count'] = total
        job['with_debug'] = with_debug
        job['n_replicas'] = n_replicas + 1
        return job

    def _decorated(self, index):
        for job_id in list(self.job_ids)[index]:
            yield self.get_job(job_id)

    def __getitem__(self, index):
        if not isinstance(index, slice):
            index = slice(index, index, 1)

        step = index.step if index.step else 1
        nelems = (index.stop - index.start if index.start else 0) / step
        if nelems > 100:
            return self.job_ids[index]
        else:
            return self._decorated(index)
    
    def __iter__(self):
        class _Iter(object):
            def __init__(self, container):
                self.container = container
                self.job_id_iter = iter(container.job_ids)

            def next(self):
                job_id = self.job_id_iter.next()
                return self.container.get_job(job_id)

        return _Iter(self)

@jsonify_paged
def get_job_list(http_request):
    """
    This view is a little bit trickier than the others.
    We get the list of job ids from t_job or t_file depending if
    filtering by state of with_file is used.
    Luckily, the rest of fields are available in both tables
    """
    filters = setup_filters(http_request)

    if filters['with_file']:
        job_ids = File.objects.values('job_id').distinct().filter(file_state__in=filters['with_file'])
    elif filters['state']:
        job_ids = Job.objects.values('job_id').filter(job_state__in=filters['state']).order_by('-submit_time')
    else:
        job_ids = Job.objects.values('job_id').order_by('-submit_time')

    if filters['time_window']:
        not_before = datetime.utcnow() - timedelta(hours=filters['time_window'])
        if filters['with_file']:
            job_ids = job_ids.filter(Q(finish_time__gte=not_before) | Q(finish_time=None))
        else:
            job_ids = job_ids.filter(Q(job_finished__gte=not_before) | Q(job_finished=None))

    if filters['vo']:
        job_ids = job_ids.filter(vo_name=filters['vo'])
    if filters['source_se']:
        job_ids = job_ids.filter(source_se=filters['source_se'])
    if filters['dest_se']:
        job_ids = job_ids.filter(dest_se=filters['dest_se'])

    job_list = JobListDecorator([j['job_id'] for j in job_ids])
    if filters['diagnosis'] or filters['with_debug'] or filters['multireplica']:
        job_list = JobDiagnosis(job_list, filters['diagnosis'], filters['with_debug'], filters['multireplica'])
    return job_list

@jsonify
def get_job_details(http_request, job_id):
    reason = http_request.GET.get('reason', None)
    try:
        file_id = http_request.GET.get('file', None)
        if file_id is not None:
            file_id = int(file_id)
    except:
        file_id = None

    try:
        job = Job.objects.get(job_id=job_id)
        job.expiry_time = ""
        if job.max_time_in_queue is not None:
            job.expiry_time = datetime.utcfromtimestamp(job.max_time_in_queue).strftime("%Y-%m-%dT%H:%M:%SZ")
        count_files = File.objects.filter(job=job_id)
        count_dm = DmFile.objects.filter(job=job_id)
    except Job.DoesNotExist:
        raise Http404

    if reason:
        count_files = count_files.filter(reason=reason)
        count_dm = count_dm.filter(reason=reason)
    if file_id:
        count_files = count_files.filter(file_id=file_id)
        count_dm = count_dm.filter(file_id=file_id)
    count_files = count_files.values('file_state').annotate(count=Count('file_state'))
    count_dm = count_dm.values('file_state').annotate(count=Count('file_state'))

    # Set job duration
    if job.job_finished:
        job.__dict__['duration'] = job.job_finished - job.submit_time
    else:
        job.__dict__['duration'] = datetime.utcnow() - job.submit_time

    # Count as dictionary
    state_count = {}
    for st in count_files:
        state_count[st['file_state']] = st['count']
    for st in count_dm:
        state_count[st['file_state']] = st['count'] + state_count.get(st['file_state'], 0)

    return {'job': job, 'states': state_count}


class TokenFetcher(object):
    """
    Fetches token (un)managed status on demand, if necessary
    """

    def __init__(self, files):
        self.files = files

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        for f in self.files[i]:
            src_token = Token.objects.filter(token_id=f.src_token_id)
            dst_token = Token.objects.filter(token_id=f.dst_token_id)
            f.src_token = dict()
            f.dst_token = dict()
            if len(src_token) > 0:
                f.src_token = {
                    'token_id': src_token[0].token_id,
                    'unmanaged': src_token[0].unmanaged
                }
            if len(dst_token) > 0:
                f.dst_token = {
                    'token_id': dst_token[0].token_id,
                    'unmanaged': dst_token[0].unmanaged
                }
            yield f

class RetriesFetcher(object):
    """
    Fetches, on demand and if necessary, the retry error messages
    """

    def __init__(self, files):
        self.files = files

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        for f in self.files[i]:
            retries = RetryError.objects.filter(file_id=f.file_id)
            f.retries = map(lambda r: {
                'reason': r.reason,
                'datetime': r.datetime,
                'attempt': r.attempt,
                'log_file': log_link(r.transfer_host, r.log_file) if (
                        r.transfer_host and r.log_file) else None
            }, retries.all())
            yield f

class LogLinker(object):
    """
    Change the log so it is the actual link
    """

    def __init__(self, files):
        self.files = files

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        for f in self.files[i]:
            if hasattr(f, 'log_file'):
                f.log_file = (
                    log_link(f.transfer_host, f.log_file)
                    if (f.transfer_host and f.log_file)
                    else None
                )
            yield f

@jsonify
def get_job_transfers(http_request, job_id):
    try :
        files = File.objects.filter(job=job_id)
        job_type = Job.objects.get(job_id=job_id).job_type

        if not files:
            files = DmFile.objects.filter(job=job_id)
            if not files:
                raise Http404
    except Job.DoesNotExist:
        raise Http404

    # Ordering
    (order_by, order_desc) = get_order_by(http_request)
    if order_by == 'id':
        files = files.order_by(ordered_field('file_id', order_desc))
    elif order_by == 'size':
        files = files.order_by(ordered_field('filesize', order_desc))
    elif order_by == 'throughput':
        files = files.order_by(ordered_field('throughput', order_desc))
    elif order_by == 'start_time':
        files = files.order_by(ordered_field('start_time', order_desc))
    elif order_by == 'finish_time':
        files = files.order_by(ordered_field('finish_time', order_desc))
    elif order_by == 'staging_start':
        files = files.order_by(ordered_field('staging_start', order_desc))
    elif order_by == 'staging_finished':
        files = files.order_by(ordered_field('staging_finished', order_desc))

    # Pre-fetch
    files = list(files)

    # Job submission time
    submission_time = Job.objects.get(job_id=job_id).submit_time

    # Build up stats
    now = datetime.utcnow()
    first_start_time = min(map(lambda f: f.get_start_time(), filter(lambda f: f.get_start_time(), files)), default=None)
    running_time = timedelta(0)

    if first_start_time:
        if files[0].finish_time:
            running_time = files[0].finish_time - first_start_time
        else:
            running_time = now - first_start_time

    running_time = (running_time.seconds + running_time.days * 24 * 3600)

    files_transferred = sum(map(lambda f: f.file_state == 'FINISHED', files))
    bytes_transferred = sum(map(lambda f: f.transferred if f.transferred else 0, files))
    with_throughputs = list(filter(lambda f: f.throughput, files))
    actives_throughput = list(filter(lambda f: f.file_state == 'ACTIVE', with_throughputs))

    stats = {
        'files_transferred': files_transferred,
        'total_files_to_transfer' : len(files) if job_type != 'R' else 1,
        'bytes_transferred': bytes_transferred,
        'first_start': first_start_time
    }

    if first_start_time:
        stats['queued_first'] = first_start_time - submission_time
    else:
        stats['queued_first'] = now - submission_time

    if running_time:
        stats['time_transfering'] = running_time
    if len(actives_throughput):
        stats['current_throughput'] = sum(map(lambda f: f.throughput, actives_throughput))
    if len(with_throughputs):
        stats['avg_throughput'] = sum(map(lambda f: f.throughput, with_throughputs)) / len(with_throughputs)

    # Now we got the stats, apply filters
    if http_request.GET.get('state', None):
        files = list(filter(lambda f: f.file_state in http_request.GET['state'].split(','), files))
    if http_request.GET.get('reason', None):
        files = list(filter(lambda f: f.reason == http_request.GET['reason'], files))
    if http_request.GET.get('file', None):
        try:
            file_id = int(http_request.GET['file'])
            files = list(filter(lambda f: f.file_id == file_id, files))
        except:
            pass

    return {
        'files': paged(TokenFetcher(RetriesFetcher(LogLinker(files))), http_request),
        'stats': stats
    }


def _contains_active_state(state_filer):
    # Consider empty a list with active states (because all are in)
    if not state_filer:
        return True
    return [x for x in state_filer if x in ACTIVE_STATES+ON_HOLD_STATES]

@jsonify_paged
def get_transfer_list(http_request):
    filters = setup_filters(http_request)

    transfers = File.objects
    if filters['state']:
        transfers = transfers.filter(file_state__in=filters['state'])
    else:
        transfers = transfers.exclude(file_state='NOT_USED')
    if filters['source_se']:
        transfers = transfers.filter(source_se=filters['source_se'])
    if filters['dest_se']:
        transfers = transfers.filter(dest_se=filters['dest_se'])
    if filters['source_surl']:
        transfers = transfers.filter(source_surl=filters['source_surl'])
    if filters['dest_surl']:
        transfers = transfers.filter(dest_surl=filters['dest_surl'])
    if filters['vo']:
        transfers = transfers.filter(vo_name=filters['vo'])
    if filters['time_window']:
        not_before = datetime.utcnow() - timedelta(hours=filters['time_window'])
        # Avoid querying for job_finished is NULL if there are no active states
        if _contains_active_state(filters['state']):
            transfers = transfers.filter(Q(finish_time__isnull=True) | (Q(finish_time__gte=not_before)))
        else:
            transfers = transfers.filter(Q(finish_time__gte=not_before))
    if filters['activity']:
        transfers = transfers.filter(activity=filters['activity'])
    if filters['hostname']:
        transfers = transfers.filter(transfer_host=filters['hostname'])
    if filters['reason']:
        transfers = transfers.filter(reason=filters['reason'])

    transfers = transfers.values(
        'file_id', 'file_state', 'job_id',
        'source_se', 'dest_se', 'start_time', 'finish_time',
        'activity', 'user_filesize', 'filesize'
    )

    # Ordering
    (order_by, order_desc) = get_order_by(http_request)
    if order_by == 'id':
        transfers = transfers.order_by(ordered_field('file_id', order_desc))
    elif order_by == 'start_time':
        transfers = transfers.order_by(ordered_field('start_time', order_desc))
    elif order_by == 'finish_time':
        transfers = transfers.order_by(ordered_field('finish_time', order_desc))
    else:
        transfers = transfers.order_by('-finish_time')

    return transfers
