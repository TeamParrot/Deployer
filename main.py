import configparser
import subprocess

from bottle import get, post, request, run

import requests

cfg = configparser.ConfigParser()
with open('config.ini') as f:
    cfg.read_file(f)


class Server:
    def __init__(self):
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            ['python3', 'main.py'], cwd=cfg['paths']['backend'])

    def stop(self):
        if self.proc is None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def restart(self):
        self.stop()
        self.start()


server = Server()

def log(msg):
    print(msg)
    requests.post(cfg['discord']['url'], json={'content': msg})


def update_instance():
    server.stop()
    log('Pulling changes from GitHub.')
    subprocess.run(['git', 'pull'], check=True, cwd=cfg['paths']['root'])
    log('Building with npm.')
    subprocess.run(['npm', 'run', 'build'], check=True,
                   cwd=cfg['paths']['frontend'])
    log('Deploying new server instance.')
    server.start()


@get('/')
def root():
    return subprocess.run(['git', 'log', '-n', '1'], check=True, cwd=cfg['paths']['root'], stdout=subprocess.PIPE).stdout.decode()


@post('/')
def handle_webhook():
    if request.json is not None and 'ref' in request.json and request.json['ref'] == 'refs/heads/master':
        if request.json['compare']:
            log('Recieved commit: {}'.format(request.json['compare']))
        else:
            log('Recieved commit')
        update_instance()


update_instance()
run(host=cfg['server']['host'], port=cfg['server']['port'])
