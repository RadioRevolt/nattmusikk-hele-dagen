import yaml
from liquidsoap_boolean import LiquidSoapBoolean


def parse_config(configfile):
    with open(configfile) as f:
        doc = yaml.load(f)
    socketfile = doc["socketfile"]
    ls_var_name = doc["liquidsoap_var_name"]

    return socketfile, ls_var_name


SOCKETFILE, LS_VAR_NAME = parse_config("settings.yaml")

interactive_bool = LiquidSoapBoolean(SOCKETFILE, LS_VAR_NAME)

outputs = []


def process_message(data):
    global outputs
    to_output = []
    if data['text'].startswith('.nattmusikk'):
        if data['text'].strip() in ('.nattmusikk', '.nattmusikk hjelp',
                                    '.nattmusikk help'):
            to_output.append("\n".join([
                "`.nattmusikk [hjelp|status|på|av]`",
                ".nattmusikk kan brukes for å slå av eller på nattmusikk-hele-"
                "døgnet. Når påslått, vil stille-på-lufta ignoreres, og "
                "nattmusikk vil brukes i stedet for tekniske problemer-jingelen"
                ".",
                "Bruk `.nattmusikk status` for å se om nattmusikk-hele-døgnet "
                "er aktivert eller ikke.",
                "Bruk `.nattmusikk på` for å skru på nattmusikk-hele-døgnet.",
                "Bruk `.nattmusikk av` for å skru av nattmusikk-hele-døgnet.",
            ]))
        else:
            command = data['text'].strip().split(' ')[1]
            with interactive_bool:
                if command in ('på', 'on', 'true'):
                    interactive_bool.value = True
                    to_output.append("Nattmusikk-hele-døgnet er skrudd *PÅ*. \nDere vil *_ikke_*"
                              " lenger få advarsel når det er stille på lufta "
                              "(annet enn når nattmusikken er stille).\n"
                              "Skriv `.nattmusikk av` når det er vanlig drift igjen.")
                elif command in ('av', 'off', 'false'):
                    interactive_bool.value = False
                    to_output.append("Nattmusikk-hele-døgnet er skrudd *AV*.\n"
                              "Normal drift gjenopptatt.")
                elif command in ('status', 'verdi'):
                    interactive_bool.force_update()
                    if interactive_bool.value:
                        to_output.append("Nattmusikk-hele-døgnet er *PÅSLÅTT*.\nDere "
                                       "vil *IKKE* få beskjed hvis det blir stille på lufta.")
                    else:
                        to_output.append("Nattmusikk-hele-døgnet er slått *av*.")
                else:
                    to_output.append("Kjente ikke igjen '%s', skriv `.nattmusikk "
                                   "hjelp` for bruksanvisning." % command)
    outputs = [(data['channel'], line) for line in to_output]
