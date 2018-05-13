'''
MODELS FILES TO HANDLE CONNECTION WITH EXTERNAL SERVICES


VERSION : 1.0
STATUS  = BETA
DATE DEC 2017
REV MAY 2018

'''


import requests
import json
import os, sys, time, datetime
import xml.etree.ElementTree as ET

#===== Libraries for NetDevices Connectivity =====
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException

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
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#====== CiscoSparkAPI call ========================
from ciscosparkapi import CiscoSparkAPI


#============ ORM For Database CRUD Operations with SQLAlchemy =======
Base = declarative_base()
#db = create_engine('sqlite:///techxdb.db') 



__author__ = "Freddy Bello"
__author_email__ = "frbello@cisco.com"
__copyright__ = "Copyright (c) 2016-2018 Cisco and/or its affiliates."
__license__ = "MIT"



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
    
    def find(self,param):
        '''
        Migrated from CLIVE MEL
        '''
        url = "/webacs/api/v3/data/ClientDetails.json?{0}".format(param)
        links = []
        user_location = []
        
       
        response = self.queryAPI(url)
        if response['queryResponse']['@count'] == 0:
            return {"status_code" : 404}



        entities = response['queryResponse']['entityId']

        for each in entities:
            links.append(str(each['@url']).replace(self.apiURI,''))

        for link in links:
            url = link + '.json'
            response = self.queryAPI(url)
            client_connection_type = response['queryResponse']['entity'][0]['clientDetailsDTO']['connectionType']

            if client_connection_type.lower() == 'wired':
               client_interface = response['queryResponse']['entity'][0]['clientDetailsDTO']['clientInterface']
               device_ip_address = response['queryResponse']['entity'][0]["clientDetailsDTO"]["deviceIpAddress"]["address"]
               client_connection_device_name = response['queryResponse']['entity'][0]["clientDetailsDTO"]["deviceName"]
               client_device_type = response['queryResponse']['entity'][0]["clientDetailsDTO"]["deviceType"]
               client_ip = response['queryResponse']['entity'][0]["clientDetailsDTO"]["ipAddress"]['address']
               client_mac_address = response['queryResponse']['entity'][0]["clientDetailsDTO"]["macAddress"]
               client_current_status = response['queryResponse']['entity'][0]["clientDetailsDTO"]["status"]
               client_vlan_name = response['queryResponse']['entity'][0]["clientDetailsDTO"]["vlanName"]
               client_vlanid = response['queryResponse']['entity'][0]["clientDetailsDTO"]["vlan"]
               client_vendor = response['queryResponse']['entity'][0]["clientDetailsDTO"]["vendor"]

               msg = """\n  **{}** has a mac-address of **{}** 
                        \n - Is of type **{}** from **{}**. 
                        \n - It is connected to switch **{}** ({}) 
                        \n - on port **{}** 
                        \n - VLAN **{}** (**{}**).
                        \n - Current status is **{}**""".format(client_ip,
                                                                client_mac_address,
                                                                client_device_type, 
                                                                client_vendor,
                                                                client_connection_device_name,
                                                                device_ip_address,
                                                                client_interface,
                                                                client_vlan_name,
                                                                client_vlanid,
                                                                client_current_status)
               user_location.append(msg)
               mapw =[]
               #return {"clt_conn_type" : client_connection_type, "location" : user_location, "status_code" : 200,"map" : mapw}
            
            else:
               #Wireless Devices
               client_ap_name = response['queryResponse']['entity'][0]["clientDetailsDTO"]['apName']
               client_ap_ip = response['queryResponse']['entity'][0]["clientDetailsDTO"]['apIpAddress']['address']
               client_ip = response['queryResponse']['entity'][0]["clientDetailsDTO"]["ipAddress"]['address']
               client_protocol = response['queryResponse']['entity'][0]["clientDetailsDTO"]["protocol"]
               client_ssid = response['queryResponse']['entity'][0]["clientDetailsDTO"]["ssid"]
               client_current_status = response['queryResponse']['entity'][0]["clientDetailsDTO"]["status"]
               client_interface = response['queryResponse']['entity'][0]["clientDetailsDTO"]["clientInterface"]
               client_connection_device_name = response['queryResponse']['entity'][0]["clientDetailsDTO"]["deviceName"]
               client_device_type = response['queryResponse']['entity'][0]["clientDetailsDTO"]["deviceType"]
               client_mac_address = response['queryResponse']['entity'][0]["clientDetailsDTO"]["macAddress"]
               client_username = response['queryResponse']['entity'][0]["clientDetailsDTO"]["userName"]
               client_vendor = response['queryResponse']['entity'][0]["clientDetailsDTO"]["vendor"]
               client_vlanid = response['queryResponse']['entity'][0]["clientDetailsDTO"]["vlan"]

               msg = """\n  **{}** has a mac-address of {} 
                        \n - Is of type **{}** from **{}**. 
                        \n - It is connected to AP **{}** (**{}**) 
                        \n - on SSID **{}** 
                        \n - (VLAN **{}**). 
                        \n - Current status is **{}**""".format(client_ip,
                                                                client_mac_address,
                                                                client_device_type,
                                                                client_vendor,
                                                                client_ap_name,
                                                                client_ap_ip,
                                                                client_interface,
                                                                client_vlanid, 
                                                                client_current_status)
                 
               user_location.append(msg)
               mapw=[] 

                
        return {"clt_conn_type" : client_connection_type, "location" : user_location, "status_code" : 200, "map" : mapw}





