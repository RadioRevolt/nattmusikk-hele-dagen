# nattmusikk-hele-dagen
Aktiver og deaktiver nattmusikk-hele-døgnet fra Slack

## Bruk

### Oppsett

1. Sett opp LiquidSoap-skriptet så du kan kommunisere med det via en socket-fil
   (se `example.liq`). Du bør sørge for at man kan bruke socket-fila bare man
   er i `liquidsoap`-gruppa (igjen, se `example.liq`).
2. Sett opp så du bruker en `interactive.bool`-variabel som skal være logisk høy
   når nattmusikk-hele-døgnet er aktivert.
3. Kjør `make setup`, og følg promptene.
4. Kjør `sudo make deploy-upstart` eller `sudo make deploy-systemd`, avhengig
   av hvilket system som kjører hos deg. Ubuntu 15.04 og senere kjører
   SystemD, tidligere kjører Upstart. Kjører du det antikvariske SysV 
   init-systemet, må du skrive en init-fil selv.
5. Kjør `sudo start nattmusikk-hele-dagen` på Upstart eller `sudo systemctl 
   start nattmusikk-hele-dagen` på SystemD for å starte programmet (det skal starte
   automatisk ved oppstart).
6. Legg til en linje i crontab ved å kjøre:

   `sudo crontab -e`

   Linjen:  
   ```
   0 9,17 * * * make -C /sti/til/nattmusikk-hele-dagen user-warn-if-on 2>&1 > /dev/null
   ```

### Slack-bruk

Skriv `.nattmusikk` for hjelp.  
Bruk `.nattmusikk status` hvis du ønsker å vite nåværende status.  
Skriv `.nattmusikk på` for å slå på nattmusikk-hele-døgnet.  
Skriv `.nattmusikk av` for å slå av nattmusikk-hele-døgnet.

Hvis du glemmer å slå av nattmusikk-hele-døgnet, skal det bli postet en
påminnelse på Slack klokken 9 om morningen og 17 på kvelden.

### Make

Les manualen for GNU Make hvis du tenker å se på `Makefile` og du ikke er kjent med
`make` allerede; `make` er et fantastisk verktøy og manualen er bra laga!

Dette er de "offentlige" målene (targets) som `Makefile` støtter:

* (ingenting) eller run: Kjør nattmusikk-hele-dagen.
* warn-if-on: Legg ut påminnelse på Slack hvis nattmusikk-hele-døgnet er aktivert.
* user-run: Kjør nattmusikk-hele-dagen, men som den dedikerte nattmusikk-hele-dagen-brukeren.
  Må kjøres med sudo. Foretrekk denne foran `run`.
* user-warn-if-on: Kjør `make warn-if-on` som nattmusikk-hele-dagen-brukeren. Må kjøres
  med sudo. Foretrekk denne foran `warn-if-on`.
* setup: Sett opp alt som må til før nattmusikk-hele-dagen kan kjøres. Interaktivt.
* deploy-upstart og deploy-systemd: Sørg for at nattmusikk-hele-dagen starter
  automatisk ved oppstart av maskinen. De to variantene er for de to forskjellige
  init-systemene Upstart og SystemD. Må kjøres som med superbruker-rettigheter.
* user: Lag en bruker med navn nattmusikk-hele-dagen og legg den til i liquidsoap-gruppa,
  gitt at brukeren ikke eksisterer ennå.

Det finnes også mange andre, ta en titt på `Makefile` for detaljer.

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

Et Python-program kobler seg til Slack og lytter på meldingene som postes på
relevante kanaler. Hvis noen poster en melding som starter på
`.nattmusikk`, trigges programmet og kan som et resultat gjøre spørringer mot
LiquidSoap for å hente status og endre den interaktive boolske variablen.

Dette er implementert ved å bruke RadioRevolt/SlackBot, fjerne alle
eksisterende plugins og legge inn en ny plugin som kommuniserer med LiquidSoap.
Ved deployment har vi brukt samme token som for RadioRevolt/SlackBot, så det
ser ut som at det tilhører samme bot.
