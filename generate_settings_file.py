import jinja2
import argparse
import os.path


parser = argparse.ArgumentParser(
    description="Generate settings.yaml or settings_slackbot.yaml"
)

parser.add_argument(
    "application",
    nargs="?",
    choices=["settings.yaml", "settings_slackbot.yaml"],
    default="settings.yaml",
    help="The kind of settings file you want to create."
)

parsed = parser.parse_args()
choice = parsed.application
nattmusikk_configfile = os.path.join(os.path.dirname(__file__), "settings.yaml")
slackbot_configfile = os.path.join(os.path.dirname(__file__), "settings_slackbot.yaml")

choices = dict()


if choice == "settings.yaml":
    # SOCKETFILE
    print("Path to the socket you've configured LiquidSoap to open:")
    choices['socketfile'] = input("> ")

    # LIQUIDSOAP_VAR_NAME
    print("Name of the interactive.bool variable in LiquidSoap:")
    choices['liquidsoap_var_name'] = input("> ")

    # SLACK_CHANNEL
    print("On which channel in Slack should messages be posted?")
    choices['slack_channel'] = input("> ")

else:
    # SLACK
    print("Slack API Token?")
    choices['slack_token'] = input("> ")

    # LOGFILE
    print("Where would you like the logfile to be?")
    print("Must be writable by the user SlackBot will run as.")
    choices['logfile'] = input("> ")

print("Generating the file...")

# Generate the files!
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
if choice == "settings.yaml":
    template = env.get_template("settings.yaml")
    with open(nattmusikk_configfile, "w") as f:
        f.write(template.render(**choices))

else:
    template = env.get_template("settings_slackbot.yaml")
    with open(slackbot_configfile, "w") as f:
        f.write(template.render(**choices))
