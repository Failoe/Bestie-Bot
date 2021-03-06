# -*- coding: utf-8 -*-
"""
A routing layer for the onboarding bot tutorial built using
[Slack's Events API](https://api.slack.com/events-api) in Python
"""
import json
import bot
from flask import Flask, request, make_response, render_template
import configparser
import requests
from pprint import pprint
from bestie_utils.db_utils import *
from bestie_utils.collections import *

pyBot = bot.Bot()
slack = pyBot.client

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('bestie.config')

bc_emoji = config['BestCoin']['emoji']

test_count = 0

def _event_handler(event_type, slack_event):
    """
    A helper function that routes events from Slack to our Bot
    by event type and subtype.

    Parameters
    ----------
    event_type : str
        type of event recieved from Slack
    slack_event : dict
        JSON response from a Slack reaction event

    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error

    """
    team_id = slack_event["team_id"]
    # ================ Team Join Events =============== #
    # When the user first joins a team, the type of event will be team_join
    if event_type == "team_join":
        user_id = slack_event["event"]["user"]["id"]
        # Send the onboarding message
        pyBot.onboarding_message(team_id, user_id)
        return make_response("Welcome Message Sent", 200,)

    # ============== Share Message Events ============= #
    # If the user has shared the onboarding message, the event type will be
    # message. We'll also need to check that this is a message that has been
    # shared by looking into the attachments for "is_shared".
    elif event_type == "message" and slack_event["event"].get("attachments"):
        user_id = slack_event["event"].get("user")
        if slack_event["event"]["attachments"][0].get("is_share"):
            # Update the onboarding message and check off "Share this Message"
            pyBot.update_share(team_id, user_id)
            return make_response("Welcome message updates with shared message",
                                 200,)

    # ============= Reaction Added Events ============= #
    # If the user has added an emoji reaction to the onboarding message
    elif event_type == "reaction_added":
        user_id = slack_event["event"]["user"]
        reaction_emoji = slack_event['event']['reaction']
        print("{} added {} emoji to the post.".format(user_id, reaction_emoji))
        # Update the onboarding message
        # pyBot.update_emoji(team_id, user_id)
        return make_response("Reaction added", 200,)

    elif event_type == 'reaction_removed':
        user_id = slack_event["event"]["user"]
        reaction_emoji = slack_event['event']['reaction']
        print("{} removed {} emoji from the post.".format(user_id, reaction_emoji))
        return make_response("Reaction removed", 200,)

    # =============== Pin Added Events ================ #
    # If the user has added an emoji reaction to the onboarding message
    elif event_type == "pin_added":
        user_id = slack_event["event"]["user"]
        # Update the onboarding message
        pyBot.update_pin(team_id, user_id)
        return make_response("Welcome message updates with pin", 200,)

    # =============== Primary Message Handler ========= #
    # Lets just ignore messages from bots for our sanity
    elif event_type == "message" and slack_event['event'].get('subtype') != 'bot_message':
        # This limits messages to the bot-testing channel
        if slack_event['event']['channel'] == 'C98LD3BGV':
            user_id = slack_event["event"].get("user")
            event_text = slack_event['event'].get('text')
            if event_text.startswith('!'):
                if event_text.startswith('!add '):
                    tag_conn = pgsql_connect('bestie.config')
                    add_tag(tag_conn, slack_event)
                    tag_conn.close()
                elif event_text.startswith('!remove '):
                    tag_conn = pgsql_connect('bestie.config')
                    remove_tag(tag_conn, slack_event)
                    tag_conn.close()
                elif event_text.startswith('!pick '):
                    tag_conn = pgsql_connect('bestie.config')
                    send_message(   slack_event['event']['channel'],
                                    pick_item(tag_conn, slack_event)
                                )
                    tag_conn.close()
            elif slack_event['event']['text'].startswith("What's good?"):
                send_message(slack_event['event']['channel'], 'Nothin\' much homie.')
                return make_response("Informed users what is good", 200,)
            
            # Onboarding message test
            elif slack_event['event']['text'] == "Onboarding Test":
                pyBot.onboarding_message(team_id, user_id)
                return make_response("Onboarding message sent", 200)

            # Form test
            elif slack_event['event']['text'] == "Form":
                post_message = pyBot.send_form(team_id, user_id, slack_event)
                return make_response("Test form sent", 200)

            # test_count += 1


            # send_message(slack_event['event']['channel'], "Responding to: {}\nOriginal post at: {}".format(
            #     slack_event['event']['text'],
            #     slack_event['event']['ts']))
            # if slack_event["event"]["attachments"][0].get("is_share"):
            #     # Update the onboarding message and check off "Share this Message"
            #     pyBot.update_share(team_id, user_id)
            return make_response("Message received", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/install", methods=["GET"])
def pre_install():
    """This route renders the installation page with 'Add to Slack' button."""
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = pyBot.oauth["client_id"]
    scope = pyBot.oauth["scope"]
    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return render_template("install.html", client_id=client_id, scope=scope)


@app.route("/thanks", methods=["GET", "POST"])
def thanks():
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    pyBot.auth(code_arg)
    return render_template("thanks.html")


@app.route("/listening", methods=["GET", "POST"])
def hears():
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    slack_event = json.loads(request.data)
    print("/listening output")
    pprint(slack_event)
    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if pyBot.verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s \npyBot has: \
                   %s\n\n" % (slack_event["token"], pyBot.verification)
        # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subcribed to
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        # Then handle the event by event_type and have your bot respond
        # if slack_event['event'].get('subtype') != 'bot_message':
        #     print("Bot message stopped.")
        #     return make_response("Stopped bot message.", 200)
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/interact", methods=["GET", "POST"])
def interact():
    slack_event = request.json
    print("EVENT RECEIVED 0")
    pprint(slack_event)
    print("EVENT RECEIVED 1")
    return make_response("Form received", 200)


@app.route("/outgoinghook", methods=["GET", "POST"])
def outgoinghook():
    print("Exclamation Point Received")


def send_message(channel_id, message):
    print("Sending message: {}".format(message))
    test = pyBot.client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username='Bestie',
        icon_emoji=':bp:'
    )
    # print(test)
    print("Message sent.")

if __name__ == '__main__':
    app.run(host=config['Flask']['host'], port=int(config['Flask']['port']), debug=True)
