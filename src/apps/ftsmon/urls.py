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

from django.urls import include, re_path
from ftsmon.views import *


urlpatterns = [
    re_path(r'^$', index.index, name='index'),
    re_path(r'^version$', index.version, name='version'),

    re_path(r'^overview$', overview.get_overview, name='get_overview'),
    re_path(r'^overview/activities$', activities.get_overview, name='get_overview'),
    re_path(r'^linkinfo$', linkinfo.get_linkinfo, name='get_linkinfo'),

    re_path(r'^jobs/?$',                               jobs.get_job_list, name='get_job_list'),
    re_path(r'^jobs/(?P<job_id>[a-fA-F0-9\-]+)$',       jobs.get_job_details, name='get_job_details'),
    re_path(r'^jobs/(?P<job_id>[a-fA-F0-9\-]+)/files$', jobs.get_job_transfers, name='get_job_transfers'),

    re_path(r'^transfers$', jobs.get_transfer_list, name='get_transfer_list'),

    re_path(r'^config/audit$',    config.get_audit, name='get_audit'),
    re_path(r'^config/storages$', config.get_se_config, name='get_se_config'),
    re_path(r'^config/ops',     config.get_ops_config, name='get_ops_config'),
    re_path(r'^config/links$',  config.get_link_config, name='get_link_config'),
    re_path(r'^config/server$', config.get_server_config, name='get_server_config'),
    re_path(r'^config/gfal2$',  config.get_gfal2_config, name='get_gfal2_config'),
    re_path(r'^config/activities$', config.get_activities, name='get_activities'),
    re_path(r'^config/activities/(?P<vo>(.+))$', config.get_actives_per_activity, name='get_actives_per_activity'),

    re_path(r'^stats$',            statistics.get_overview, name='get_overview'),
    re_path(r'^stats/servers$',    statistics.get_servers, name='get_servers'),
    re_path(r'^stats/vo$',         statistics.get_pervo, name='get_pervo'),

    re_path(r'^optimizer$',         optimizer.get_optimizer_pairs, name='get_optimizer_pairs'),
    re_path(r'^optimizer/detailed$', optimizer.get_optimizer_details, name='get_optimizer_details'),

    re_path(r'^errors$',     errors.get_errors, name='get_errors'),
    re_path(r'^errors/list$', errors.get_errors_for_pair, name='get_errors_for_pair'),

    re_path(r'^unique/activities',   autocomplete.get_unique_activities, name='get_unique_activities'),
    re_path(r'^unique/destinations', autocomplete.get_unique_destinations, name='get_unique_destinations'),
    re_path(r'^unique/sources',      autocomplete.get_unique_sources, name='get_unique_sources'),
    re_path(r'^unique/vos',          autocomplete.get_unique_vos, name='get_unique_vos'),
    re_path(r'^unique/hostnames',    autocomplete.get_unique_hostnames, name='get_unique_hostnames')
]