class CnrAPI():
    ''' Access to DNS and DHCP Info '''
    def __init__(self):
        self.user = str(os.environ['CNR_USER'])
        self.passd = str(os.environ['CNR_PASW'])
        self.apiURI = str(os.environ['CNR_URI'])
        self.lookupKey = '01:06:'
        self.headers = {'accept': "application/json",'content-type': "application/json",'cache-control': "no-cache"}


    def queryAPI(self,url):
        apiurl = self.apiURI + url
        r = requests.get(apiurl,auth=(self.user,self.passd),verify=False)
        result = r.text
        return result
    
    def getDHCPStats(self):
        url = "stats/DHCPServer" 
        data = self.queryAPI(url)
        return data

    def getDNSStats(self):
        url = "stats/DNSCachingServer"
        data = self.queryAPI(url)
        return data 

    def getDHCPUse(self):
        url="stats/DHCPServer?nrClass=DHCPTopUtilizedStats"
        data = self.queryAPI(url)
        return data

    def post(self,url,payload):
        apiurl = self.apiURI + url
        try:

            r = requests.post(apiurl,headers=self.headers,auth=(self.user,self.passd),data=json.dumps(payload),verify=False)
            result = r.status_code
            data = result
        except ConnectionError as e:
            data = 500

        return data


    def reserveLease(self,ipaddr,mac):
        lookupKey = self.lookupKey + mac
        uri = 'resource/Reservation'
        payload = {"ipaddr" : ipaddr, "lookupKey" : lookupKey, "lookupKeyType":"9"}
        
        try:
            response = self.post(uri,payload)
            #if response == 201:
                #Sync with the ALternate CNR
                #url = "https://10.0.114.5:8443/web-services/rest/resource/CCMFailoverPair/Failover"
                #payload={"action" : "sync","mode" : "update","direction" : "fromMain"}
                #sync_response = requests.request("PUT", url=url, headers=self.headers, auth=(self.user ,self.passw), data=payload,verify=False)
        except ConnectionError as e:
            response = 500   
        
        return response

    def getLeaseInfo(self,ipaddr):
        '''Request Info about DHCP Lease for and IP Address
           uri = 'resource/Lease/'+ ipaddr
           returns Status Code
        '''
        data = {} 
        url = self.apiURI + 'resource/Lease/'+ipaddr
        try:
            response = requests.get(url,headers=self.headers,auth=(self.user,self.passd),verify=False)
            if response.status_code == 200:
                data = json.loads(response.text)
        except ConnectionError as e:
            data = {"error": e, "status_code" : 500}
        
        return data
        
    def deleteLease(self,ipaddr):
        '''Delete an Existing Lease


        '''
        url = self.apiURI+'resource/Reservation/'+ip
        try:
            response = requests.delete(url,headers=self.headers,auth=(self.user,self.passd),verify=False)
            data = response.status_code
        except ConnectionError as e:
            data = 500
                
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
        try:
            if content == True:
               data = r.content
            else:
               result = r.text
               data = json.loads(result)
        except ConnectionError as e:
            data =  False
        return data
    


    def getNowCount(self):
        url = 'api/analytics/v1/now/connectedDetected'
        data = self.queryAPI(url)
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

