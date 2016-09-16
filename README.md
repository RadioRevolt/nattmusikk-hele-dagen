# nattmusikk-hele-dagen
Aktiver og deaktiver nattmusikk-hele-døgnet fra Slack

## Bruk

### Oppsett

Ops: ikke alle stegene her er implementert enda.

1. Sett opp LiquidSoap-skriptet så du kan kommunisere med det via en socket-fil
   (se example.liq).
2. Sett opp så du bruker en interactive.bool-variabel som skal være logisk høy
   når nattmusikk-hele-døgnet er aktivert.
3. Kjør `make setup`, og følg promptene.
4. Kopier `keyfile_copy.txt`, `settings_slackbot.yaml` og `slack2request.py` over til
   din SlackBot instans.
5. Når du er på serveren med SlackBot-instansen:
   * `mv keyfile{_copy,}.txt`
   * `chmod 400 keyfile.txt`
   * `sudo chown navn-på-slackbot-bruker:navn-på-slackbot-gruppe keyfile.txt`
5. Slett `keyfile_copy.txt` fra serveren med LiquidSoap.
6. Kjør `sudo systemctl start nattmusikk-hele-dagen` (SystemD)
7. Restart SlackBot

Alternativt oppsett (ikke holdt oppdatert, vil fjernes en gang):

1. `virtualenv -p python3 venv`
2. `. venv/bin/activate`
3. `pip install -r requirements.txt`
4. `sudo adduser --system --no-create-home --group --disabled-login nattmusikk-hele-dagen`
5. ``
6. Resten av stegene er ikke implementert enda (antar SystemD brukes):

   `sudo cp nattmusikk-hele-dagen.service /etc/systemd/system/`
7. Rediger `/etc/systemd/system/nattmusikk-hele-dagen.service` og fyll inn
   manglende detaljer.
8. `sudo systemctl enable nattmusikk-hele-dagen`
9. Endre LiquidSoap-skriptet så det bruker en interactive bool med navnet du
   brukte i steg 7. Du må også sette opp bruk av en socket-fil. Se
   `liquidsoap_example.liq`
9. `sudo systemctl start nattmusikk-hele-dagen`
10. Kopier nøkkel-fila (du må være superbruker for å lese den) og putt den
    samme fila på maskinen med SlackBot.
11. Integrer `slack2request.py` med rammeverket ditt.

### Slack-bruk

Skriv `.nattmusikk` for hjelp.
Bruk `.nattmusikk status` hvis du ønsker å vite nåværende status.

Skriv `.nattmusikk på` for å slå på nattmusikk-hele-døgnet.
Skriv `.nattmusikk av` for å slå av nattmusikk-hele-døgnet.

Merk at Anna må være oppe for at dette skal fungere.

Hvis du glemmer å slå av nattmusikk-hele-døgnet, skal det bli postet en
påminnelse på Slack klokken 9 om morningen og 17 på kvelden.

## Bakgrunn

Mellom 0 og 7 går det nattmusikk på Radio Revolt. Denne nattmusikken er en egen
stream i LiquidSoap, som består av låter fra en spesifikk mappe (med noen
jingler kastet inn). Samtidig så kan du ha en sending fra studio ved å ganske
enkelt sette et av studioene på lufta og starte sendinga. Du trenger ikke gjøre
noenting for å skru av nattmusikken.

Nattmusikken er implementert ved at den spilles når det er "stille på lufta"
mellom 0 og 7. Det vil si at hvis det er stille fra alle studioene i 12
sammenhengende sekunder, så vil en fallback kicke inn. 0-7 er dette nattmusikk,
7-24 er dette "tekniske problemer"-jingelen og vi varsles om problemene. Er det
stille fra nattmusikken i 12 sammenhengende sekunder, vil også "tekniske
problemer"-jingelen brukes og vi vil varsles.

"Tekniske problemer"-jingelen er en evig loop av Patrik Alm sin "tekniske
problemer"-låt. Den går i ett minutt før den looper. Hver gang den looper,
kjøres et Python-skript som sender oss beskjed på Slack om at det er "Stille på
streamn(sic)".

Problemet dette prosjektet ønsker å løse, er at vi ofte vil bli spammet ned av
Anna når det er langvarig stille-på-lufta, for eksempel når det har vært
strømbrudd og vi ikke har fått opp pappagorg, men streamer er oppe. Vi har da
ikke tilgang til radioarkivet der alle reprisene ligger, men streamer kjefter
likevel på oss om at det er stille på lufta. Dette blir plagsomt i lengden, så
derfor pleier vi å gå inn i LiquidSoap-konfigurasjonen og sette på det jeg liker
å kalle **"Nattmusikk hele døgnet"**. Det vil si at vi setter nattmusikken til
å kjøre 0-24, slik at lytterne har noe å høre på og vi slipper å bli varslet
hvert minutt.

Det er ganske slitsomt å måtte logge seg inn på streamer hver gang vi trenger å
gjøre dette (spesielt siden det er under spesielt stressende omstendigheter
behovet melder seg). Derfor ønsker jeg å **gjøre det enkelt** å aktivere
nattmusikk-hele-døgnet når vi vet at det blir langvarig stillhet, og deaktivere
når vi er tilbake i vanlig drift. For at vi ikke skal glemme å slå det av, skal
vi også varsles når det har vært på i lengre tid.

## Design

I LiquidSoap lager vi oss en interaktiv bool - det vil si en variabel som kan
endre verdi når som helst, og som kan endre hvilken stream som brukes også.
Vi setter også opp slik at eksterne program kan kommunisere med
LiquidSoap-serveren.

Et Python-program vil lytte etter HTTP-requests, og autentisere disse.
Avhengig av hva avsenderen ønsker, vil programmet kommunisere med
LiquidSoap-serveren og endre verdien til den nevnte variabelen og hente dens
nåværende verdi.

På en annen maskin vil en annen Python-modul kommunisere med Python-programmet
fra forrige avsnitt, og fungere som et lag mellom den og Slack.

## Protokoll

I utgangspunktet bør kryptert HTTP brukes (HTTPS), men det er ikke alltid like
lett å få til. Et passord og et engangspassord brukes for å autentisere
klienten, Dette betyr at de hemmelige nøklene er lagret både hos klient og
server, og at begge må være synkronisert i tid.

Hvis en angriper får tilgang til én av maskinene, vil han eller hun kunne skru
nattmusikk-hele-døgnet av eller på. Derfor er programvaren laget slik at det
postes på Slack hver gang nattmusikk-hele-døgnet skrus av eller på. Dette gjøres
på server-sida, for å sikre at ikke en angriper på egen maskin kan gå forbi
rapporteringen.

For å endre og hente status på nattmusikk-hele-døgnet, sender du en
POST-request til root der request2liquidsoap.py kjører. Den skal inneholde tre
POST-felter:

* **`password`**: Passordet, som er lagret i keyfile.txt.
* **`onetime_password`**: Éngangspassordet, generert med nøkkelen i keyfile.txt.
* **`action`**: Én av status, on eller off, avhengig av hva du ønsker å gjøre.

Uansett hvilken `action` du velger, så vil responsen være JSON med følgende
felter:
* **`onetime_password`**: Et éngangspassord, generert med den andre nøkkelen
    i keyfile.txt. Brukes for å forsikre seg om at serveren godkjente
    innloggingen.
* **`status`**: `true` hvis nattmusikk-hele-døgnet er aktivert, `false` hvis
    ikke.

