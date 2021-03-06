'''
TECHX BOT FUNCTIONAL SCRIPT
CREATED BY FRBELLO AT CISCO DOT COM
DATE NOV 2017
VERSION 1.0
STATE RC1

DESCRIPTION: 
This is the script hosting all the logic for the bot to hears calls from the webhook
this will be publish the GET and POST methods for spark bot. 

'''

#Libraries
#========= microframeworks ====================
from bottle import post,get,put,delete
from bottle import request, response, template, static_file, hook

from flask import Flask, request, render_template as template, make_response, jsonify, abort
from flask_ask import Ask, statement, question, session

#======== Common Libraries ====================
import re, json
import requests
import os,sys

from requests_toolbelt.multipart.encoder import MultipartEncoder

#Local Classes from models.py
from bot.models import theBot

#Local CLasses from Monitor
from bot.botmonitor import botMonitorAPI



#Import CiscoSparkAPI()
from ciscosparkapi import CiscoSparkAPI,Webhook

#Import Logging
import logging
import logging.handlers
from datetime import datetime

#Global Variables
global bot_token
global bot_email
global bot_name 
global bot_room 
global msg_url 
global headers

#Token Retrieve
bot_token = str(os.environ['BOT_KEY'])
bot_email = str(os.environ['BOT_EMAIL'])
bot_name = str(os.environ['BOT_NAME'])
bot_room = str(os.environ['BOT_ROOM'])
req_room = str(os.environ['REQ_ROOM'])
slg_room = str(os.environ['SLG_ROOM'])
clus_tkn = str(os.environ['SPARK_ACCESS_TOKEN'])
clive_room = str(os.environ['SPARK_BASE_ROOM'])

msg_url = "https://api.ciscospark.com/v1/messages/"
headers = {"Accept" : "application/json", 
           "Content-Type" : "application/json" , 
           "cache-control" : "no-cache" , 
           "Authorization" : "Bearer " +bot_token 
          }


#========== Flask Instance ==========
app = Flask(__name__)
ask = Ask(app,'/clive_skill')


#========== Versioning ==============
__author__ = "Freddy Bello"
__author_email__ = "frbello@cisco.com"
__copyright__ = "Copyright (c) 2016-2018 Cisco and/or its affiliates."
__license__ = "MIT"


#=========== Define a Logger ==============#
logger = logging.getLogger('cliveBot')
LOG_FILENAME = 'clivebot.log'

# set up the logger
logger.setLevel(logging.DEBUG)

#File Rotation
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=2048000, backupCount=5)

# File Logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

#Console Logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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
    logger.info('Sending Message {}'.format(str(data['markdown'])))              
    r = bot.SparkPOST(msg_url,payload,headers)
    if r.status_code != 200:
        logger.error('Message sends Fail code {}'.format(str(r.status_code)))
    logger.info('Message sent sucessfully!!!')
    return str(r.status_code)


#======= Allow CORS ============
_allow_origin = "*"
_allow_methods = 'PUT, GET, POST, DELETE, OPTIONS'
_allow_headers = 'Authorization, Origin, Accept, Content-Type, X-Requested-With'
_content_type = 'application/json'
@hook('after_request')
def enable_cors():
    '''Add Headers to enable CORS'''
    response.headers['Access-Control-Allow-Origin'] = _allow_origin
    response.headers['Access-Control-Allow-Methods'] = _allow_methods
    response.headers['Access-Control-Allow-Headers'] = _allow_headers
    response.headers['Content-Type'] = _content_type


#======= Bottle GET Endpoints for the Bot ==========#
@get("/techx/v1/mon/endpoints/")
def getEnpoints():
    '''
    Read Bot Endpoints
    '''
    mon = botMonitorAPI()
    endp = mon.prepareURIList()
    
    return endp


@get("/techx/v1/mon/orders/")
def getOrdersList():
    '''
    Read Bot Order List
    '''
    mon = botMonitorAPI()
    orders = mon.prepareOrderList()

    return orders


