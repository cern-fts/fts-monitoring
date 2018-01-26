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
from django.db.models import Sum, Q
from django.http import Http404

from ftsweb.models import OptimizerEvolution, Optimizer
from authn import require_certificate
from jsonify import jsonify, jsonify_paged
from util import paged
from django import template
import settings

register = template.Library()

@register.simple_tag
def getSetting(value):
    return getattr(settings, value)

@require_certificate
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


@require_certificate
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

    return {
        'evolution': paged(optimizer, http_request),
    }
