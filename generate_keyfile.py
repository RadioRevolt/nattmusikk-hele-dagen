import pyotp
import argparse

parser = argparse.ArgumentParser(
    description="Generate keyfile.txt"
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

keyfile.writelines([pyotp.random_base32() + "\n" for _ in range(4)])
keyfile.close()
