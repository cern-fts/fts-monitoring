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

import json
import os
from django.db import connection
from django.db.models import Count
from django.http import Http404

from ftsmon.models import ActivityShare, File, OperationLimit
from ftsmon.models import ConfigAudit
from ftsmon.models import LinkConfig, ShareConfig, Storage
from libs.jsonify import jsonify, jsonify_paged
from settings.common import FTS3WEB_CONFIG

@jsonify_paged
def get_audit(http_request):
    ca = ConfigAudit.objects

    if http_request.GET.get('action', None):
        ca = ca.filter(action=http_request.GET['action'])
    if http_request.GET.get('contains', None):
        ca = ca.filter(config__icontains=http_request.GET['contains'])

    return ca.order_by('-datetime')


@jsonify
def get_server_config(http_request):
    config = dict()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT retry, max_time_queue, global_timeout, sec_per_mb, vo_name
        FROM t_server_config
    """)
    server_config = cursor.fetchall()
    config['per_vo'] = list()
    for entry in server_config:
        c = dict(
            retry=entry[0],
            max_time_queue=entry[1],
            global_timeout=entry[2],
            sec_per_mb=entry[3],
            vo_name=entry[4]
        )
        config['per_vo'].append(c)
    return config


@jsonify_paged
def get_se_config(http_request):
    return Storage.objects.all()


@jsonify
def get_ops_config(http_request):
    return OperationLimit.objects.all()


# Wrap a list of link config, and push the
# vo shares on demand (lazy!)
class AppendShares:

    def __init__(self, result_set):
        self.rs = result_set

    def __len__(self):
        return len(self.rs)

    def __getitem__(self, i):
        for link in self.rs[i]:
            shares = ShareConfig.objects.filter(source=link.source_se, destination=link.dest_se).all()
            link.shares = {}
            for share in shares:
                link.shares[share.vo] = share.active
            yield link

@jsonify_paged
def get_link_config(http_request):
    links = LinkConfig.objects

    if http_request.GET.get('source_se'):
        links = links.filter(source_se=http_request.GET['source_se'])
    if http_request.GET.get('dest_se'):
        links = links.filter(dest_se=http_request.GET['dest_se'])

    return AppendShares(links.all())

@jsonify
def get_activities(http_request):
    rows = ActivityShare.objects.all()
    per_vo = dict()
    for row in rows:
        share = per_vo.get(row.vo, dict())
        for entry in json.loads(row.activity_share):
            for share_name, share_value in iter(entry.items()):
                share[share_name] = share_value
        per_vo[row.vo] = share
    return per_vo


@jsonify
def get_actives_per_activity(http_request, vo):
    try:
        active = File.objects.filter(vo_name = vo, finish_time__isnull=True)
    except:
        raise Http404

    if http_request.GET.get('source_se', None):
        active = active.filter(source_se = http_request.GET['source_se'])
    if http_request.GET.get('dest_se', None):
        active = active.filter(dest_se = http_request.GET['dest_se'])

    active = active .exclude(file_state='NOT_USED')\
            .values('activity', 'file_state').annotate(count=Count('activity')).values('activity', 'file_state', 'count')

    grouped = dict()
    for row in active:
        activity = row['activity']
        info = grouped.get(activity, dict(count=dict()))
        info['count'][row['file_state']] = row['count']
        grouped[activity] = info

    # Find config
    share_config = dict()
    try:
        share_db = ActivityShare.objects.get(vo = vo)
    except:
        raise Http404

    if share_db is not None:
        for entry in json.loads(share_db.activity_share):
            for share_name, share_value in iter(entry.items()):
                share_config[share_name.lower()] = share_value

    weight_sum = 0
    for activity in grouped.keys():
        if activity.lower() in share_config and grouped[activity]['count'].get('SUBMITTED', 0) > 0:
            weight_sum += share_config.get(activity.lower(), 0)

    for activity in grouped.keys():
        if activity.lower() not in share_config:
            grouped[activity]['notes'] = 'Activity not configured. Fallback to default.'
        else:
            grouped[activity]['weight'] = share_config[activity.lower()]
            if grouped[activity]['count'].get('SUBMITTED', 0) > 0:
                grouped[activity]['ratio'] = share_config[activity.lower()] / weight_sum

    return grouped


@jsonify
def get_gfal2_config(http_request):
    if not FTS3WEB_CONFIG.getboolean('site', 'show_gfal2_config'):
        return dict()

    try:
        config_files = os.listdir('/etc/gfal2.d')
    except:
        config_files = list()
    config_files = list(filter(lambda c: c.endswith('.conf'), config_files))

    config = dict()
    for cfg in config_files:
        cfg_path = os.path.join('/etc/gfal2.d', cfg)
        config[cfg_path] = open(cfg_path).read()

    return config
