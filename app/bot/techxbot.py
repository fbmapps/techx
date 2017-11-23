'''
TECHX BOT FUNCTIONAL SCRIPT
CREATED BY FRBELLO AT CISCO DOT COM
DATE NOV 2017
VERSION 0.1
STATE ALPHA

DESCRIPTION: 
This is the script hosting all the logic for the bot to hears calls from the webhook
this will be publish the GET and POST methods for spark bot. 

'''

#Libraries
from bottle import post,get,put,delete
from bottle import request, response, template
import re, json
import requests
import os,sys

#Local Classes from models.py
from bot.models import SportStats, PrimeAPI



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


#Functions (Spark GET and POST)
def botSparkGET(url,headers):
    '''
    This function will hear any message that webhook receive and will process it accordingly
    '''
    r = requests.request('GET',url,headers=headers)
    contents = r.text
    return contents

def botSparkPOST(url,payload,headers):
    ''''
    This function will send messages to spark room where the bot is invoked
    '''
    contents =  requests.request("POST",url,data=payload,headers=headers)
    return contents


#Web Server Functions (BOTTLE GET,POST)
@get("/techx/<msg>")
def techxbotPUT(msg):
    '''
    This URI is for push message to BOT_ROOM
    will send the message when react to an stimulus
    '''
     
    data = {}
    data['roomId'] = bot_room
    data['markdown'] = str(msg) + " I'm **Reacting** to an Stimulus"
    data['file']= "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzZTLid7KPsrcQ6nKGx3WpBky4OJUsJAN13tmFLRk_GQQb3_bs"
    payload = json.dumps(data)
    r = botSparkPOST(msg_url,payload,headers)

    return str(r.status_code)






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
    resp = {}                #LOCAL RESP DICTIONARY AUXILIARY
    msg = ''                 #THIS WILL BE THE MSG TO BE POSTED AT SPARK ROOM
    url = ''

    nba = SportStats()       #The bot read nba Stats from data.nba.net
    pri = PrimeAPI()         #The bot read PRIME devices status summary 

    webhook = request.json   #INFO FROM SPARK IN JSON FORMAT
    get_url = "https://api.ciscospark.com/v1/messages/{0}".format(webhook['data']['id'])      #READ THE MESSAGE ID 
    post_url = "https://api.ciscospark.com/v1/messages/"
    result = botSparkGET(get_url,headers)
    result = json.loads(result)
    data['roomId'] = str(webhook['data']['roomId'])


    if 'errors' in result:    #Catch any error from webhook and close procedure
       return



    if webhook['data']['personEmail'] != bot_email:
        in_message = result.get('text','').lower()
        in_message = in_message.replace(bot_name,'')

        #Logic for parsing instruction messages
        if 'ruthere' in in_message or 'ready' in in_message:
           msg = "Yes, I'm Here preparing myself to receive **orders** in the near future"
           url = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1033931-200.png'
        elif 'nbarank' in in_message:
           stats = nba.teamStanding()
           east_ttl = "\n**East Conference:** \n"
           west_ttl = "\n**West Conference:** \n"
           east_msg = ''
           west_msg = ''
           
           for stat in stats:
               if stat['conf'] == 'East':
                  east_msg = east_msg + stat['ranking'] + ". **" + stat['teamName'] + "** W:**" + stat['wins'] + "** L: **" + stat['loss'] + "** \n"
               else:
                  west_msg = west_msg + stat['ranking'] + ". **" + stat['teamName'] + "** W:**" + stat['wins'] + "** L: **" + stat['loss'] + "** \n"
           msg = "**Latest NBA Ranking:** \n".format(str(webhook['data']['personEmail'])) + east_ttl + east_msg + west_ttl + west_msg
           url = "http://media.nola.com/hornets_impact/photo/10295491-small.jpg"   
        elif 'nbagame' in in_message:
           today_gm = "\n**Games for Today**\n"
           today_match = '' 
           games = nba.todayGames()
           for game in games:
               today_match = today_match + "- **" + game['vTeam'] + "** AT **" + game['hTeam'] + "**  *" + game['sTime'] +"* \n"
           msg = today_gm + today_match
        elif 'nbaresult' in in_message:
           today_gm = "\n**Games Results for Today**\n"
           today_match = '' 
           games = nba.todayResults()
           for game in games:
               today_match = today_match + "- **" + game['vTeam'] + "** : **"+ game['vScore']  + "** AT **" + game['hTeam'] + "** :  **" + game['hScore'] +"** \n"
           msg = today_gm + today_match
        elif 'getprime' in in_message:
           devs = pri.getDevices()
           if int(devs['queryResponse']['@count']) == 0:
              msg = "**Everything looks Good! All devices seems reachables!!**"
              url = 'https://t6.rbxcdn.com/023c0a0a3aa7fb0629725f2ebe365f8f'
           else:
              msg = "**Right now we have {0} devices Unreachables!!**".format(str(devs['queryResponse']['@count']))
              url = 'https://www.shareicon.net/data/128x128/2016/08/18/815448_warning_512x512.png'
        else: #CATCH ALL SWITCH
           msg = "I do not understand the request. **Ask later!!**"
           url = "https://s-media-cache-ak0.pinimg.com/originals/09/37/fd/0937fd67d480736fa7a623944bd89f4b.jpg"
    
    

    if url != '':
       data['file'] = url
    
    data['markdown'] = msg 
    
    payload = json.dumps(data)
    botSparkPOST(post_url,payload,headers)
    return "{'result' : '200 OK'}"

