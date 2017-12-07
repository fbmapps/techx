'''
MODELS FILES TO HANDLE CONNECTION WITH EXTERNAL SERVICES

'''





import requests
import json
import os, sys, time, datetime

#===== Libraries for CMX Maps Processing ======
import base64,re, uuid
from PIL import Image as PilImage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
from tkinter import *

#==== DATABASE Libraries ======
from sqlalchemy import Column, Integer, Sequence, String, DateTime, Boolean 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

#====== DISABLING Security Warnings=======
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


Base = declarative_base()
#db = create_engine('sqlite:///techxdb.db') 

class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True)
    devId = Column(String(100),nullable=False)
    devName = Column(String(100),nullable=False)
    ipAdd = Column(String(20),nullable=False)
    url = Column(String(250))
    location = Column(String(100))
    status = Column(String(100),nullable=False)
    bot_notify_request = Column(Boolean)
    last_bot_notify = Column(DateTime)
    bot_notify_count = Column(Integer) 
    last_status_change = Column(DateTime)
    status_change_count = Column(Integer)
    record_created = Column(DateTime)
    








#============ API CALLS Wrapper =================#
class PrimeAPI():
    def checkStatus(self):
        return {"response" : "200" }

    def __init__(self):
        self.user = str(os.environ['PRM_USER'])                #API USER
        self.passd = str(os.environ['PRM_PASW'])               #API PASS
        self.apiURI = str(os.environ['PRM_URL'])               #PRIME SERVER URL


    def queryAPI(self,url):
        apiurl = self.apiURI + url
        r = requests.get(apiurl,auth=(self.user,self.passd),verify=False)
        result = r.text
        data = json.loads(result)
        return data

    def getAllDevices(self):
         
        url = "/webacs/api/v1/data/Devices.json?.full=true&.sort=ipAddress&.firstResult=0&.maxResults=19"
        data = self.queryAPI(url)
        return data


    def getDevices(self):
        url = "/webacs/api/v1/data/Devices.json?.full=true&.sort=ipAddress&reachability=UNREACHABLE"
        data = self.queryAPI(url)

        return data


class CmxAPI():
    def checkStatus(self):
        return {"response" : "200" }

    def __init__(self):
        self.user =  str(os.environ['CMX_USER'])
        self.passd = str(os.environ['CMX_PASW'])
        self.apiURI = str(os.environ['CMX_URI'])
        self.PATH = str(os.environ['CMX_MAP'])        



    def queryAPI(self,url,content=False):
        apiurl = self.apiURI + url
        r = requests.get(apiurl,auth=(self.user,self.passd),verify=False)
        if content == True:
           data = r.content
        else:
           result = r.text
           data = json.loads(result)
        return data


    def getMap(self):
        url = "api/config/v1/maps"
        data = self.queryAPI(url)
        return data

    def getMapImage(self,img,x,y,lt,wt,ipaddr):

        #declare the file
        file = self.PATH + img
        
        #check if image exist on disk
        if os.path.isfile(file) == True:
           #Encode in Base64 and Store
           fb64 = self.encodeFile(file)
        
        else:
           #Query the API
           url="api/config/v1/maps/imagesource/" + str(img)
           image = self.queryAPI(url,content=True)
           
           #Store the image
           fh = open(file, "wb")
           fh.write(image)
           fh.close()
           
           #Encode Base64 version of the image
           fb64 = self.encodeFile(file)

        imgb = base64.b64decode(fb64)
        mapinmem = BytesIO(imgb)

        data = self.doMapPlot(mapinmem,x,y,lt,wt,ipaddr)

        return { "response" : 200 , "data" : data }
 

    def encodeFile(self,file):
        f = open(file,"rb")
        f_b64 = base64.b64encode(f.read())
        f.close()

        return f_b64    

    def doMapPlot(self,mapinmem,x,y,lt,wt,ipaddr):
        ''' Ploting method to put IP in map with a BullEye'''
        buff = BytesIO() 
        #_im=plt.imread(StringIO(mapinmem.decode('base64')), format='jpeg')

        convertedim = PilImage.open(mapinmem).convert('P')
        #Plot over the image 

        implot = plt.imshow(convertedim, extent=[0,wt,0,lt], origin='lower', aspect=1)

       
        #Mark IP Coordinates received from CMX
        
        plt.scatter([x],[y],facecolor='r',edgecolor='r')
        plt.scatter([x],[y],s=1000, facecolor='none',edgecolor='r')
        plt.scatter([x],[y],s=2000, facecolor='none',edgecolor='r')
        plt.scatter([x],[y],s=3500, facecolor='none',edgecolor='r')

        #Correct the scale
        ax = plt.gca()
        ax.set_ylim([0,lt])
        ax.set_xlim([0,wt])
        
        #match Y axis with CMX 
        ax.set_ylim(ax.get_ylim()[::-1])
        ax.xaxis.tick_top()


        #SHow axis marking off
        plt.axis('off')
        

        #Save new image in memory
        plt.savefig(buff, format='png', dpi=500)
        plt.gcf().clear()

       
        #Get the new Image
        buff.seek(0)
        newmaptagged = base64.b64encode(buff.read())

        #Save Tagged img in disk
        _name = str(ipaddr) + '.png'
        file = self.PATH + _name
        fh = open(file,"wb")
        fh.write(base64.b64decode(newmaptagged))
        fh.close()

          
        return { "tagmap" : _name }

    def getClientsCount(self):
        url = "api/location/v2/clients/count"
        data = self.queryAPI(url)
        return data

    def getActiveClients(self): 
        url = "api/location/v2/clients"
        data = self.queryAPI(url)
        return data

    def getClientByMAC(self,macaddr):
        url = "api/location/v2/clients?macAddress=" + str(macaddr)
        data = self.queryAPI(url,False)
        return data

    def getClientByIP(self,ipaddr):
        url = "api/location/v2/clients?ipAddress=" + str(ipaddr)
        data = self.queryAPI(url,False)
        return data

    def getClientByUserName(self,username):
        url = "api/location/v2/clients?username=" + str(username)
        data = self.queryAPI(url,False)
        return data

    

