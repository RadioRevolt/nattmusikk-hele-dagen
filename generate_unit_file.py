import argparse
import os.path
import jinja2

parser = argparse.ArgumentParser(
    description="Generate unit file for either Upstart or SystemD"
)

parser.add_argument(
    "choice",
    choices=["upstart", "systemd"],
    help="Which system to generate a file for. Upstart is generally recent "
         "Ubuntus before 16.04, SystemD is for 16.04 or newer."
)

parser.add_argument(
    "output",
    nargs="?",
    type=argparse.FileType("w", encoding="UTF-8"),
    help="Where to output the file. Use - for stdout (default).",
    default="-"
)

args = parser.parse_args()
system = args.choice
output = args.output
try:
    path = os.path.dirname(os.path.realpath(__file__))

    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    template = env.get_template(
        "nattmusikk-hele-dagen." +
        ("conf" if system == "upstart" else "service")
    )
    output.write(template.render(path=path))
finally:
    output.close()
