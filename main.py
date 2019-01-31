import configparser
import subprocess

from bottle import get, post, request, run

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


def update_instance():
    server.stop()
    print('PULLING')
    subprocess.run(['git', 'pull'], check=True, cwd=cfg['paths']['root'])
    print('BUILDING')
    subprocess.run(['npm', 'run', 'build'], check=True,
                   cwd=cfg['paths']['frontend'])
    print('RUNNING')
    server.start()


@get('/')
def root():
    return subprocess.run(['git', 'log', '-n', '1'], check=True, cwd=cfg['paths']['root'], stdout=subprocess.PIPE).stdout.decode()


@post('/')
def handle_webhook():
    if request.json is not None and 'ref' in request.json and request.json['ref'] == 'refs/heads/master':
        update_instance()


update_instance()
run(host=cfg['server']['host'], port=cfg['server']['port'])
