#! python3
from urllib.request import urlopen
import random

outputs = []

url = "http://mentalfloss.com/api/1.0/views/amazing_facts?id="
top = 1560
bottom = 15
replace = {'\\"': '"'} 
remove = ["<strong>", "</strong>", "<em>", "</em>"]

def process_message(data):
	if data["text"] in [".fun", ".funfact", ".fact"]:
		info = "[]"
		while info == "[]":
			info = urlopen(url + str(random.randint(bottom, top))).read().decode()
		fact = info.split("</p>")[0][12:]
		for a in replace:
			fact = fact.replace(a, replace[a])
		for a in remove:
			fact = fact.replace(a, "")
		outputs.append([data["channel"], fact])
