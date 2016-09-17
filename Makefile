# Run/deploy nattmusikk-hele-dagen
.PHONY: run
run: settings.yaml settings_slackbot.yaml .installed_requirements
	venv/bin/python slackbot/rtmbot.py -c settings_slackbot.yaml

# Configuration files, can be generated through helpful user interface
settings.yaml settings_slackbot.yaml: | .installed_requirements
	venv/bin/python generate_settings_file.py "$@"

# Unit files
nattmusikk-hele-dagen.conf: templates/nattmusikk-hele-dagen.conf | .installed_requirements
	venv/bin/python generate_unit_file.py upstart "$@"

nattmusikk-hele-dagen.service: templates/nattmusikk-hele-dagen.service | .installed_requirements
	venv/bin/python generate_unit_file.py systemd "$@"

# Virtual environment
venv:
	virtualenv -p python3 venv

# This file is used just to make sure we adopt to changes in 
# requirements.txt. Whenever they change, we install the packages
# again and touch this file, so its modified date is set to now.
.installed_requirements: requirements.txt slackbot/requirements.txt | venv
	. venv/bin/activate && pip install -r requirements.txt
	touch .installed_requirements

# User to create for running this application
USER = "nattmusikk-hele-dagen"

# Create USER if it doesn't exist yet
.PHONY: user
user:
	@echo "sudo is potentially needed to create a new user on this system."
	id -u $(USER) > /dev/null 2>&1 || sudo adduser --system --no-create-home --group --disabled-login $(USER)

# Make the application ready for deployment
.PHONY: setup
setup: .installed_requirements settings.yaml settings_slackbot.yaml user

# Remove any local user-files from the folder
.PHONY: wipe
wipe:
	rm -rf venv settings.yaml settings_slackbot.yaml


