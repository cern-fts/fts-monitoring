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
from django.http import Http404

from ftsmon.models import OptimizerEvolution, Storage
from libs.jsonify import jsonify, jsonify_paged
from libs.util import paged

@jsonify_paged
def get_optimizer_pairs(http_request):
    # From the optimizer evolution
    from_optimizer = OptimizerEvolution.objects.filter(throughput__isnull=False)\
        .values('source_se', 'dest_se')

    if http_request.GET.get('source_se', None):
        from_optimizer = from_optimizer.filter(source_se=http_request.GET['source_se'])
    if http_request.GET.get('dest_se', None):
        from_optimizer = from_optimizer.filter(dest_se=http_request.GET['dest_se'])
    try:
        time_window = timedelta(hours=int(http_request.GET['time_window']))
    except:
        time_window = timedelta(minutes=30)

    not_before = datetime.utcnow() - time_window
    from_optimizer = from_optimizer.filter(datetime__gte=not_before)
    from_optimizer = from_optimizer.distinct()

    return from_optimizer


@jsonify
def get_optimizer_details(http_request):
    source_se = str(http_request.GET.get('source', None))
    dest_se = str(http_request.GET.get('destination', None))

    if not source_se or not dest_se:
        raise Http404

    try:
        time_window = timedelta(hours=int(http_request.GET['time_window']))
        not_before = datetime.utcnow() - time_window
    except:
        not_before = datetime.utcnow() - timedelta(minutes=30)

    optimizer = OptimizerEvolution.objects.filter(source_se=source_se, dest_se=dest_se)
    optimizer = optimizer.filter(datetime__gte=not_before)
    optimizer = optimizer.values(
        'datetime', 'active', 'ema', 'throughput', 'success',
        'filesize_avg', 'filesize_stddev',
        'rationale', 'actual_active', 'queue_size', 'diff'
    )
    optimizer = optimizer.order_by('-datetime')

    storage_info = get_storage_info(source_se, dest_se)

    return {
        'evolution': paged(optimizer, http_request),
        'storage_info': storage_info
    }

def get_storage_info(source_se, dest_se):
    source_info = {'storage': source_se}
    dest_info = {'storage': dest_se}
    cursor = connection.cursor()

    cursor.execute( """
    SELECT COUNT(*)
    FROM t_file
    WHERE source_se = %s AND file_state = 'ACTIVE'
    """,
    [source_se])
    row = cursor.fetchall()[0]
    source_info['active'] = row[0]

    cursor.execute( """
    SELECT COUNT(*)
    FROM t_file
    WHERE dest_se = %s AND file_state = 'ACTIVE'
    """,
    [dest_se])
    row = cursor.fetchall()[0]
    dest_info['active'] = row[0]

    storages = Storage.objects
    row = storages.filter(storage='*').all()
    if row.count() > 0:
        source_info['max_active'] = row[0].outbound_max_active
        dest_info['max_active'] = row[0].inbound_max_active

    row = storages.filter(storage=source_se, outbound_max_active__gt=0).all()
    if row.count() > 0:
        source_info['max_active'] = row[0].outbound_max_active

    row = storages.filter(storage=dest_se, inbound_max_active__gt=0).all()
    if row.count() > 0:
        dest_info['max_active'] = row[0].inbound_max_active

    return [source_info, dest_info]
