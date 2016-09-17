import sys, os.path
sys.path.append(os.path.abspath("slackbot"))

from slackbot.plugins.nattmusikk import interactive_bool, send_to_slack

with interactive_bool:
    if interactive_bool.value:
        send_to_slack("Påminnelse: Nattmusikk-hele-døgnet er for øyeblikket "
                      "*PÅSLÅTT*. Husk å skru det av når normal drift er "
                      "gjenopptatt ved å skrive `.nattmusikk av`!")
