from slackclient import SlackClient
import configparser


# Import our config file
config = configparser.ConfigParser()
config.read('bestie.config')

slack_client = SlackClient(config['Slack Auth']['token'])


def list_channels():
	channels_call = slack_client.api_call("channels.list")
	if channels_call.get('ok'):
		return channels_call['channels']
	return None


def channel_info(channel_id):
	channel_info = slack_client.api_call("channels.info", channel=channel_id)
	if channel_info:
		return channel_info['channel']
	return None


def send_message(channel_id, message):
	slack_client.api_call(
		"chat.postMessage",
		channel=channel_id,
		text=message,
		username='Bestie',
		icon_emoji=':bp:'
	)


if __name__ == '__main__':
	channels = list_channels()
	if channels:
		print("Channels: ")
		for c in channels:
			print(c['name'] + " (" + c['id'] + ")")
			""" Channel Testing
			detailed_info = channel_info(c['id'])
			if detailed_info:
				print(detailed_info['latest']['text'])
			if c['name'] == 'bot-testing':
				send_message(c['id'], "Hello " +
							 c['name'] + "! It worked!")
			"""
	else:
		print("Unable to authenticate.")
