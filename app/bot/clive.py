'''
CLIVE FUNCTIONAL SCRIPT
CREATED BY FRBELLO AT CISCO DOT COM
DATE NOV 2018
VERSION 1.0
STATE BETA

DESCRIPTION: 
This is the script hosting all the logic for the bot to hears calls from the webhook
this will be publish the GET and POST methods for spark bot. 

'''
#Libraries
from ciscosparkapi import CiscoSparkAPI, Webhook
import os,sys

bot_token = "OTUwNWQzNGYtNjgwNi00OWE5LTlmNDAtMjZlMTA1ZTA2ZGU2NDlhZmMzNDYtMzI1"

api = CiscoSparkAPI(access_token=bot_token)

all_rooms = api.rooms.list()

# Create a Room
demo_room = api.rooms.create('Clive Machine Shop')

email_addresses = ['frbello@cisco.com', 'rydsouza@cisco.com']

for email in email_addresses:
    api.memberships.create(demo_room.id,personEmail=email)

#Post a Message
api.messages.create(demo_room.id, text="Welcome to the room!")