#============ DEVICE CONTROL ============#     

class SwitchPort():
    '''
    Set Vlan Configuration using NetMiko Library
    '''
    def __init__(self):
        self.user =  str(os.environ['NET_USER'])
        self.passd = str(os.environ['NET_PASW'])
        self.interface = ''
        self.ipaddr = ''
        global device
        global current_config
        

                
    def CheckConnectivity(self, ipaddr):
        response = os.system("ping -c 2 " + ipaddr)
        if response == 0:
            return {'message' : 'Connection Ok' , 'status' : 200}
        else:
            return {'message' : 'Connection Failed!' , 'status' : 500}

    def CheckInterfaceConfig(self,ipaddr,interface):
        device = {
            'device_type': 'cisco_ios',
            'ip': ipaddr,
            'username': self.user,
            'password': self.passd,
        }
        try:
            net_connect = ConnectHandler(**device)
            net_connect.find_prompt()
            output = str(net_connect.send_command("show run int gi {0}".format(interface)))
            if 'Invalid input detected' in output:
                output = str(net_connect.send_command("show run int te {0}".format(interface)))
                if 'Invalid input detected' in output:
                    status =  False
                    response = {'code' : 500 , 'message' : 'Invalid Input Detected' , 'status' : status} 
                    return response
                else:
                    self.interface = 'te' + interface
                    self.ipaddr = ipaddr 
                    status =  True
                    response = {'message' : output.strip().splitlines(),'code' : 200, 'status' : status }
                    return response
            else:
                self.interface = 'gi' + interface
                self.ipaddr = ipaddr
                status = True
                response = {'message' : output.strip().splitlines() , 'code' : 200, 'status' : status }
                return response
            net_connect.disconnect() 
        except ValueError:
                return {'code' : 500 , 'message' : ValueError, 'status' : False }

    def ChangeInterfaceConfig(self,vlan_name):
        config_commands = []
        vlan_id = {
            'trunk':'',
            'nocwired': '304',
	    'ciscotv' : '308',
	    'voice' : '312',
	    'registration' :  '316',
	    'sesscap' : '320',
	    'signage' : '332',
	    'camera' : '336',
	    'ap' : '340',
	    'speaker':'344',
	    'devnet':'348',
	    'wisp': '372',
	    'nocpublic': '751',
	    'regpublic': '752',
	    'occcpublic': '753',
	    'labspublic':'754',
	    'ciscotvpublic':'755',
	    'wospublic2':'756',
	    'wospublic':'757',
	    'hyattpublic':'758',        
	    'wos550' : '550',
            'wos551':	'551',
	    'wos552':	'552',
	    'wos553':	'553',
	    'wos554':	'554',
	    'wos555':	'555',
	    'wos556':	'556',
	    'wos557':	'557',
	    'wos558':	'558',
	    'wos559':	'559',
	    'wos560':	'560',
	    'wos561':	'561',
            'wos562':	'562',
	    'wos563':	'563',
	    'wos564':	'564',
	    'wos565':	'565',
	    'wos566':	'566',
            'wos570':  '570',
	    'wos571':	'571',
	    'wos572':	'572',
	    'wos573':	'573',
            'wos574':	'574',
	    'wos575':	'575',
	    'wos576':	'576',
	    'wos577':	'577',
	    'wos578':	'578',
	    'wos579':	'579',
	    'wos580':	'580',
	    'wos581':	'581',
	    'wos582':	'582',
	    'wos583':	'583',
	    'wos584':	'584',
	    'wos585':	'585',
	    'wos586':	'586'
       } 

        base_config = [
            'switchport',
            'switchport mode access',
            'switchport port-security maximum 10',
            'switchport port-security',
            'switchport port-security aging time 10',
            'load-interval 30',
            'ipv6 nd raguard',
            'ipv6 dhcp guard',
            'udld port aggressive',
            'storm-control broadcast level pps 100',
            'storm-control multicast level pps 2k',
            'spanning-tree link-type point-to-point',
            'spanning-tree guard root',
            'no shut'
        ]

        trunk_config = [
            'switchport',
            'switchp mode trunk',
            'switchp non',
            'load-interval 30',
            'udld port aggressive',
            'spanning-tree link-type point-to-point',
            'spanning-tree guard loop',
            'no shut'
        ]

        
        if vlan_name == 'trunk':
            config_commands = trunk_config
        else:
            config_commands = base_config
            config_commands.insert(2, 'switchport access vlan ' + vlan_id[vlan_name])

        config_commands.insert(0,'default int  '+ self.interface)
        config_commands.insert(1,'interface '+ self.interface) 

        results = self.ExecuteCommand(config_commands)

        return results   

    def ChangeInterfaceStatus(self):
        '''
        This action brings up a port
        '''
        config_commands = []
        base_config = [
            'no shut'
        ]
        config_commands = base_config
        config_commands.insert(0,'interface '+ self.interface) 
        results = self.ExecuteCommand(config_commands)
        return results  
            
    def ExecuteCommand(self,config_commands):
        '''
        Receive a Command Set and Execute it 
        '''

        device = {
            'device_type': 'cisco_ios',
            'ip': self.ipaddr,
            'username': self.user,
            'password': self.passd,
        }
        try: 
            net_connect = ConnectHandler(**device)
            time.sleep(0.5)
            net_connect.send_config_set(config_commands)
            int_config = str(net_connect.send_command("show run int {}".format(self.interface)))
            net_connect.disconnect()
            return {'status' : 200 , 'message' : int_config.strip().splitlines()}

        except ValueError:
            return {'message' : 'Configuration Unsucessfull', 'status': 500}  



    

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


