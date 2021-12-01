#!/usr/bin/env python3
import json
from common import get_url
from optparse import OptionParser

def get_servers():
    servers = get_url('https://fts3-pilot.cern.ch:8449/fts3/ftsmon/stats/servers')
    return json.loads(servers)

if __name__ == '__main__':
    servers = get_servers()
    for (hostname, values) in iter(servers.items()):
        print(hostname)
        print("\tActive:", values.get('active', 0))
        print("\tReceived:", values.get('submissions', 0))
        print("\tExecuted:", values.get('transfers', 0))
