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


#Local Classes from models.py
from bot.models import theBot

#Global Variables
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

#===== Disable Warnings in Security =====
requests.packages.urllib3.disable_warnings()


#======= Web Endpoints for the Bot ==========#
@get("/techx/v1/note/<msg>")
def techxbotPUT(msg):
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''
    bot = theBot() 
    data = {}
    data['roomId'] = bot_room
    data['markdown'] = str(msg)
    #data['file']= "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzZTLid7KPsrcQ6nKGx3WpBky4OJUsJAN13tmFLRk_GQQb3_bs"
    payload = json.dumps(data)
    r = bot.SparkPOST(msg_url,payload,headers)

    return { "response" : str(r.status_code) }

@post('/techx/v1/alert/')
def txtReceiveAlarm():
    '''
    RECEIVING ALERTS FROM GRAFANA AND SENDIT TO Spark
    '''
    bot = theBot()
    alert = request.json
    msg = str(alert['message'])
    url = str(alert['imageUrl'])
    
    data = {}
    
    data['roomId'] = bot_room
    data['markdown'] = msg
    data['file'] = url
    payload = json.dumps(data)
    r = bot.SparkPOST(msg_url,payload,headers)
     
    return {"response" : r.status_code }



@post("/techx/v1/note/")
def txBotNotify():
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''
    bot = theBot()
    note = request.json  
   
    msg = str(note['msg'])
    url = str(note['file'])
    data = {}
    data['roomId'] = bot_room
    data['markdown'] = msg
    data['file']= url
    payload = json.dumps(data)
    r = bot.SparkPOST(msg_url,payload,headers)

    return { "response" : str(r.status_code) }

@post("/techx/v1/ifttt/")
def txbIFTTT():
    '''
    Integration of Amazon Alexa, Spark and IFTT via Webhook
    '''
    data = {}
    cmd = request.json
    action = str(cmd['cmd']).strip().lower()
    personId = str(cmd['personEmail']).strip().lower()
    bot = theBot()
    
    
    resp =  bot.getOrders(personId,action)

    data['roomId'] = bot_room
    data['markdown'] = resp['msg']
    if resp['file'] != '': 
       data['file'] = resp['file']                                      

    payload = json.dumps(data)
    r = bot.SparkPOST(msg_url,payload,headers)
    
    return { "response" : str(r.status_code) }


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

    webhook = request.json   #INFO FROM SPARK IN JSON FORMAT
    get_url = "https://api.ciscospark.com/v1/messages/{0}".format(webhook['data']['id'])      #READ THE MESSAGE ID 
    post_url = "https://api.ciscospark.com/v1/messages/"
    result = bot.SparkGET(get_url,headers)
    result = json.loads(result)
    data['roomId'] = str(webhook['data']['roomId'])
    personId = str(webhook['data']['personId'])

    if 'errors' in result:    #Catch any error from webhook and close procedure
       return

    if webhook['data']['personEmail'] != bot_email:
        in_message = result.get('text','').lower()
        in_message = in_message.replace(bot_name,'')

        #Logic for parsing instruction messages
        resp = bot.getOrders(personId,in_message)
        msg = resp['msg']
        url = resp['file'] 
        
        if url != '':
           data['file'] = url
   
        data['markdown'] = msg 
        payload = json.dumps(data)
        r = bot.SparkPOST(post_url,payload,headers)
        return { "response" : str(r.status_code) }
