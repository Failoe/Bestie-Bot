from flask import Flask, request, Response
import configparser

# Import our config file
config = configparser.ConfigParser()
config.read('bestie.config')

app = Flask(__name__)
SLACK_WEBHOOK_SECRET = config['Slack Auth']['token']


@app.route('/slack', methods=['POST'])
def inbound():
	if request.form.get('token') == SLACK_WEBHOOK_SECRET:
		channel = request.form.get('channel_name')
		username = request.form.get('user_name')
		text = request.form.get('text')
		inbound_message = username + " in " + channel + " says: " + text
		print(inbound_message)
	return Response(), 200


@app.route('/', methods=['GET'])
def test():
	return Response('It works!')


if __name__ == '__main__':
	app.run(debug=True)
