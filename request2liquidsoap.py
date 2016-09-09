# This script runs an HTTP server which allows another host to ask us whether
# nightmusic-all-day-round is activated or not, and activate or deactivate it.

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
    ls_var_name = doc["liquidsoap_var_name"]

    return keyfile, socketfile, port, allowed_remote_addresses, ls_var_name


def init_otps(keyfile):
    with open(keyfile, "r") as f:
        lines = f.readlines()
    keys = [line.strip() for line in lines if line.strip()]
    return [pyotp.TOTP(key) for key in keys]


class LiquidSoapBoolean:
    def __init__(self, socketfilepath, ls_var_name):
        self.socketfilepath = socketfilepath
        self.ls_var_name = ls_var_name
        self.__value = None
        self.socket = None

    @staticmethod
    def _create_socket(socketfilepath):
        new_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        new_socket.connect(socketfilepath)
        return new_socket

    def _send_to_socket(self, data):
        if not self.socket:
            raise RuntimeError("Cannot interact with LiquidSoap before socket "
                               "is opened.")
        self.socket.sendall(data.encode("UTF-8"))
        return self.socket.recv(4096).decode("UTF-8")

    @property
    def value(self):
        if self.__value is None:
            self.force_update()
        return self.__value

    def _fetch_value(self):
        r = self._send_to_socket("var.get %s\n" % self.ls_var_name)
        returned_value = r.strip()
        return True if returned_value == "true" else False

    def force_update(self):
        self.__value = self._fetch_value()

    @value.setter
    def value(self, new_value):
        if new_value != self.value:
            # This is a change
            new_value_str = "true" if new_value else "false"
            r = self._send_to_socket("var.set %s = %s\n" %
                                     (self.ls_var_name, new_value_str))
            self.__value = new_value

    def open(self):
        self.socket = self._create_socket(self.socketfilepath)

    def close(self):
        self.socket.close()
        self.socket = None

    def __enter__(self):
        self.open()

    def __exit__(self, *_):
        self.close()


################################################################################
# Initialize globals
################################################################################

# Init the Flask application
app = flask.Flask('request2liquidsoap')
# Where to find the settings
CONFIGFILE = os.path.join(os.path.dirname(__file__), 'settings.yaml')
# Parse settings
KEYFILE, SOCKETFILE, PORT, ALLOWED_REMOTE_ADDRESSES, LS_VAR_NAME = \
    parse_config(CONFIGFILE)
# Init the one time password objects
OTPS = init_otps(KEYFILE)

interactive_bool = LiquidSoapBoolean(SOCKETFILE, LS_VAR_NAME)


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
        flask.abort(401)
        pass
    else:
        if do_status:
            # We'll return the current value anyway
            pass
        elif do_activate:
            interactive_bool.value = True
        elif do_deactivate:
            interactive_bool.value = False
        return str(OTPS[2].now() + (OTPS[3].now() * (1 if interactive_bool.value else -1)))


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
    with interactive_bool:
        main()
