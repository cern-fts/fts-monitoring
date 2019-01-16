FTS Web Monitoring
==================

The FTS3 Web Monitoring allows peeking at the internal FTS3 state: active transfers, success rate, optimizer decisions...

It is *not* a tool for historical data, data aggregation, etc... For this sort of uses, better use the [FTS Dashboard](https://monit-grafana.cern.ch/dashboard/db/fts-transfers-30-days?orgId=20). 

## Firewalld: How to set up a firewall using firewalld on centos7

Firewalld is installed by default on some Linux distributions, including many images of CentOS 7. However, it may be necessary for you to install firewalld yourself:

    sudo yum install firewalld

After you install firewalld, you can enable the service and reboot your server. Keep in mind that enabling firewalld will cause the service to start up at boot. It is best practice to create your firewall rules and take the opportunity to test them before configuring this behavior in order to avoid potential issues.

    sudo systemctl enable firewalld
    sudo reboot

When the server restarts, your firewall should be brought up, your network interfaces should be put into the zones you configured (or fall back to the configured default zone), and any rules associated with the zone(s) will be applied to the associated interfaces.

We can verify that the service is running and reachable by typing:

    sudo firewall-cmd --state

output
running

This indicates that our firewall is up and running with the default configuration.

When running fts-rest, we can allow this traffic for interfaces in our "public" zone for this session by copying first ftsmon.xml in /usr/lib/firewalld/services and then typing:

    sudo firewall-cmd --zone=public --add-service=ftsmon

You can leave out the --zone= if you wish to modify the default zone. We can verify the operation was successful by using the --list-all or --list-services operations:

    sudo firewall-cmd --zone=public --list-services