#============ HIDDEN GEMS ==============#

class SportStats():

    def todayResults(self):
       games = []
       date = datetime.datetime.now().strftime("%Y%m%d")
       query_url= 'http://data.nba.net/data/10s/prod/v1/{0}/scoreboard.json'.format(date) 
       data = self.queryAPI(query_url)
      
       for game in data['games']:
          if game['statusNum'] == 3: #Game has finished
             hTeam,hConf = self.searchTeam(game['hTeam']['teamId'])
             hTeamScore = game['hTeam']['score']    
             vTeam,vConf = self.searchTeam(game['vTeam']['teamId'])
             vTeamScore = game['vTeam']['score']
               
       
             d = {'hTeam' : hTeam,
                  'vTeam' : vTeam,
                  'hScore' : hTeamScore,
                  'vScore' : vTeamScore
                 }
             games.append(d)
    
       return games


    def todayGames(self):
       games = []
       date = datetime.datetime.now().strftime("%Y%m%d")
       now = datetime.datetime.now()
       query_url= 'http://data.nba.net/data/10s/prod/v1/{0}/schedule.json'.format(str(now.year)) 
       data = self.queryAPI(query_url)
       
       for game in data['league']['standard']:
          if game['startDateEastern'] == date:
             hTeam,hConf = self.searchTeam(game['hTeam']['teamId'])    
             vTeam,vConf = self.searchTeam(game['vTeam']['teamId'])
             sTime = game['startTimeEastern']    
       
             d = {'hTeam' : hTeam,
                  'vTeam' : vTeam,
                  'sTime' : sTime
                 }
             games.append(d)
    
       return games

    def queryAPI(self,url):
       r = requests.get(url)
       result = r.text
       data = json.loads(result)
       
       return data



    def teamStanding(self):
       standings = []
       
       query_url = 'http://data.nba.net/10s/prod/v1/current/standings_all.json'
       data = self.queryAPI(query_url)

       for team in data['league']['standard']['teams']:
           teamName,teamConf = self.searchTeam(team['teamId'])
           ranking = team['confRank']
           teamWins = team['win']
           teamLost = team['loss'] 
            

           d = {'teamName' : teamName,
                'ranking' : ranking,
                'wins' : teamWins,
                'loss' : teamLost,
                'conf' : teamConf
                } 

           standings.append(d) 

       return standings

    def searchTeam(self,teamId):
       
       i = 0
       now = datetime.datetime.now()
       query_url = 'http://data.nba.net/data/10s/prod/v1/{0}/teams.json'.format(str(now.year))

       data = self.queryAPI(query_url)

       for team in data['league']['standard']:
           if team['teamId'] == teamId:
               name = team['fullName'] 
               conf = team['confName']
 
       return name,conf


class BitcoinEx():

    def __init__(self):
       return

    def getBTCRate(self):
       data = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
       return data

 
