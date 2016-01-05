## Overview

Flume is a distributed, reliable, and available service for efficiently
collecting, aggregating, and moving large amounts of log data. It has a simple
and flexible architecture based on streaming data flows. It is robust and fault
tolerant with tunable reliability mechanisms and many failover and recovery
mechanisms. It uses a simple extensible data model that allows for online
analytic application. Learn more at [flume.apache.org](http://flume.apache.org).

This charm provides a Flume agent designed to receive remote syslog events and
send them to the `apache-flume-hdfs` agent for storage into the shared
filesystem (HDFS) of a connected Hadoop cluster. Think of this charm as a
replacement for `rsyslog`, sending syslog events to HDFS instead of writing
them to a local filesystem.


## Deployment

This charm is uses the Hadoob base layer and the HDFS interface to pull its dependencies
and act as a client to a Hadoop namenode:

You may manually deploy the recommended environment as follows:

    juju deploy apache-hadoop-datanode datanode
    juju deploy apache-hadoop-namenode namenode
    juju deploy apache-hadoop-nodemanager nodemgr
    juju deploy apache-hadoop-resourcemanager resourcemgr

    juju add-relation namenode datanode
    juju add-relation resourcemgr nodemgr
    juju add-relation resourcemgr namenode

Deploy Flume hdfs:

    juju deploy apache-flume-hdfs flume-hdfs
    juju add-relation flume-hdfs namenode

Now that the base environment has been deployed (either via quickstart or
manually), you are ready to add the `apache-flume-syslog` charm and
relate it to the `flume-hdfs` agent:

    juju deploy apache-flume-syslog flume-syslog
    juju add-relation flume-syslog flume-hdfs

You are now ready to ingest remote syslog events! Note the deployment at this
stage isn't very useful. You'll need to relate this charm to any other service
that is configured to send data via the `syslog` interface.


## Usage

As an example use case, let's ingest our `hdfs-master` syslog events into HDFS.
Deploy the `rsyslog-forwarder-ha` subordinate charm, relate it to
`hdfs-master`, and then link the `syslog` interfaces:

    juju deploy rsyslog-forwarder-ha
    juju add-relation rsyslog-forwarder-ha datanode
    juju add-relation rsyslog-forwarder-ha flume-syslog

Any syslog data generated on the `datanode` unit will now be ingested into
HDFS via the `flume-syslog` and `flume-hdfs` charms. Flume may include multiple
syslog events in each file written to HDFS. This is configurable with various
options on the `flume-hdfs` charm. See descriptions of the `roll_*` options on
the [apache-flume-hdfs](https://jujucharms.com/apache-flume-hdfs/) charm store
page for more details.

Flume will write files to HDFS in the following location:
`/user/flume/<event_dir>/<yyyy-mm-dd>/FlumeData.<id>`. The `<event_dir>`
subdirectory is configurable and set to `flume-syslog` by default for this
charm.


## Test the deployment

To verify this charm is working as intended, trigger a syslog event on the
monitored unit (`hdfs-master` in our deployment scenario):

    juju ssh datanode/0 'echo flume-test'

Now SSH to the `flume-hdfs` unit, locate an event, and cat it:

    juju ssh flume-hdfs/0
    hdfs dfs -ls /user/flume/<event_dir>               # <-- find a date
    hdfs dfs -ls /user/flume/<event_dir>/<yyyy-mm-dd>  # <-- find an event
    hdfs dfs -cat /user/flume/<event_dir>/<yyyy-mm-dd>/FlumeData.<id>

You should be able to find a timestamped message about SSH'ing into the
`datanode` unit that corresponds to the trigger you issued above. Note that
this workload isn't limited to ssh-related events. You'll get every syslog
event from the `datanode` unit. Happy logging!


## Contact Information

- <bigdata@lists.ubuntu.com>


## Help

- [Apache Flume home page](http://flume.apache.org/)
- [Apache Flume bug tracker](https://issues.apache.org/jira/browse/flume)
- [Apache Flume mailing lists](https://flume.apache.org/mailinglists.html)
- `#juju` on `irc.freenode.net`
