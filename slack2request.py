import requests
import pyotp
import warnings
import yaml


def parse_config(configfile):
    with open(configfile) as f:
        doc = yaml.load(f)
    keyfile = doc['keyfile']
    port = doc['port']
    host = doc['host']
    https = doc['https']

    if not https:
        warnings.warn("Not connecting to the server securely. This is only "
                      "acceptable during development!")

    return keyfile, port, host, https


def parse_keyfile(keyfile):
    with open(keyfile, "r") as f:
        lines = f.readlines()
    keys = [line.strip() for line in lines if line.strip()]
    return [pyotp.TOTP(key) for key in keys[:3]], keys[3]


KEYFILE, PORT, HOST, USE_HTTPS = parse_config("settings_slackbot.yaml")
OTPS, PASSWORD = parse_keyfile(KEYFILE)


def set_nightmusic(enabled):
    send_to_server("on" if enabled else "off")


def send_to_server(action):
    r = requests.post("http%s://%s:%s" % ("s" if USE_HTTPS else "", HOST, PORT),
                      data={"password": PASSWORD,
                            "onetime_password": OTPS[0].now(),
                            "action": action})
    r.raise_for_status()
    data = r.json()
    if not OTPS[1].verify(data['onetime_password']):
        raise RuntimeError("Could not verify the authenticity of the server."
                           " Are the credentials right?")
    return data['status']


outputs = []


def process_message(data):
    if data['text'].startswith('.nattmusikk'):
        if data['text'].strip() in ('.nattmusikk', '.nattmusikk hjelp',
                                    '.nattmusikk help'):
            outputs.extend([
                "`.nattmusikk [hjelp|status|på|av]`",
                ".nattmusikk kan brukes for å slå av eller på nattmusikk-hele-"
                "døgnet. Når påslått, vil stille-på-lufta ignoreres, og "
                "nattmusikk vil brukes i stedet for tekniske problemer-jingelen"
                ".",
                "Bruk `.nattmusikk status` for å se om nattmusikk-hele-døgnet "
                "er aktivert eller ikke.",
                "Bruk `.nattmusikk på` for å skru på nattmusikk-hele-døgnet.",
                "Bruk `.nattmusikk av` for å skru av nattmusikk-hele-døgnet.",
            ])
        else:
            command = data['text'].strip().split(' ')[1]
            if command in ('på', 'on', 'true'):
                action = 'on'
            elif command in ('av', 'off', 'false'):
                action = 'off'
            elif command in ('status', 'verdi'):
                action = 'status'
            else:
                outputs.append("Kjente ikke igjen '%s', skriv `.nattmusikk "
                               "hjelp` for bruksanvisning." % command)
                return

            status = send_to_server(action)
            if command in ('status', 'verdi'):
                if status:
                    outputs.append("Nattmusikk-hele-døgnet er PÅSLÅTT.")
                    outputs.append("Dere vil IKKE få beskjed hvis det blir stille på lufta.")
                else:
                    outputs.append("Nattmusikk-hele-døgnet er slått av.")


def main():
    import sys
    action = sys.argv[1]
    print(send_to_server(action))

if __name__ == '__main__':
    main()
