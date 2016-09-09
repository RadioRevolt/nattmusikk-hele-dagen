# This script runs an HTTP server which allows another host to ask us whether
# nightmusic-all-day-round is activated or not, and activate or deactivate it.

from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from time import sleep
import pyotp
import flask
import yaml
import os.path


app = flask.Flask(__name__)


def parse_config():
    with open(os.path.join(os.path.dirname(__file__), 'settings.yaml')) as f:
        doc = yaml.load(f)
    keyfile = doc["keyfile"]
    socketfile = doc["socketfile"]
    port = doc["port"]
    allowed_hosts = doc["allowed_hosts"]

    return keyfile, socketfile, port, allowed_hosts


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


class HTTPRequestHandler(BaseHTTPRequestHandler):
    allowed_hosts = ["IP-ADDRESSES HERE"]

    def do_GET(self):
        # TODO: Check that it is an allowed host
        user_key = int(self.path[1:])
        our_otps = [otp.now() for otp in self.server.otps[:1]]

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


class CustomHTTPServer(HTTPServer):
    # TODO: Set self.otps and self.allowed_hosts
    pass


def main():
    # TODO: Parse command line arguments
    # TODO: Set up server
    # TODO: Start serving!
    pass





