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
from settings.common import FTS3WEB_CONFIG
import os


@jsonify
def get_linkinfo(http_request):
    if not FTS3WEB_CONFIG.getboolean('linkinfo', 'enabled'):
        return []

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
        WHERE storage = %(source_se)s AND outbound_max_active > 0
        """
    cursor.execute(query, {"source_se": source_se})
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
        WHERE file_state in ("READY", "ACTIVE") AND source_se = %(source_se)s
        """
    cursor.execute(query, {"source_se": source_se})
    source["active_transfers"] = cursor.fetchall()[0][0]
    result["source"] = source

    # Check if there is limit specific for the dest_se (inbound)
    query = """
        SELECT inbound_max_active 
        FROM t_se 
        WHERE storage = %(dest_se)s AND inbound_max_active > 0
        """
    cursor.execute(query, {"dest_se": dest_se})
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
        WHERE file_state in ("READY", "ACTIVE") AND dest_se = %(dest_se)s
        """
    cursor.execute(query, {"dest_se": dest_se})
    destination['active_transfers'] = cursor.fetchall()[0][0]
    result["destination"] = destination

    # Check Optimizer_evolution values
    # active -> optimizer decision (int)
    # actual_active -> actual_active (int)
    # rationale -> reason why (string)
    query = """
        SELECT active, actual_active, rationale
        FROM t_optimizer_evolution
        WHERE source_se = %(source_se)s AND dest_se = %(dest_se)s
        ORDER BY datetime DESC
        LIMIT 1
        """

    cursor.execute(query, {"source_se": source_se, "dest_se": dest_se})
    optimizer_output = cursor.fetchall()[0]
    optimizer['decision'] = optimizer_output[0]
    optimizer['active_transfers'] = optimizer_output[1]
    optimizer['description'] = optimizer_output[2]
    result["optimizer"] = optimizer

    def query_link_info(source, destination):
        query = """
            SELECT min_active, max_active
            FROM t_link_config
            WHERE source_se = %(source_se)s AND dest_se = %(dest_se)s
            """
        cursor.execute(query, {"source_se": source, "dest_se": destination})
        return cursor.fetchall()

    link_config_arrangements = [
        (source_se, dest_se, "specific_link"),
        (source_se, "*", "specific_link"),
        ("*", dest_se, "specific_link"),
        ("*", "*", "generic")
    ]
    link = {"active_transfers": optimizer['active_transfers']}

    for source, destination, config_type in link_config_arrangements:
        query_results = query_link_info(source=source, destination=destination)
        if len(query_results):
            link["limits"] = query_results[0]
            link["config_type"] = config_type
            break

    result["link"] = link

    # Get user DN and format
    user_dn = os.environ['SSL_CLIENT_S_DN'].split(',')
    user_dn = '/' + '/'.join(reversed(user_dn))

    # Check if USER_DN is authorized
    query = """
        SELECT DISTINCT 1 AS dn
        FROM t_authz_dn
        WHERE dn = %(user_dn)s
        """

    cursor.execute(query, {"user_dn": user_dn})
    dn_query_result = cursor.fetchall()
    result['user_dn_result'] = 1 if len(dn_query_result) else 0

    return [result]
