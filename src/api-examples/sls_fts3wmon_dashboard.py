#!/usr/bin/env python3
# Copyright notice:
# Copyright (C) CERN 2015, 2020
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
import requests
import optparse
import time
import xml.etree.ElementTree as ET
import re


class Fts3SlsPlus:
    """
    Enriched Service Level Status
    """

    VOS = ["atlas", "cms", "lhcb"]

    def _get_json(self, url):
        """
        Do an HTTP GET
        """
        # We have to pass an authorization key created especially for FTS otherwise grafana will not authorise the query.
        response = requests.get(
            url, headers={"Authorization": "Bearer " + str(self.token)}
        )
        return response.json()

    def _get_xml(self, url):
        """
        Do an HTTP GET
        """
        response = requests.get(
            url, headers={"Authorization": "Bearer " + str(self.token)}
        )
        return response.text

    def __init__(self, fts3_name, sls_url, dashb_base, interval, token):
        """
        Constructor
        :param fts3_name:  The FTS3 name as sent to the dashboard
        :param sls_url:    The SLS url used as base
        :param dashb_base: Dashboard base url
        """
        self.fts3_name = fts3_name
        self.sls_url = sls_url
        self.dashb_base = dashb_base
        self.interval = interval
        self.token = token

    def generate_sls(self):
        """
        Generate the enriched SLS
        """
        xml_string = self._get_xml(self.sls_url)
        root = ET.fromstring(xml_string)

        availabilityinfo = re.search(
            "<availabilityinfo>(.*)</availabilityinfo>", xml_string
        )
        availabilityinfo = availabilityinfo.group(1)

        availability = {
            "producer": "fts",
            "type": "availability",
            "serviceid": root[0].text,
            "service_status": root[2].text,
            "availabilityinfo": availabilityinfo,
            "timestamp": int(time.time()),
        }
        metrics = {"producer": "fts", "type": "metric", "timestamp": int(time.time())}
        data = root[3]
        for numericvalue in data:
            metrics[numericvalue.attrib["name"]] = numericvalue.text
            try:
                metrics[numericvalue.attrib["name"]] = int(numericvalue.text)
            except ValueError:
                pass

        for vo in self.VOS:
            if vo == "atlas":
                fts3_name = "fts3-atlas.cern.ch"
            elif vo == "lhcb":
                fts3_name = "fts3-lhcb.cern.ch"
            else:
                fts3_name = self.fts3_name
            try:
                monit_bytes = self._get_json(
                    self.dashb_base
                    + "/api/datasources/proxy/7794/query?db=monit_production_transfer&q=SELECT%20sum(%22transferred_volume%22)%20%20FROM%20%22one_month%22.%22transfer_fts%22%20WHERE%20(%22vo%22%20%3D%20%27"
                    + vo
                    + "%27%20AND%20%22endpnt%22%20%3D%20%27"
                    + fts3_name
                    + "%27%20AND%20%22technology%22%20%3D%20%27fts%27%20)%20AND%20time%20%3E%3D%20now()%20-%20"
                    + str(self.interval)
                    + "h&epoch=m"
                )

                transferred = monit_bytes["results"][0]["series"][0]["values"][0][1]
                throughput = transferred / (self.interval * 3600)
            except Exception:
                throughput = 0

            try:
                monit_success = self._get_json(
                    self.dashb_base
                    + "/api/datasources/proxy/7794/query?db=monit_production_transfer&q=SELECT%20sum(%22count%22)%20%20FROM%20%22one_month%22.%22transfer_fts%22%20WHERE%20(%22vo%22%20%3D%20%27"
                    + vo
                    + "%27%20AND%20%22endpnt%22%20%3D%20%27"
                    + fts3_name
                    + "%27%20AND%20%22technology%22%20%3D%20%27fts%27%20AND%20%22t_final_transfer_state%22%20%3D%20%27Ok%27%20)%20AND%20time%20%3E%3D%20now()%20-%20"
                    + str(self.interval)
                    + "h&epoch=ms"
                )
                n_transfers = monit_success["results"][0]["series"][0]["values"][0][1]
            except Exception:
                n_transfers = 0

            try:
                monit_errors = self._get_json(
                    self.dashb_base
                    + "/api/datasources/proxy/7794/query?db=monit_production_transfer&q=SELECT%20sum(%22count%22)%20%20FROM%20%22one_month%22.%22transfer_fts%22%20WHERE%20(%22vo%22%20%3D%20%27"
                    + vo
                    + "%27%20AND%20%22endpnt%22%20%3D%20%27"
                    + fts3_name
                    + "%27%20AND%20%22technology%22%20%3D%20%27fts%27%20AND%20%22t_final_transfer_state%22%20%3D%20%27Error%27%20)%20AND%20time%20%3E%3D%20now()%20-%20"
                    + str(self.interval)
                    + "h&epoch=ms"
                )
                n_errors = monit_errors["results"][0]["series"][0]["values"][0][1]
            except Exception:
                n_errors = 0

            metrics[vo + "_finished"] = n_transfers
            metrics[vo + "_errors"] = n_errors
            metrics[vo + "_throughput"] = throughput

        return [availability, metrics]


def send(document):
    return requests.post(
        "http://monit-metrics:10012/",
        data=json.dumps(document),
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )


def send_and_check(document, should_fail=False):
    response = send(document)
    assert (
        response.status_code in [200]
    ) != should_fail, "With document: {0}. Status code: {1}. Message: {2}".format(
        document, response.status_code, response.text
    )


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("--fts", help="FTS3 endpoint name", default="fts3-devel.cern.ch")
    parser.add_option(
        "--sls",
        help="FTS3 SLS content",
        default="https://fts3-devel.cern.ch:8449/fts3/ftsmon/stats/servers?format=sls",
    )
    parser.add_option(
        "--dashboard", help="FTS3 dashboard", default="https://monit-grafana.cern.ch"
    )
    parser.add_option("--interval", help="Interval in hours", type=int, default=1)

    parser.add_option("--token", help="Bearer authorisation for monit-grafana")

    options, args = parser.parse_args()

    sls = Fts3SlsPlus(
        options.fts, options.sls, options.dashboard, options.interval, options.token
    )
    messages = sls.generate_sls()
    for m in messages:
        print(json.dumps(m))
        send_and_check(m)