@get("/techx/v1/mon/check/")
def getHealth():
    '''
    Check Backend Status
    '''
    mon = botMonitorAPI()
    check = mon.CheckBackendServices()

    return check

@get("/techx/v1/note/<msg>")
def techxbotPUT(msg):
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''
    r = botMessenger(str(msg))
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



#========= Flask GET URI Methods ===================

@app.route('/techx/v1/base/')
def test_uri():    
    return "<h1>Bot Served by Flasks</h1>"

@app.route('/techx/v1/mon/endpoints/',methods=['GET'])
def flask_endpoints():
    edp = getEnpoints()
    return jsonify(edp) 

@app.route('/techx/v1/mon/orders/',methods=['GET'])
def flask_orders():
    orders =  getOrdersList()
    return jsonify(orders)

@app.route('/techx/v1/mon/check/',methods=['GET'])
def flask_health():
    health = getHealth()
    return jsonify(health) 

#========== Flask POST URI Methods =============

@app.route('/techx/v2/elk/',methods=['POST'])
def flask_ELK():
    resp = txtElkNotify()
    return jsonify(resp) 

@app.route('/techx/v2/alert/',methods=['POST'])
def flask_Alert():
    resp = txtReceiveAlarm()
    return jsonify(resp)

@app.route('/techx/v1/note/',methods=['POST'])
def flask_Note():
    resp = txBotNotify()
    return jsonify(resp)

@app.route('/techx/v1/ifttt/',methods=['POST'])
def flask_IFTTT():
    resp = txbIFTTT()
    return jsonify(resp)

@app.route('/techx/',methods=['POST'])
def flask_Bot():
    resp = techxbot()
    return jsonify(resp)
 


#========== Bottle POST CALLS TO BOT ==================
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
   
    logger = logging.getLogger('cliveBot.ELK')

    try:
        note = request.json
    except:
        return
    roomId = slg_room
    if not roomId:
        roomId = os.environ['SLG_ROOM']
        logger.warning('Using Default Syslog Room. Please check the environmental variables' )
    
    msg = str(note['msg'])
    r = ''   
    
    clive_token = clus_tkn 
    if not clive_token:
        clive_token = os.environ['SPARK_ACCESS_TOKEN']
        logger.warning('Using embeeded token. Please check the environmental variables ') 
       

    try:
        clive = CiscoSparkAPI(access_token=clive_token)
        room = clive.rooms.get(roomId)
        logger.info('Receiving message from ELK and Sending it to room {}. Content={}'.format(room.title,str(msg)))
        clive.messages.create(roomId,markdown=msg)
    except (TypeError,ValueError)as e:
        msg="ELK is trying to tell me something but I am unable to parse the message"
        clive.messages.create(roomId,text=msg) 
        logger.error('ELK Message Reception Fails message:{}'.format(e))

    logger.info('ELK info received and processed sucessfully!!!')
    #print(msg)
    return {'response' : 200 }
    

@post("/techx/v1/note/")
def txBotNotify():
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''

    logger = logging.getLogger('cliveBot.External')

    files = []
    note = request.json  
    msg = str(note['msg'])
    url = str(note['file'])


    roomId = slg_room
    if not roomId:
        roomId = os.environ['SLG_ROOM'] 
        logger.warning('Using Default Syslog Room. Please check the environmental variables' )
    
    #Migrating Notify to CLive
    clive_token = clus_tkn
    if not clive_token:
        clive_token = os.environ['SPARK_ACCESS_TOKEN'] 
        logger.warning('Using embeeded token. Please check the environmental variables ') 
    
    try:
        clive = CiscoSparkAPI(access_token=clive_token)
        room = clive.rooms.get(roomId)
        logger.info('Receiving a Message from outside and Sending it to room. Content={}'.format(room.title,str(msg)))
        files.append(url)
        clive.messages.create(roomId,markdown=msg,files=files)
    except (TypeError,ValueError,SparkApiError) as e:
        msg="An external systems is trying to reachme, but I'm not able to parse the message"
        clive.messages.create(roomId,text=msg) 
        logger.error('External Message reception fails message:{}'.format(e))
    
    #r = botMessenger(msg,url)
    logger.info('Message sent Sucessfully!!! {}'.format(str(msg)))
    return { "response" : r }