class MacVendor():
    '''
    Returns Organization ID from a Mac Address
    '''

    def __init__(self):
        self.apiURL = "https://api.macvendors.com/"

    def getMacVendor(self,mac):
        '''
        Receive a MAC and returns the Organizations that own it
        '''   
        url = self.apiURL + mac
        data = requests.get(url,verify=False)
        return data.text
     
        


class MyInfoAPI:

    def __init__(self):
       return


    def aboutMe(self):

       data = {}

       data = {'cmx_user' : str(os.environ['CMX_USER']),
               'prime_user' : str(os.environ['PRM_USER']),
               'cnr_user' : str(os.environ['CNR_USER']),
               'my_email' : str(os.environ['BOT_EMAIL']),
               'prime_url' : str(os.environ['PRM_URL']),
               'cmx_url' : str(os.environ['CMX_URI']),
               'cnr_url' : str(os.environ['CNR_URI']) 
              } 

       return data



#================= BOT Class with all the Commands ============

class theBot:

    def __init__(self):

        self.pri = PrimeAPI()
        self.nba = SportStats()
        self.btc = BitcoinEx()
        self.cmx = CmxAPI()
        self.cnr = CnrAPI()
        self.inf = MyInfoAPI()
        self.svl = SwitchPort()
        self.clive =  CiscoSparkAPI(access_token='OTUwNWQzNGYtNjgwNi00OWE5LTlmNDAtMjZlMTA1ZTA2ZGU2NDlhZmMzNDYtMzI1')
        self.vendor = MacVendor()        

        #OTUwNWQzNGYtNjgwNi00OWE5LTlmNDAtMjZlMTA1ZTA2ZGU2NDlhZmMzNDYtMzI1

        
    def getOrders(self,personId='',order='help',roomId=''):
        '''
        Receive the intents of user and execute the actions associated to the intent
        Actions are Objects which API calls to respond back to bot

        '''
    
        in_message = order #Intent
        personId = personId #Requester
        roomId = roomId #WebexTeam asking services
        msg = ''
        url = ''

        #Feedback Message
        msg = 'Hi <@personId:{0}>, Please standby while I do that for you...'.format(personId)
        self.clive.messages.create(roomId,markdown=msg)

        if 'ruthere' in in_message or 'ready' in in_message:
           msg = "Yes <@personId:{0}>, I'm Here preparing myself to receive **orders** in the near future".format(personId)
           url = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1033931-200.png'
        elif 'nbarank' in in_message:
           stats = self.nba.teamStanding()
           east_ttl = "\n**East Conference:** \n"
           west_ttl = "\n**West Conference:** \n"
           east_msg = ''
           west_msg = ''
           for stat in stats:
               if stat['conf'] == 'East':
                  east_msg = east_msg + stat['ranking'] + ". **" + stat['teamName'] + "** W:**" + stat['wins'] + "** L: **" + stat['loss'] + "** \n"
               else:
                  west_msg = west_msg + stat['ranking'] + ". **" + stat['teamName'] + "** W:**" + stat['wins'] + "** L: **" + stat['loss'] + "** \n"
           msg = "**<@personId:{0}>  here is the latest NBA Ranking:** \n".format(personId) + east_ttl + east_msg + west_ttl + west_msg
           url = "http://media.nola.com/hornets_impact/photo/10295491-small.jpg"   
        elif 'nbagame' in in_message:
           today_gm = "\n**Games for Today**\n"
           today_match = '' 
           games = self.nba.todayGames()
           for game in games:
               today_match = today_match + "- **" + game['vTeam'] + "** AT **" + game['hTeam'] + "**  *" + game['sTime'] +"* \n"
           msg = today_gm + today_match
        elif 'nbaresult' in in_message:
           today_gm = "\n**Games Results for Today**\n"
           today_match = '' 
           games = self.nba.todayResults()
           for game in games:
               today_match = today_match + "- **" + game['vTeam'] + "** : **"+ game['vScore']  + "** AT **" + game['hTeam'] + "** :  **" + game['hScore'] +"** \n"
           msg = today_gm + today_match
        elif 'getbitcoin' in in_message:
           rate = self.btc.getBTCRate()
           msg = "The Current Price of Bitcoin is $**{0}**".format(str(rate.json()['bpi']['USD']['rate'])) 
        elif 'getprime' in in_message:
           devs = self.pri.getDevices()
           if int(devs['queryResponse']['@count']) == 0:
              msg = "**Everything looks Good <@personId:{0}>.  All devices appears to be reachables now!!**".format(personId)
              url = 'https://t6.rbxcdn.com/023c0a0a3aa7fb0629725f2ebe365f8f'
           else:
              msg = "It seems you need to go and Check!!! \n - **Right now we have {0} devices Unreachables!!**".format(str(devs['queryResponse']['@count']))
              url = "https://www.shareicon.net/data/128x128/2016/08/18/815448_warning_512x512.png"
        elif 'getxcount' in in_message:
           conx = self.cmx.getClientsCount()
           msg = "**We have *{0}* Active connections seen in CMX**".format(str(conx['count'])) 
        elif 'whereis' in in_message:
           query = in_message.split('whereis ',1)[1]
                      
           if query[0].isdigit() and query[1].isdigit():
              location = self.cmx.getClientByIP(query.strip())
           else:
              location = self.cmx.getClientByUserName(query.strip())           
        
           if not location:
               msg = "**{0}** not found in CMX".format(query)       
           else: 
               for record in location:
                   ipaddr = record['ipAddress'][0]
                   macaddr = record['macAddress']
                   ssid = record['ssId']
                   username = record['userName']
                   maps= record['mapInfo']['mapHierarchyString'].split('>')
                   building = maps[0]
                   level = maps[1]
                   floor = maps[2]
                   status = record['dot11Status']
                   img =  record['mapInfo']['image']['imageName']
                   x = record['mapCoordinate']['x']
                   y = record['mapCoordinate']['y']
                   lt= record['mapInfo']['floorDimension']['length']
                   wt= record['mapInfo']['floorDimension']['width']
                   resp=self.cmx.getMapImage(img,x,y,lt,wt,ipaddr)
                   maplk = "[see on map here...](https://bot.xmplelab.com/static/img/{0}{1})".format(str(ipaddr).strip(),'.png')
                   msg = """<@personId:{8}> This is what I've found:
                          \n-  **{7}** is **{5}** on the ssid **{2}** 
                          \n - Building **{3}** at **{4}** 
                          \n-  IP: {0} 
                          \n - username: **{1}**""".format(ipaddr,username,ssid,building,floor,status, maplk,query,personId)
                   url = ["/var/www/html/static/img/{0}{1}".format(str(ipaddr).strip(),'.png')]
                   self.clive.messages.create(roomId,markdown=msg,files=url)
                   msg = "**Job Done!!!**"
                   #url = "http://www.computerhistory.org/ciscoarchive/_media/img/chm-cisco-systems.jpg"
        elif 'getdhcp' in in_message:
           data = self.cnr.getDHCPStats()
           stats = ET.fromstring(data)
           uptime = stats[4].text.strip()
           dhcpdisc = stats[11].text.strip()
           dhcpoffer = stats[13].text.strip()
           dhcprel = stats[14].text.strip()
           dhcpreq = stats[15].text.strip()
           dhcpack = stats[9].text.strip()
           msg = """ Hi <@personId:{0}>. This are the stats for DHCP Server:
                     \n - Uptime        : **{1}**
                     \n - DHCP Request  : **{2}**
                     \n - DHCP Ack      : **{3}**
                     \n - DHCP Offer    : **{4}**
                     \n - DHCP Discover : **{5}**
                 """.format(personId,uptime,dhcpreq,dhcpack,dhcpoffer,dhcpdisc) 
        elif 'getdns' in in_message:
           data = self.cnr.getDNSStats()
           stats = ET.fromstring(data)
           msg = """ <@personId:{0}> Data is Loading... """.format(personId)
        elif 'getipuse' in in_message:
           data = self.cnr.getDHCPUse()
           ns = { "cnr" : "http://ws.cnr.cisco.com/xsd" } 
           root = ET.fromstring(data)
           msg = 'Hi <@personId:{0}>. Here is a summary of DHCP Scope usage: \n'.format(personId)
           
           for item in root.findall('cnr:list',ns):
               for element in item.findall('cnr:DHCPScopeAggregationStatsItem',ns):
                  name = element.find('cnr:name',ns)
                  inUse = element.find('cnr:inUseAddresses',ns)
                  usage = element.find('cnr:utilizedPct',ns)
                  total = element.find('cnr:totalAddresses',ns)
                  available =  int(total.text) - int(inUse.text)
                  msg = msg + """\n - Scope : *{0} is at {1}. IPs used : {2} IP in scope {3} Availables :**{4}** """.format(name.text,
                                                                                                                             usage.text,
                                                                                                                             inUse.text,
                                                                                                                             total.text,
                                                                                                                             str(available))
        elif 'changevlan' in in_message:
            #Data Parsing
            ip = ''.join(re.findall('\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}',in_message))
            interface1 = ''.join(re.findall(r'\w{1,3}/\w{1,3}/\w{1,3}',in_message))
            interface2=  ''.join(re.findall(r'\w{1,3}/\w{1,3}',in_message))
            if not interface1:
                interface = interface2
            else: 
                interface = interface1
            vlan = ''.join(re.findall(r'\bnocwired\b|\bciscotv\b|\bvoice\b|\bregistration\b|\bsesscap\b|\bsignage\b|\bcamera\b|\bap\b|\bspeaker\b|\bdevnet\b|\bwisps\b|\bnocpublic\b|\bregpublic\b|\bocccpublic\b|\blabspublic\b|\bciscotvpublic\b|\bhyattpublic\b|\bwos\w{1,7}\b',in_message))
            device_status = self.svl.CheckConnectivity(ip)
            ifc_check = self.svl.CheckInterfaceConfig(ip,interface)
            #config = '\n**********Current Config**********\n\n' + current_config['message']
            if device_status['status'] == 200 and ifc_check['status'] is True:
                final_config = self.svl.ChangeInterfaceConfig(vlan)
                msg = '\n**********Final Config**********\n\n'
                conf = '```' #MarkDown for Code Format
                for line in final_config['message']:
                    conf = conf + ' ' + line + '\n'
                msg = msg + conf + '```'  
            else:
                msg = current_config['message']

        elif 'noshut' in in_message:
            #Data Parsing
            ip = ''.join(re.findall('\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}',in_message))
            interface = ''.join(re.findall(r'\w{1,3}/\w{1,3}/\w{1,3}',in_message))
            device_status = self.svl.CheckConnectivity(ip)
            ifc_check = self.svl.CheckInterfaceConfig(ip,interface)
            if device_status['status'] == 200 and ifc_check['status'] is True:
                final_config = self.svl.ChangeInterfaceStatus()
                msg = '\n**********Final Config**********\n\n'
                conf = '```' #MarkDown for Code Format
                for line in final_config['message']:
                    conf = conf + ' ' + line + '\n'
                msg = msg + conf + '```'
       
            else:
                msg = ifc_check['message']           
        

        elif 'showint' in in_message:
            #Data Parsing
            ip = ''.join(re.findall('\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}',in_message))
            interface = ''.join(re.findall(r'\w{1,3}/\w{1,3}/\w{1,3}',in_message))
            device_status = self.svl.CheckConnectivity(ip)
            ifc_check = self.svl.CheckInterfaceConfig(ip,interface)
            if device_status['status'] == 200 and ifc_check['status'] is True:
                msg = '\n********** Current Config **********\n\n'
                conf = '```'
                for line in ifc_check['message']:
                    conf = conf + ' ' + line + '\n'
                msg = msg + conf + '```'

            else:
                msg = ifc_check['message']
       
        elif 'find' in in_message:
            #Data Parser
            query = in_message.split('find ',)[1]
            ip = ''.join(re.findall('\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}',in_message))
            mac = ''.join(re.findall(r'(?:[0-9|a-f|A-F]:?){12}',in_message))
            if not mac and not ip:
               #Trying to find a User
               user = query.strip()
               param = 'userName={0}'.format(user)
            elif not mac:
               #Trying to find by IP Address
               param = 'ipAddress={0}'.format(ip)
            else:
               #Trying to find by MAC Address
               param = 'macAddress="{0}"'.format(str(mac))

            #print(param)
            result = self.pri.find(param)
            if result['status_code']==404:
               msg = '**{0}** Not Found'.format(query.strip())
               self.clive.messages.create(roomId,markdown=msg)
            else:
               dev_type = result['clt_conn_type']
               data = result['location']
               if dev_type.lower()=='wired':
                  for each in data:
                     msg = data[0]
                     self.clive.messages.create(roomId,markdown=msg)
               else:
                  #Wireles
                  for each in data:
                     msg = data[0]
                     self.clive.messages.create(roomId,markdown=msg)
            
            msg = '**Job Done!!!**'
        
       
        elif 'reserve' in in_message:
            #Data Parser
            ip = ''.join(re.findall('\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}',in_message))
            mac = ''.join(re.findall(r'(?:[0-9|a-f|A-F]:?){12}',in_message))
            
            #Case 1: A new Lease Reserve for unasigned IP
            #Must provide both IP and Mac
            if mac != '' and ip != '':
                vendor = self.vendor.getMacVendor(mac)
                msg = "A **new** lease reservation will be created for mac {0}. It seems a device from {2}  . The IP **{1}** will be reserved for this host".format(mac,ip,vendor)
                self.clive.messages.create(roomId,markdown=msg)
                response = self.cnr.reserveLease(ip,mac)
                if response == 201:
                    msg = "A lease reservation was created for mac **{0}** from {2}. The IP **{1}** is reserved now for that mac!".format(mac,ip,vendor)                 
                else:
                    msg = "A lease reservation for mac **{0}** fails. The IP **{1}** is not reserved, please check your info and try again".format(mac,ip) 
                self.clive.messages.create(roomId,markdown=msg) 
                    
            #Case 2: An IP is assigned by DHCP but user wants it reserved for that host
            #must provide IP
            elif not mac and ip !='':
                msg = """
                      \nFirst thing first: let me ask CPNR to check if this lease already exists,then this lease reservation with the IP **{0}** will be assigned and reserved for the host with it\n\n""".format(ip)
                self.clive.messages.create(roomId,markdown=msg)
                check_lease = self.cnr.getLeaseInfo(ip)
                mac = check_lease['clientBinaryClientId']
                mac = mac[3:]
                vendor = self.vendor.getMacVendor(mac)
                response = self.cnr.reserveLease(ip,mac)
                if response == 201:
                    msg = "A lease reservation was created for mac **{0}** (it looks like as a device from **{2}**). The IP **{1}** is reserved now for that mac!".format(mac,ip,vendor)                 
                else:
                    msg = "A lease reservation for mac **{0}** fails. It looks like as a device from **{2}**. The IP **{1}** is not reserved, please check your info and try again".format(mac,ip,vendor)
                self.clive.messages.create(roomId,markdown=msg)  
                
            
            #Case 3: No parameter has been submitted
            else:

                msg = "There is no info to execute this task. Please use the format **reserve ip mac**"
                self.clive.messages.create(roomId,markdown=msg)

            msg = '**Task Complete!!!**'

 
   



                           

        elif 'showsvc' in in_message:
           about = self.inf.aboutMe()
           msg = ''' Hi <@personId:{0}>. This is a summary of the services an user id I'm using to connect \n'''.format(personId) 
           msg = msg + ''' 
                 \n - PRIME : UID **{0}** | API URI : **{1}**
                 \n - CMX :   UID **{2}** | API URI : **{3}**
                 \n - CNR :   UID **{4}** | API URI : **{5}**
                
  
           '''.format(about['prime_user'],
                      about['prime_url'],
                      about['cmx_user'],
                      about['cmx_url'],
                      about['cnr_user'],
                      about['cnr_url'])  



        elif 'getcmxcount' in in_message:
           
           result = self.cmx.getNowCount()
           msg = '''
                 This is the CMX Count snapshot
                 \n - Total Connected : **{0}**
                 \n - Total Detected : **{1}**'''.format(str(result['total']['totalConnected']),str(result['total']['totalDetected']))
 
      
        elif 'help' in in_message:
           msg = '''
                 Hi <@personId:{0}>,  I'm a API helper. I'll look up info on PRIME, CMX, and any other location where my builders connect me at. To help you just call my name @clive follow by any of this:\n
                 \n - **getprime** : I'll give you the count of Reachables and Unreachables Devices 
                 \n - **getcmxcount** : I'll show you the Actives connection from CMX
                 \n - **whereis x.x.x.x or whereis username** : I'll contact CMX to see where this client is, and I will send you a link with a marked floorplan displaying the location
                 \n - **getdhcp** : I'll contact CNR API to see Stats info of DHCPServer
                 \n - **getipuse** : Top stats of DHCP Scopes in use
                 \n - **changevlan switch_ip port vlan name** :  Change Vlan Configuration
                 \n - **noshut switch_ip port** :  Brings Switch Port UP 
                 \n - **showint switch_ip port** : Shows Interface Configuration 
                 \n - **showsvc** :  Info About Me and the services I'm using
                 \n - **find x.x.x.x | mac_address | username** : get info from PRIME
                 \n - **reserve x.x.x.x | mac_address ** : Manage DHCP Lease Reservations
                 \n - **help** : to see this message
                 \n - **and more...**
                  
                 '''.format(personId)
        
        else: #CATCH ALL SWITCH
           msg = "I do not understand the request. **Ask later!!**"
           url = "https://s-media-cache-ak0.pinimg.com/originals/09/37/fd/0937fd67d480736fa7a623944bd89f4b.jpg"    
        
        #Send Response to caller
        return { "msg" : msg , "files" : url }

    def SparkGET(self,url,headers):
        '''
        This will hear any message posted at the webhook
        '''

        r = requests.request("GET",url,headers=headers)
        content = r.text
        return content

    def SparkPOST(self,url,payload,headers):
        '''
        This Function send messages to spark room where the bot is invoked
        '''

        content = requests.request("POST",url,data=payload,headers=headers)
        return content
