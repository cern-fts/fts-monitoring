# Copyright notice:
#
# Copyright (C) CERN 2023
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

# A sample logging configuration
LOGGING = {
    'version': 1,
    # Uncomment this to enable logging
    'disable_existing_loggers': False,
    'formatters': {
        'generic': {
            'format': FTS3WEB_CONFIG.get('formatter_generic', 'format'),
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': FTS3WEB_CONFIG.get('handler_log_file', 'filename'),
            'formatter': FTS3WEB_CONFIG.get('handler_log_file', 'formatter'),
        }
    },
    'loggers': {
        'django.db': {
            'handlers': ['file'],
            'level': FTS3WEB_CONFIG.get('logger_db', 'level')
        },
        'django.request': {
            'handlers': ['file'],
            'level': FTS3WEB_CONFIG.get('logger_request', 'level')
        },
        'ftsmon': {
            'handlers': ['file'],
            'level': FTS3WEB_CONFIG.get('logger_ftsmon', 'level')
        }
    }
}
