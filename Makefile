.PHONY: run
run: settings.yaml keyfile.txt venv
    venv/bin/python request2liquidsoap.py

settings.yaml: venv
    venv/bin/python generate_settings_file.py server

keyfile.txt: venv
    venv/bin/python generate_keyfile.py keyfile.txt
    chmod 400 keyfile.txt

venv:
    virtualenv -p python3 venv
    . venv/bin/activate && pip install -r requirements.txt

.PHONY: setup
setup: venv keyfile.txt
    venv/bin/python generate_settings_file.py both
    @echo "sudo is potentially needed to create a new user on this system."
    id -u nattmusikk-hele-dagen &>/dev/null || sudo adduser --system --no-create-home --group --disabled-login nattmusikk-hele-dagen
    sudo chown nattmusikk-hele-dagen:nattmusikk-hele-dagen keyfile.txt

.PHONY: wipe
wipe:
    rm -rf venv keyfile.txt settings.yaml settings_slackbot.yaml


