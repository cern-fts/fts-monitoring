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


from .common import BASE_URL, FTS3WEB_CONFIG
import os
import urllib.parse as urlparse

def _urlize(path):
    url = urlparse.urlparse(path)
    if url.scheme:
        return path
    else:
        return path % {'base': BASE_URL}


SITE_NAME        = FTS3WEB_CONFIG.get('site', 'name')
SITE_ALIAS       = FTS3WEB_CONFIG.get('site', 'alias')
SITE_LOGO        = _urlize(FTS3WEB_CONFIG.get('site', 'logo'))
SITE_LOGO_SMALL  = _urlize(FTS3WEB_CONFIG.get('site', 'logo_small'))

LINKINFO         = FTS3WEB_CONFIG.get('linkinfo', 'enabled')
FTS3_REST_ENDPNT = _urlize(FTS3WEB_CONFIG.get('linkinfo', 'fts3_rest_endpoint'))

ADMINS = (
    (FTS3WEB_CONFIG.get('site', 'admin_name'), FTS3WEB_CONFIG.get('site', 'admin_mail'))
)

try:
    SHOW_GFAL2_CONFIG = FTS3WEB_CONFIG.getboolean('site', 'show_gfal2_config')
except:
    SHOW_GFAL2_CONFIG = False

try:
    if FTS3WEB_CONFIG.get('site', 'monit'):
        SITE_MONIT = FTS3WEB_CONFIG.get('site', 'monit')
    else:
        SITE_MONIT = None
except:
    SITE_MONIT = None

if FTS3WEB_CONFIG.get('logs', 'port'):
    LOG_BASE_URL = "%s://%%(host)s:%d/%s" % (FTS3WEB_CONFIG.get('logs', 'scheme'),
                                             FTS3WEB_CONFIG.getint('logs', 'port'),
                                             FTS3WEB_CONFIG.get('logs', 'base'))
else:
    LOG_BASE_URL = "%s://%%(host)s:8449/%s" % (FTS3WEB_CONFIG.get('logs', 'scheme'),
                                               FTS3WEB_CONFIG.get('logs', 'base'))


# Configure host aliases
HOST_ALIASES = dict()
if os.path.exists('/etc/fts3/host_aliases'):
    aliases = open('/etc/fts3/host_aliases')
    for line in aliases:
        line = line.strip()
        if len(line) > 0 and not line.startswith('#'):
            original, alias = line.split()
            HOST_ALIASES[original] = alias

ALLOWED_HOSTS = ['*']