@post("/techx/v1/ifttt/")
def txbIFTTT():
    '''
    Integration of Amazon Alexa, Spark and IFTT via Webhook
    '''
    #data from IFTTT Webhook
    cmd = request.json
    action = str(cmd['cmd']).strip().lower()
    _email = str(cmd['personEmail']).strip().lower()
    msg=''
        
 
    logger = logging.getLogger('cliveBot.IOT') 
    logger.info('A request was received via IOT Device')    


    #Migration to CiscoSparkAPI and Clive
    clive_token =  clus_tkn
    if not clive_token:
        clive_token = os.environ['SPARK_ACCESS_TOKEN']
        logger.warning('Using default token. Please check the environmental variables ')


    roomId = clive_room
    if not roomId:
        roomId = os.environ['SPARK_BASE_ROOM']
        logger.warning('Using Default Room. Please check the environmental variables' )


    try:
        clive = CiscoSparkAPI(access_token=clive_token)
        people = clive.people.list(email=_email,max=1)
        for person in people:
            personId = person.id
        room = clive.rooms.get(roomId)
        bot = theBot()
        resp =  bot.getOrders(personId,action,roomId)
        logger.info('Responding IOT requests to room. Content={}'.format(room.title,str(msg)))
        msg = resp['msg']
        clive.messages.create(roomId,markdown=msg)
        logger.info('IOT Order Executed')
        response = {"status_code" : 200}
    except (ValueError,TypeError,Exception) as e:
        logger.error('A request from IOT Device has failed message: {}'.format(e))
        return {"status_code" :  500} 



    return response


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
    
    
    logger = logging.getLogger('cliveBot.WebHook')

    #Techx.bot Instance
    webhook = request.json   #INFO FROM SPARK IN JSON FORMAT
    #print(webhook['data']['personId'])
    #Clive Instance
    
    req_room = webhook['data']['roomId']

    if req_room != os.environ['SLG_ROOM']:
        #print('Ctach Non SLSG')
        return {"status_code" : 203}
    
     
    
    clive_token = clus_tkn
    if not clive_token:
         clive_token = os.environ['SPARK_ACCESS_TOKEN']
         logger.warning('Using the embeeded token. Please check environmentals variables')         

    clive = CiscoSparkAPI(access_token=clive_token)
    clive_wh = Webhook(webhook)
    room = clive.rooms.get(clive_wh.data.roomId)
    message = clive.messages.get(clive_wh.data.id)
    person = clive.people.get(message.personId)
    me = clive.people.me()
    files = []



    try:
        if message.personId == me.id:
            #logger.warning('Can send a message to myself')
            return {"status_code":500}  
        else:
            logger.info('Receiving Data from Spark Room {}'.format(room.title))
            bot = theBot()
            logger.info('Sending Order to Bot: {}'.format(str(message.text))) 
            resp = bot.getOrders(person.id,message.text,room.id)
            msg = resp['msg']
            if not msg:
                msg ='.'
            if resp['files'] !='':
                files.append(resp['files'])
                clive.messages.create(room.id,markdown=msg,files=files)
            else:
                clive.messages.create(room.id,markdown=msg)
            logger.info('Order executed')
            respo = {"status_code": 200}
    except (TypeError,ValueError,Exception) as e:
        msg="Unable to execute the task"
        clive.messages.create(room.id,text=msg) 
        logger.error("Communication Error with Clive message:{}".format(e))
        respo = {"status_code" : 500}

    return respo




#===================== Clive Alexa Skill ===========================#

@ask.launch
def start_clive_skill():
    welcome_message = template('welcome')
    reprompt_message = template('reprompt')

    return question(welcome_message) \
           .reprompt(reprompt_message)



