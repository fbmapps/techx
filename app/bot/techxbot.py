'''
TECHX BOT FUNCTIONAL SCRIPT
CREATED BY FRBELLO AT CISCO DOT COM
DATE NOV 2017
VERSION 0.3
STATE BETA

DESCRIPTION: 
This is the script hosting all the logic for the bot to hears calls from the webhook
this will be publish the GET and POST methods for spark bot. 

'''

#Libraries
from bottle import post,get,put,delete
from bottle import request, response, template, static_file
import re, json
import requests
import os,sys

from requests_toolbelt.multipart.encoder import MultipartEncoder

#Local Classes from models.py
from bot.models import theBot
from bot.botutils import *

#Import CiscoSparkAPI()
from ciscosparkapi import CiscoSparkAPI,Webhook



#Global Variables
global bot_token
global bot_email
global bot_name 
global bot_room 
global msg_url 
global headers


bot_token = str(os.environ['BOT_KEY'])
bot_email = str(os.environ['BOT_EMAIL'])
bot_name = str(os.environ['BOT_NAME'])
bot_room = str(os.environ['BOT_ROOM'])
msg_url = "https://api.ciscospark.com/v1/messages/"
headers = {"Accept" : "application/json", 
           "Content-Type" : "application/json" , 
           "cache-control" : "no-cache" , 
           "Authorization" : "Bearer " +bot_token 
          }



__author__ = "Freddy Bello"
__author_email__ = "frbello@cisco.com"
__copyright__ = "Copyright (c) 2016-2018 Cisco and/or its affiliates."
__license__ = "MIT"




#===== Disable Warnings in Security =====
requests.packages.urllib3.disable_warnings()

#=========== Common Functionality ===========#
def botMessenger(msg,url=''):
    '''DRY Messenger Function '''
    bot = theBot() 
    data = {}
    files = []
    data['roomId'] = bot_room
    data['markdown'] = msg

    #Building the payload
    if url != '':
        files = [url]
        data['files'] = files

    
    payload = json.dumps(data)              
    r = bot.SparkPOST(msg_url,payload,headers)
    return str(r.status_code)






#======= Web Endpoints for the Bot ==========#
@get("/techx/v1/note/<msg>")
def techxbotPUT(msg):
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''
    r = botMessenger(str(msg))
    return { "response" : r }

@post('/techx/v1/alert/')
def txtReceiveAlarm():
    '''
    RECEIVING ALERTS FROM GRAFANA AND SENDIT TO Spark
    '''
    alert = request.json
    msg = str(alert['msg'])
    url = str(alert['file'])
    
     
    r = botMessenger(msg,url)
    return {"response" : r}

@post('/techx/v2/elk/')
def txtElkNotify():
    '''
    This URI is for receive data from logstash parser
    '''

    note = request.json

    msg = str(note['msg'])
    r = ''    
    print(msg)
    return {'response' : r }
    

@post("/techx/v1/note/")
def txBotNotify():
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''
    note = request.json  
   
    msg = str(note['msg'])
    url = str(note['file'])
    r = botMessenger(msg,url)

    return { "response" : r }

@post("/techx/v1/ifttt/")
def txbIFTTT():
    '''
    Integration of Amazon Alexa, Spark and IFTT via Webhook
    '''
    #data from IFTTT Webhook
    cmd = request.json
    action = str(cmd['cmd']).strip().lower()
    personId = str(cmd['personEmail']).strip().lower()
    

    bot = theBot()
    resp =  bot.getOrders(personId,action)
    
    url = ''
    msg = resp['msg']
    if resp['files'] != '': 
       url = resp['files']                                      



    r = botMessenger(msg,url)
    
    return { "response" : r }


@get("/techx/")
def techxbotGET():
    '''
    This function will catch any Web Browser Attempt to
    Connect to BOT URI.
    Will Respond with a Splash Page
    Can Be expanded to a Instructional Page
    a template should be created on the template folder
    to catch the variable in msg
    '''
    msg = "Techx BOT is Getting Ready to Rumble!!!"
    return template("say_hi",msg=msg)


@get("/techx/static/img/<filepath:re:.*\.(jpg|png|gif|ico|svg)>")
def img(filepath):
    return static_file(filepath, root="/var/www/html/static/img")

@post("/techx/")
def techxbot():
    '''
    This is the Web Server URI for the Call to bot from Web Hook
    http://<PUBLIC-IP>:5105/techx/
    This info should be configured at the webhook on developer.ciscospark.com
    '''
    #Local Variables
    data = {}                #LOCAL DATA DICTIONARY TO BUILD THE PAYLOAD TO SEND BACK TO SPARK
    msg = ''                 #THIS WILL BE THE MSG TO BE POSTED AT SPARK ROOM
    url = ''
    
    #API CALLS OBJECTS
    bot = theBot()



    #Techx.bot Instance
    webhook = request.json   #INFO FROM SPARK IN JSON FORMAT
    #get_url = "https://api.ciscospark.com/v1/messages/{0}".format(webhook['data']['id'])      #READ THE MESSAGE ID 
    #post_url = "https://api.ciscospark.com/v1/messages/"
    #result = bot.SparkGET(get_url,headers)
    #result = json.loads(result)
    #data['roomId'] = str(webhook['data']['roomId'])
    #roomId = str(webhook['data']['roomId'])
    #personId = str(webhook['data']['personId'])

    #if 'errors' in result:    #Catch any error from webhook and close procedure
    #   return

    #if webhook['data']['personEmail'] != bot_email:
    #    in_message = result.get('text','').lower()
    #    in_message = in_message.replace(bot_name,'')

        #Logic for parsing instruction messages
    #    resp = bot.getOrders(personId,in_message,roomId)
    #    msg = resp['msg']
    #    url = resp['files'] 
     
    #    r = botMessenger(msg,url)
    #    return { "response" : r }


    #Clive Instance
    clive_token ='OTUwNWQzNGYtNjgwNi00OWE5LTlmNDAtMjZlMTA1ZTA2ZGU2NDlhZmMzNDYtMzI1' # os.environ['SPARK_ACCESS_TOKEN']
    clive = CiscoSparkAPI(access_token=clive_token) 
    clive_wh = Webhook(webhook)
    

    room = clive.rooms.get(clive_wh.data.roomId)
    message = clive.messages.get(clive_wh.data.id)
    person = clive.people.get(message.personId)
    me = clive.people.me()

    files = []

    if message.personId == me.id:
        return
    else:
        resp = bot.getOrders(person.id,message.text,room.id)
        msg = resp['msg']
        if resp['files'] !='':
            files.append(resp['files'])
            clive.messages.create(room.id,markdown=msg,files=files)
        else:
            clive.messages.create(room.id,markdown=msg)






