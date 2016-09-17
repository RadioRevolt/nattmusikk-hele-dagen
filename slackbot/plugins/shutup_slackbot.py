outputs = []

def process_message(data):
	if data["text"] in ["Bpye Berg Nyberg"]:
		outputs.append([data["channel"], "Hold kjeft, slackbot..."])
