import jujuresources
from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state
from charmhelpers.core import hookenv
from charms.flume import Flume
from jujubigdata.utils import DistConfig

def dist_config():

    if not getattr(dist_config, 'value', None):
        flume_reqs = ['packages', 'groups', 'users', 'dirs']
        dist_config.value = DistConfig(filename='dist.yaml', required_keys=flume_reqs)
    return dist_config.value


@when_not('flumesyslog.installed')
def install_flume(*args):

    flume = Flume(dist_config())
    if flume.verify_resources():
        hookenv.status_set('maintenance', 'Installing Flume syslog agent')
        flume.install()
        set_state('flumesyslog.installed')


@when('flumesyslog.installed')
@when_not('flume-agent.connected')
def waiting_for_flume_connection():
    hookenv.status_set('blocked', 'Waiting for connection to Flume HDFS')


@when('flumesyslog.installed', 'flume-agent.connected')
@when_not('flume-agent.available')
def waiting_for_flume_available(flume):
    hookenv.status_set('waiting', 'Waiting for availability of Flume HDFS')


@when('flumesyslog.installed', 'flume-agent.available')
@when_not('flumesyslog.started')
def configure_flume(flumehdfs):
    try:
        port = flumehdfs.get_flume_port()
        ip = flumehdfs.get_flume_ip()
        protocol = flumehdfs.get_flume_protocol()
        flumehdfsinfo = {'port': port, 'private-address': ip, 'protocol': protocol}
        hookenv.log("Connecting to Flume HDFS")
        hookenv.status_set('maintenance', 'Setting up Flume')
        flume = Flume(dist_config())
        flume.configure_flume(flumehdfsinfo)
        flume.restart()
        hookenv.status_set('active', 'Ready')
        set_state('flumesyslog.started')
    except:
        hookenv.log("Relation with Flume sink not established correctly")        


@when('flumesyslog.started')
@when_not('flume-agent.available')
def agent_disconnected():
    remove_state('flumesyslog.started')
    hookenv.status_set('blocked', 'Waiting for a connection from a Flume agent')

    
@when('syslog.related')
@when_not('syslog.available')
def syslog_forward_related(syslog):
    hookenv.status_set('waiting', 'Waiting for the connection to syslog producer.')
    syslog.send_port(hookenv.config()['source_port'])


@when('syslog.available', 'flumesyslog.started')
def syslog_forward_connected(syslog):
    hookenv.status_set('active', 'Ready')

