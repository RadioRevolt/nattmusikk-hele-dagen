# This script runs an HTTP server which allows another host to ask us whether
# nightmusic-all-day-round is activated or not, and activate or deactivate it.

from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from time import sleep
import pyotp
import flask
import yaml
import os.path
import gunicorn.app.base

################################################################################
# Define utilities
################################################################################


def parse_config(configfile):
    with open(configfile) as f:
        doc = yaml.load(f)
    keyfile = doc["keyfile"]
    socketfile = doc["socketfile"]
    port = doc["port"]
    allowed_remote_addresses = doc["allowed_remote_addresses"]

    return keyfile, socketfile, port, allowed_remote_addresses


def init_otps(keyfile):
    with open(keyfile, "r") as f:
        lines = f.readlines()
    keys = [line.strip() for line in lines if line.strip()]
    return [pyotp.TOTP(key) for key in keys]


class LiquidSoapBoolean:
    ls_var_name = "nightmusic_activated"
    def __init__(self, socketfilepath):
        self.socketfilepath = socketfilepath
        self.socket = self.create_socket(socketfilepath)

    @staticmethod
    def create_socket(socketfilepath):
        new_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        new_socket.connect(socketfilepath)
        return new_socket

    def send_to_socket(self, data):
        self.socket.sendall(data.encode("UTF-8"))
        return self.socket.recv(4096).decode("UTF-8")

    @property
    def value(self):
        r = self.send_to_socket("var.get %s\n" % self.ls_var_name)
        returned_value = r.strip()
        return True if returned_value == "true" else False

    @value.setter
    def value(self, new_value):
        new_value_str = "true" if new_value else "false"
        r = self.send_to_socket("var.set %s = %s\n" %
                                (self.ls_var_name, new_value_str))

    def close(self):
        self.socket.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


################################################################################
# Initialize globals
################################################################################

# Init the Flask application
app = flask.Flask('request2liquidsoap')
# Where to find the settings
CONFIGFILE = os.path.join(os.path.dirname(__file__), 'settings.yaml')
# Parse settings
KEYFILE, SOCKETFILE, PORT, ALLOWED_REMOTE_ADDRESSES = \
    parse_config(CONFIGFILE)
# Init the one time password objects
OTPS = init_otps(KEYFILE)


################################################################################
# Define and run the Flask server
################################################################################

@app.before_request
def deny_if_not_allowed_remote_address():
    remote_address = flask.request.remote_addr
    if remote_address not in ALLOWED_REMOTE_ADDRESSES:
        flask.abort(401)


@app.route("/<user_key>")
def handle(user_key):
    user_key = int(user_key)
    our_otps = [otp.now() for otp in OTPS[:1]]

    # TODO: Protect against side-chaining attacks
    do_status = (user_key - our_otps[0]) == 0
    do_activate = (user_key - our_otps[0]) == our_otps[1]
    do_deactivate = (user_key - our_otps[0]) == -our_otps[1]

    sleep(1)  # Weak protection against side-chaining and brute-force

    if not (do_status or do_activate or do_deactivate):
        # TODO: Send error
        pass
    else:
        if do_status:
            # TODO: Fetch value
            pass
        elif do_activate:
            # TODO: Set interactive boolean to True
            pass
        elif do_deactivate:
            # TODO: Set interactive boolean to False
            pass
        # TODO: Send response with status==200 and confirmation codes


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, application, options=None):
        self.options = options or dict()
        self.application = application
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    options = {
        'bind': '%s:%s' % ('0.0.0.0', str(PORT)),
        'workers': 1,
    }
    StandaloneApplication(app, options).run()

if __name__ == '__main__':
    main()
