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

    #Result
    result = {}

    # Run queries for source SE outbound settings
    #
    # t_se -> Storage config limits
    # t_link -> Link config limits
    # t_file -> Where all the transfers are (including active ones)
    #
    # Check if there is limit specifc for the SE (outbound)
    query = """
        SELECT outbound_max_active 
        FROM t_se 
        WHERE storage = '%s' ;
        """ % source_se

    cursor.execute(query)
    result['outbound_max_active_source'] = cursor.fetchall()


    # Check the default outbound limit for all SEs
    query = """
        SELECT outbound_max_active 
        FROM t_se 
        WHERE storage = '*' ;
        """

    cursor.execute(query)
    result['outbound_max_active_all'] =  cursor.fetchall()

    # Active transfers for the destination
    query = """
        SELECT count(*) 
        FROM t_file 
        WHERE file_state in ("READY", "ACTIVE") AND dest_se = '%s' ;
        """ % dest_se

    cursor.execute(query)
    result['active_transfers_dest'] =  cursor.fetchall()

    # Active transfers for the source
    query = """
        SELECT count(*) 
        FROM t_file 
        WHERE file_state in ("READY", "ACTIVE") AND source_se = '%s' ;
        """ % source_se

    cursor.execute(query)
    result['active_transfers_source'] =  cursor.fetchall()

    # Active transfers for the destination
    query = """
        SELECT count(*) 
        FROM t_file 
        WHERE file_state in ("READY", "ACTIVE") AND dest_se ="%s";
        """ % dest_se

    cursor.execute(query)
    result['active_transfers_dest'] =  cursor.fetchall()

    # Check Optimizer_evolution values
    # active -> optimizer decision (int)
    # actual_active -> actual_active (int)
    # rationale -> reason why (string)
    query = """
        SELECT active, actual_active, rationale
        FROM t_optimizer_evolution
        WHERE dest_se = '%s' AND source_se = '%s'
        ORDER BY datetime DESC
        LIMIT 1;
        """ % (dest_se, source_se)

    cursor.execute(query)
    result['optimizer_evolution'] =  cursor.fetchall()

    # Check Link config from the source_se -> dest_se
    # 
    # WHERE source_se = "davs://dcgftp.usatlas.bnl.gov" AND dest_se="gclouds://atlas-google-cloud.cern.ch";
    query = """
        SELECT min_active, max_active
        FROM t_link_config 
        WHERE source_se = '%s' AND dest_se ='%s' ;
        """ % (source_se, dest_se)

    cursor.execute(query)
    result['Link_source_to_dest'] =  cursor.fetchall()

    # Check Link config from the source_se -> *
    #
    query = """
        SELECT min_active, max_active
        FROM t_link_config 
        WHERE source_se = '%s' AND dest_se = '*' ;
        """ % source_se

    cursor.execute(query)
    result['Link_source_to_all'] =  cursor.fetchall()

    # Check Link config from the * -> dest_se
    # 
    query = """
        SELECT min_active, max_active
        FROM t_link_config 
        WHERE source_se = '*' AND dest_se = '%s' ;
        """ % dest_se

    cursor.execute(query)
    result['Link_all_to_dest'] =  cursor.fetchall()

    #Check Link config from the * -> *
    #
    query = """
        SELECT min_active, max_active
        FROM t_link_config 
        WHERE source_se = '*' AND dest_se = '*' ;
        """

    cursor.execute(query)
    result['link_all_to_all'] =  cursor.fetchall()

    # Get user DN and format 
    user_dn = os.environ['SSL_CLIENT_S_DN'].split(',');
    user_dn = '/' + '/'.join(reversed(user_dn));
    
    #Check if USER_DN is authorized
    query = """
        SELECT distinct 1 dn
        FROM t_authz_dn
        WHERE dn = '%s'; 
        """ % user_dn

    cursor.execute(query)
    result['user_dn_result']  = cursor.fetchall()[0][0]

    return [result]