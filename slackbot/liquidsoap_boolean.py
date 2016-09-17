"""
MIT License

Copyright (c) 2016 Radio Revolt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Class for interacting with a interactive.bool in LiquidSoap

import socket


class LiquidSoapBoolean:
    def __init__(self, socketfilepath, ls_var_name):
        """
        Class for interacting with a, well, interactive.bool in LiquidSoap.

        Args:
            socketfilepath (str): Path to the socketfile opened by LiquidSoap.
            ls_var_name (str): Variable name given as the first argument to
                the interactive.bool in LiquidSoap.

        Usage:

        >>> my_bool = LiquidSoapBoolean("/tmp/liquidsoap_socket", "variable_name")
        >>> # ...
        >>> with my_bool:
        >>>     print(my_bool.value)
        True
        >>>     my_bool.value = not my_bool.value
        >>>     print(my_bool.value)
        False

        As seen here, you must ensure the socket is opened before manipulating
        or accessing the interactive.bool. You can do this by using this class
        as context manager (as seen in the example), or by calling open() and
        close() yourself.
        """
        self.socketfilepath = socketfilepath
        self.ls_var_name = ls_var_name
        self.__value = None
        self.socket = None

    @staticmethod
    def _create_socket(socketfilepath):
        """
        Return a socket.socket object, connected to the given Unix socket.

        Args:
            socketfilepath (str): Path to the Unix socket file which the socket
                shall be connected to.

        Returns:
            socket.socket: Socket connected to socketfilepath.
        """
        new_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        new_socket.connect(socketfilepath)
        return new_socket

    def _send_to_socket(self, data):
        """
        Send data to socket, and return whatever LiquidSoap returned.

        Args:
            data (str): Single string which shall be sent to the LiquidSoap
                socket. You must ensure it ends in a newline yourself.

        Returns:
            list: List of strings, representing the lines returned by
                LiquidSoap (with newlines stripped).

        Raises:
            RuntimeError: If called when the socket isn't opened, or if
                LiquidSoap says that a variable isn't defined (thus we assume
                you are using var.get or var.set).
        """
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
        """
        The value of the interactive.bool in LiquidSoap. You can assign a new
        value to this to change the value of the interactive.bool.

        Note that you must have opened the socket in order to use this.

        The value is cached, so it will not represent the actual state in
        LiquidSoap if other sources manipulate the interactive.bool variable.
        Run force_update() so fetch the value from LiquidSoap.
        """
        if self.__value is None:
            self.force_update()
        return self.__value

    def _fetch_value(self):
        """
        Returns the current value of the interactive.bool from LiquidSoap.
        """
        r = self._send_to_socket("var.get %s\n" % self.ls_var_name)
        returned_value = r[0].strip()
        return True if returned_value == "true" else False

    def force_update(self):
        """
        Ensure value has the current value of the interactive.bool in
        LiquidSoap.
        """
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
        """Open the socket, allowing communication with LiquidSoap."""
        self.socket = self._create_socket(self.socketfilepath)

    def close(self):
        """Close the socket."""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.socket = None

    def __enter__(self):
        self.open()

    def __exit__(self, *_):
        self.close()
