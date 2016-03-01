from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state, is_state
from charms.reactive.helpers import any_file_changed

from charmhelpers.core import hookenv

from charms.layer.apache_flume_base import Flume


@when('flume-base.installed')
@when_not('flume-syslog.started')
def report_status():
    syslog_joined = is_state('syslog.joined')
    sink_joined = is_state('flume-sink.joined')
    sink_ready = is_state('flume-sink.ready')
    if not syslog_joined and not sink_joined:
        hookenv.status_set('blocked', 'Waiting for connection to Flume Sink and Syslog Forwarder')
    elif not syslog_joined:
        hookenv.status_set('blocked', 'Waiting for connection to Syslog Forwarder')
    elif not sink_joined:
        hookenv.status_set('blocked', 'Waiting for connection to Flume Sink')
    elif sink_joined and not sink_ready:
        hookenv.status_set('blocked', 'Waiting for Flume Sink')


@when('flume-base.installed', 'flume-sink.ready', 'syslog.joined')
def configure_flume(sink, syslog):  # pylint: disable=unused-argument
    hookenv.status_set('maintenance', 'Configuring Flume')
    flume = Flume()
    flume.configure_flume({'agents': sink.agents()})
    if any_file_changed([flume.config_file]):
        # must run as root to listen on low-number UDP port
        # the port is currently hard-coded in the rsyslog-forwarder-ha charm
        flume.restart(user='root')
    hookenv.status_set('active', 'Ready')
    set_state('flume-syslog.started')


@when('flume-syslog.started')
@when_not('flume-sink.ready')
def stop_flume():
    flume = Flume()
    flume.stop()
    remove_state('flume-syslog.started')


@when('flume-syslog.started')
@when_not('syslog.joined')
def lost_syslog():
    stop_flume()
