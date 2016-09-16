# This script runs an HTTP server which allows another host to ask us whether
# nightmusic-all-day-round is activated or not, and activate or deactivate it.

import socket
from time import sleep
import pyotp
import flask
import yaml
import os.path
import gunicorn.app.base
import hmac
import random
import requests

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
    slack_options = doc["slack"]

    return keyfile, socketfile, port, allowed_remote_addresses, ls_var_name, \
        slack_options


def parse_keyfile(keyfile):
    with open(keyfile, "r") as f:
        lines = f.readlines()
    keys = [line.strip() for line in lines if line.strip()]
    return [pyotp.TOTP(key) for key in keys[:3]], keys[3]


def send_to_slack(message):
    options = SLACK_OPTIONS
    options['text'] = message
    r = requests.get("https://slack.com/api/chat.postMessage", params=options,
                     timeout=10.0)
    r.raise_for_status()
    r.close()


class LiquidSoapBoolean:
    def __init__(self, socketfilepath, ls_var_name):
        self.socketfilepath = socketfilepath
        self.ls_var_name = ls_var_name
        self.__value = None
        self.socket = None

    @staticmethod
    def _create_socket(socketfilepath):
        new_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        new_socket.connect(socketfilepath)
        return new_socket

    def _send_to_socket(self, data):
        if not self.socket:
            raise RuntimeError("Cannot interact with LiquidSoap before socket "
                               "is opened.")
        self.socket.sendall(data.encode("UTF-8"))
        r = self.socket.recv(4096).decode("UTF-8")
        lines = r.split("\n")
        if lines[0].endswith("is not defined."):
            raise RuntimeError("Variable %s is not defined in LiquidSoap" %
                               self.ls_var_name)
        return lines

    @property
    def value(self):
        if self.__value is None:
            self.force_update()
        return self.__value

    def _fetch_value(self):
        r = self._send_to_socket("var.get %s\n" % self.ls_var_name)
        returned_value = r[0].strip()
        return True if returned_value == "true" else False

    def force_update(self):
        self.__value = self._fetch_value()

    @value.setter
    def value(self, new_value):
        if new_value != self.value:
            # This is a change
            new_value_str = "true" if new_value else "false"
            _ = self._send_to_socket("var.set %s = %s\n" %
                                     (self.ls_var_name, new_value_str))
            self.__value = new_value

    def open(self):
        self.socket = self._create_socket(self.socketfilepath)

    def close(self):
        self.socket.shutdown(socket.SHUT_RDWR)
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
KEYFILE, SOCKETFILE, PORT, ALLOWED_REMOTE_ADDRESSES, LS_VAR_NAME, \
    SLACK_OPTIONS = parse_config(CONFIGFILE)
# Init the one time password objects
OTPS, PASSWORD = parse_keyfile(KEYFILE)

interactive_bool = LiquidSoapBoolean(SOCKETFILE, LS_VAR_NAME)


################################################################################
# Define and run the Flask server
################################################################################

@app.before_request
def deny_if_not_allowed_remote_address():
    remote_address = flask.request.remote_addr
    if remote_address not in ALLOWED_REMOTE_ADDRESSES:
        flask.abort(401)


@app.route("/", methods=['POST'])
def handle():
    form = flask.request.form
    password = form.get('password', 'notarealpassword')
    try:
        onetime_password = int(form.get('onetime_password', '000000'))
    except ValueError:
        return "One-time password is expected to be integer.", 400
    action = form.get('action', 'status').lower()

    correct_password = hmac.compare_digest(password, PASSWORD)
    correct_one_time_password = OTPS[0].verify(onetime_password)
    is_authenticated = correct_password and correct_one_time_password

    # Weak protection against side-chaining and brute-force
    sleep(random.SystemRandom().randint(500, 1500) / 1000)

    with interactive_bool:
        if action == "on" and is_authenticated:
            interactive_bool.value = True
            send_to_slack("Nattmusikk-hele-døgnet er skrudd *PÅ*. \nDere vil *_ikke_*"
                          " lenger få advarsel når det er stille på lufta "
                          "(annet enn når nattmusikken er stille).\n"
                          "Skriv `.nattmusikk av` når det er vanlig drift igjen.")
        if action == "off" and is_authenticated:
            interactive_bool.value = False
            send_to_slack("Nattmusikk-hele-døgnet er skrudd *AV*.\n"
                          "Normal drift gjenopptatt.")
        if action == "status" and is_authenticated:
            pass
        current_value = interactive_bool.value

    our_one_time_password = OTPS[1].now()
    our_fake_one_time_password = OTPS[2].now()
    returned_one_time_password = our_one_time_password if is_authenticated \
        else our_fake_one_time_password
    returned_status = current_value if is_authenticated else False

    data = {
        "onetime_password": returned_one_time_password,
        "status": returned_status,
    }

    return flask.jsonify(data)


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
