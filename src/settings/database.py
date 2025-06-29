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


from .common import FTS3WEB_CONFIG

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.' + FTS3WEB_CONFIG.get('database', 'engine'),
        'USER':     FTS3WEB_CONFIG.get('database', 'user'),
        'PASSWORD': FTS3WEB_CONFIG.get('database', 'password'),
        'NAME':     FTS3WEB_CONFIG.get('database', 'name'),
        'HOST':     FTS3WEB_CONFIG.get('database', 'host'),
        'PORT':     FTS3WEB_CONFIG.get('database', 'port'),
        'OPTIONS':  {}
    }
}

if DATABASES['default']['ENGINE'] == 'django.db.backends.oracle':
    DATABASES['default']['OPTIONS']['threaded'] = True

if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    import MySQLdb.cursors
    DATABASES['default']['OPTIONS']['init_command'] = "SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"
    if FTS3WEB_CONFIG.has_option('database', 'max_execution_time'):
        DATABASES['default']['OPTIONS']['init_command'] += "; SET SESSION MAX_EXECUTION_TIME =" + \
                                                           FTS3WEB_CONFIG.get('database', 'max_execution_time')
    DATABASES['default']['OPTIONS']['cursorclass'] = MySQLdb.cursors.SSCursor

DISABLE_TRANSACTION_MANAGEMENT = True

if FTS3WEB_CONFIG.getboolean('site', 'overview_page_cache'):
    DATABASES['overview_write_cache'] = {
        'ENGINE':   'django.db.backends.mysql',
        'USER':     FTS3WEB_CONFIG.get('overview_write_cache_database', 'user'),
        'PASSWORD': FTS3WEB_CONFIG.get('overview_write_cache_database', 'password'),
        'NAME':     FTS3WEB_CONFIG.get('overview_write_cache_database', 'name'),
        'HOST':     FTS3WEB_CONFIG.get('overview_write_cache_database', 'host'),
        'PORT':     FTS3WEB_CONFIG.get('overview_write_cache_database', 'port'),
    }
