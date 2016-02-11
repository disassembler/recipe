from fabric.api import *
from fabric.context_managers import settings
from contextlib import contextmanager as _contextmanager
from fabric.decorators import roles
from fabric.api import run, cd, env, roles
from pprint import pprint
from time import sleep
import time
import yaml
import fabric
from fabric.contrib.files import *

env.use_ssh_config = True

env.roledefs = {
    'hello': [
        'app.docker.local'
     ]
}

env.activate = 'source /opt/recipe/python/bin/activate'
config_dir = 'config'

@_contextmanager
def virtualenv():
    with prefix(env.activate):
        yield

def loadenv(environment = ''):
    with open(config_dir + '/' + environment + '.yaml', 'r') as f:
        env.config = yaml.load(f)
        env.roledefs = env.config['roledefs']

@roles('hello')
def hello():
  run("echo hello world from `hostname`")


@roles('app')
def setup(wipe=False):
    """Sets up recipe application"""
    wipe = bool(wipe)
    if wipe or not exists('/opt/recipe'):
        sudo('rm -rf /opt/recipe')
    sudo('mkdir -p /opt/recipe')
    sudo('chown ' + env.user + ':' + env.user + ' /opt/recipe')
    if not exists('/opt/recipe/python'):
        run('virtualenv /opt/recipe/python')
    sudo('chown ' + env.user + ':' + env.user + ' /opt/recipe')
    with virtualenv():
        run('pip install -I gunicorn supervisor')
    sudo('mkdir -p /etc/supervisor.d')
    put(config_dir + '/files/supervisord-init', '/etc/init.d/supervisord', use_sudo=True, mode=0755)
    put(config_dir + '/files/supervisord.conf', '/etc/supervisord.conf', use_sudo=True)


@roles('app')
def deploy(version='master'):
    """Deploys recipe code to application server"""
    if not exists('/opt/recipe'):
        setup()
    local('rm -rf recipe')
    local('/usr/bin/git clone git@github.com:disassembler/recipe.git')
    env.release = time.strftime('%Y%m%d%H%M%S')
    with lcd('recipe'):
        local('git checkout ' + version)
        local('git archive --format=tar ' + version + ' | gzip > /tmp/recipe-' + env.release + '.tar.gz')
    put('/tmp/recipe-' + env.release + '.tar.gz', '/tmp/')
    run('mkdir -p /opt/recipe/builds/' + env.release)
    with cd('/opt/recipe/builds/' + env.release):
        run('tar -zxf /tmp/recipe-' + env.release + '.tar.gz')
    run('rm -f /opt/recipe/current')
    run('ln -sf /opt/recipe/builds/' + env.release + ' /opt/recipe/current')
    with cd('/opt/recipe/current'):
        with virtualenv():
            run('pip install -I -r requirements.txt')
    put(config_dir + '/files/' + env.config['environment'] + '/supervisor-recipe.conf', '/etc/supervisor.d/recipe.conf', use_sudo=True)
    #sudo('/opt/recipe/python/bin/supervisorctl reread')
    #sudo('/opt/recipe/python/bin/supervisorctl restart recipe')
    #sudo('/opt/recipe/python/bin/supervisorctl restart celery')
    #sudo('/opt/recipe/python/bin/supervisorctl restart celerybeat')
    #sudo('/opt/recipe/python/bin/supervisorctl status recipe')
    #sudo('/opt/recipe/python/bin/supervisorctl status celery')
    #sudo('/opt/recipe/python/bin/supervisorctl status celerybeat')
    cleanupBuilds()

@roles('app')
def cleanupBuilds():
    sudo('/bin/rm -rf `/bin/ls -t | /usr/bin/tail -n +5`')
    sudo('/bin/rm -f /tmp/recipe-*.tar.gz')
    local('/bin/rm -f /tmp/recipe-*.tar.gz')
