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

from ftsmon.views.jobs import setup_filters
from libs.jsonify import jsonify
from django.http import Http404
from django.db import connection
import os


@jsonify
def get_linkinfo(http_request):
    source_se = str(http_request.GET.get('source_se', None))
    dest_se = str(http_request.GET.get('dest_se', None))
   
    if not source_se or not dest_se:
        raise Http404

    cursor = connection.cursor()

    result = {}
    source = {}
    destination = {}
    optimizer = {}

    # t_se -> Storage config limits
    # t_link -> Link config limits
    # t_file -> Where all the transfers are (including active ones)
    
    # Check the default outbound limit for all SEs
    query = """
        SELECT inbound_max_active, outbound_max_active
        FROM t_se 
        WHERE storage = '*'
        """    
    cursor.execute(query)
    generic_se_active_limits = cursor.fetchall()

    # Check if there is limit specific for the SE (outbound)
    query = """
        SELECT outbound_max_active 
        FROM t_se 
        WHERE storage = '%s' AND outbound_max_active > 0
        """ % source_se
    cursor.execute(query)
    source["outbound_limit"] = cursor.fetchall()
    
    # If the limit is not set conf_type = generic
    if not source["outbound_limit"]:
        source["outbound_limit"] = generic_se_active_limits[0][1]
        source["config_type"] = "generic"
    else:
        source["outbound_limit"] = source["outbound_limit"][0][0]
        source["config_type"] = "specific"

    # Active transfers for the source
    query = """
        SELECT count(*) 
        FROM t_file 
        WHERE file_state in ("READY", "ACTIVE") AND source_se = '%s'
        """ % source_se
    cursor.execute(query)
    source["active_transfers"] = cursor.fetchall()[0][0]
    result["source"] = source

    # Check if there is limit specific for the dest_se (inbound)
    query = """
        SELECT inbound_max_active 
        FROM t_se 
        WHERE storage = '%s' AND inbound_max_active > 0
        """ % dest_se
    cursor.execute(query)
    destination["inbound_limit"] = cursor.fetchall()

    # If the limit is not set conf_type = generic
    if not destination["inbound_limit"]:
        destination["inbound_limit"] = generic_se_active_limits[0][0]
        destination["config_type"] = "generic"
    else:
        destination["inbound_limit"] = destination["inbound_limit"][0][0]
        destination["config_type"] = "specific"

    # Active transfers for the destination
    query = """
        SELECT count(*) 
        FROM t_file 
        WHERE file_state in ("READY", "ACTIVE") AND dest_se = '%s'
        """ % dest_se
    cursor.execute(query)
    destination['active_transfers'] = cursor.fetchall()[0][0]
    result["destination"] = destination

    # Check Optimizer_evolution values
    # active -> optimizer decision (int)
    # actual_active -> actual_active (int)
    # rationale -> reason why (string)
    query = """
        SELECT active, actual_active, rationale
        FROM t_optimizer_evolution
        WHERE dest_se = '%s' AND source_se = '%s'
        ORDER BY datetime DESC
        LIMIT 1
        """ % (dest_se, source_se)

    cursor.execute(query)
    optimizer_output = cursor.fetchall()[0]
    optimizer['decision'] = optimizer_output[0]
    optimizer['active_transfers'] = optimizer_output[1]
    optimizer['description'] = optimizer_output[2]
    result["optimizer"] = optimizer

    def query_link_info(source='*', destination='*'):
        query = """
            SELECT min_active, max_active
            FROM t_link_config
            WHERE source_se = '%s' AND dest_se = '%s'
            """ % (source, destination)
        cursor.execute(query)
        return cursor.fetchall()

    link = {
        "active_transfers": optimizer['active_transfers'],
        "config_type": "specific_link"
    }

    # Check Link config from the source_se -> dest_se
    query_results = query_link_info(source=source_se, destination=dest_se)
    if len(query_results):
        link["limits"] = query_results[0]
    else:
        # Check Link config from the source_se -> *
        query_results = query_link_info(source=source_se, destination="*")
        if len(query_results):
            link["limits"] = query_results[0]
            query_results = query_link_info(source="*", destination=dest_se)
            if len(query_results):
                link["limits"] = query_results[0]
                # Check Link config from the * -> *
                query_results = query_link_info(source="*", destination="*")
                if len(query_results):
                    link["limits"] = query_results[0]
                    link["config_type"] = "generic"

    result["link"] = link

    # Get user DN and format
    user_dn = os.environ['SSL_CLIENT_S_DN'].split(',')
    user_dn = '/' + '/'.join(reversed(user_dn))

    # Check if USER_DN is authorized
    query = """
        SELECT DISTINCT 1 AS dn
        FROM t_authz_dn
        WHERE dn = '%s'
        """ % user_dn

    cursor.execute(query)
    dn_query_result = cursor.fetchall()
    result['user_dn_result'] = 1 if len(dn_query_result) else 0

    return [result]
