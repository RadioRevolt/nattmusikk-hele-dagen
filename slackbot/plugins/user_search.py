from urllib.request import urlopen, quote
from json import loads

outputs = []

URL = 'https://bruker.smint.no/search/index.php'


def process_message(data):
    if data['text'].startswith('.finn '):
        term = data['text'][6:]
        if len(term) < 1:
            return
        result = loads(urlopen(URL + '?s=' + quote(term)).read().decode())[:7]
        for person in result:
            name = person['cn'] if person['cn'] is not None else 'ukjent navn'
            username = person['uid']
            phone = person['tlf'] if person['tlf'] is not None else 'ukjent tlf.'
            mail = person['mail'] if person['mail'] is not None else 'ukjent mail'
            outputs.append([data['channel'], name + ' (' + username + '): ' + phone + ' // ' + mail])
