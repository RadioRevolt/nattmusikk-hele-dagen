import jinja2
import argparse
import os.path


parser = argparse.ArgumentParser(
    description="Generate settings.yaml"
)

parser.add_argument(
    "application",
    nargs="?",
    choices=["both", "server", "slackbot"],
    default="both",
    help="The kind of settings file you want to create."
)

parsed = parser.parse_args()
choice = parsed.application
server_configfile = os.path.join(os.path.dirname(__file__), "settings.yaml")
slackbot_configfile = os.path.join(os.path.dirname(__file__), "settings_slackbot.yaml")

choices = dict()

# Recognize what the user wants
if choice == "both":
    print("This script will help you get two settings files; one for the "
          "server on which LiquidSoap runs, and one for the host where "
          "Slackbot resides.")
elif choice == "server":
    print("This script will help you get the setting file for the server on "
          "which LiquidSoap runs.")
else:
    print("This script will help you get the setting file for the server on "
          "which Slackbot resides.")

# HOST
if choice in ("both", "slackbot"):
    choices['host'] = input("Which host will the server run on? ")

# PORT
if choice == "both":
    choices['port'] = int(input("At which port? [8000] ") or 8000)
elif choice == "server":
    choices['port'] = int(input("Which port should the server run on? [8000] ") or 8000)
else:
    if os.path.isfile(server_configfile):
        # We can use the server's configuration
        import yaml
        with open(server_configfile, "r") as f:
            doc = yaml.load(f)
        choices['port'] = doc["port"]
    else:
        choices['port'] = int(input("Which port is/will the server running/run on? [8000] ") or 8000)

# KEYFILE
if choice in ("both", "server"):
    keyfile_server = input("Path on the server to the file with the 4 keys: [keys.txt] ") or "keys.txt"

if choice in ("both", "slackbot"):
    keyfile_slackbot = input("Path on the Slackbot host to the file with the 4 keys: [keys.txt] ") or "keys.txt"

# Server specific
if choice in ("both", "server"):
    # SOCKETFILE
    choices['socketfile'] = input("Path to the socket you've configured LiquidSoap to open: ")

    # LIQUIDSOAP_VAR_NAME
    choices['liquidsoap_var_name'] = input("Name of the interactive.bool variable in LiquidSoap: ")

    # ALLOWED_REMOTE_ADDRESSES
    print("Which computers shall be able to connect to the server?")
    print("Write an IP address (4 or 6) on each line.")
    print("Remember to include the IPv6 address when applicable.")
    print("Give an empty line when you're done.")
    choices['allowed_remote_addresses'] = list()
    while True:
        this_input = input("> ")
        if not this_input:
            break
        choices['allowed_remote_addresses'].append(this_input)

print("Generating the file(s)...")

# Generate the files!
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
if choice in ("both", "server"):
    template = env.get_template("settings_server.yaml")
    with open(server_configfile, "w") as f:
        choices['keyfile'] = keyfile_server
        f.write(template.render(**choices))

if choice in ("both", "slackbot"):
    template = env.get_template("settings_slackbot.yaml")
    with open(slackbot_configfile, "w") as f:
        choices['keyfile'] = keyfile_slackbot
        f.write(template.render(**choices))

if choice == "both":
    print("Both config files have been written.")
else:
    print("The config file has been written.")
