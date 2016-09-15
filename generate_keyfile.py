import pyotp
import argparse
import base64
import os

parser = argparse.ArgumentParser(
    description="Generate keyfile.txt, which contains two One Time "
                "Password-keys (one for each direction of communication), and "
                "one shared 'password' for authenticating the slack2request "
                "program."
)

parser.add_argument(
    "keyfile",
    type=argparse.FileType("w", encoding="UTF-8"),
    nargs="?",
    default="keyfile.txt",
    help="Where to save the keyfile. Use - for standard output. "
         "Defaults to keyfile.txt",
)

args = parser.parse_args()
keyfile = args.keyfile

keyfile.writelines(
    [pyotp.random_base32(), pyotp.random_base32(),
     base64.b64encode(os.urandom(64))])
keyfile.close()
