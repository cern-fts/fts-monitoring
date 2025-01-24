FTS3 Web Monitoring
===================

The FTS3 Web Monitoring allows seeing the FTS3 state: active transfers, success rate, optimizer decisions...

**Note**: It is not a tool for historical data, data aggregation and various visualisations. 
For FTS3 instances within the WLCG, we recommend using the [FTS3 Dashboards (CERN Central Monitoring)][1] 

### Setting up firewalld

The `firewalld` service is available by default on many Linux distributions, including Alma9. 

To have FTS3 Web Monitoring work with `firewalld`, you will need to allow port 8449 (default).
```bash
firewall-cmd --permanent --zone=public --add-port=8449/tcp
```

### SELinux

Some distributions come with SELinux as well. For FTS3 Web Monitoring to work
with SELinux, we provide the `fts-montioring-selinux` package:
```bash
dnf install fts-monitoring-selinux
```

[1]: https://monit-grafana.cern.ch/d/veRQSWBGz/fts-servers-dashboard
