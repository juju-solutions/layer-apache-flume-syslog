from charms.reactive import RelationBase
from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state, is_state
from charms.reactive.helpers import any_file_changed

from charmhelpers.core import hookenv

from charms.layer.apache_flume_base import Flume


@when('flume-base.installed')
@when_not('flume-syslog.started', 'flume-sink.ready')
def wait_for_sink():
    sink_joined = is_state('flume-sink.joined')
    sink_ready = is_state('flume-sink.ready')
    if not sink_joined:
        hookenv.status_set('blocked', 'Waiting for connection to Flume Sink')
    elif sink_joined and not sink_ready:
        hookenv.status_set('blocked', 'Waiting for Flume Sink')


@when('flume-base.installed', 'flume-sink.ready')
def configure_flume(sink):
    flume = Flume()
    flume.configure_flume({'agents': sink.agents()})
    if any_file_changed([flume.config_file]):
        # the port is currently hard-coded in the rsyslog-forwarder-ha charm
        # must run as root to listen on low-number UDP port
        hookenv.status_set('maintenance', 'Configuring Flume')
        hookenv.open_port(hookenv.config('source_port'))
        flume.restart(user='root')
        set_state('flume-syslog.started')

    syslog = RelationBase.from_state('syslog.joined')
    if syslog is None:
        hookenv.status_set('active', 'Ready')
    else:
        hookenv.status_set('active', 'Ready (Syslog souces: {})'
                                     .format(syslog.client_count()))


@when('flume-syslog.started')
@when_not('flume-sink.ready')
def stop_flume():
    flume = Flume()
    hookenv.close_port(hookenv.config('source_port'))
    flume.stop()
    remove_state('flume-syslog.started')
