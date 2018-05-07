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


class CnrAPI():
    ''' Access to DNS and DHCP Info '''
    def __init__(self):
        self.user = str(os.environ['CNR_USER'])
        self.passd = str(os.environ['CNR_PASW'])
        self.apiURI = str(os.environ['CNR_URI'])

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

    def ChangeInterfaceConfig(self,ipaddr,vlan_name):
        config_commands = []
        vlan_id = {
            'guest-wired':'980',
            'noc-wired':'941',
            'cisco-tv':'942',
            'phones':'943',
            'reg':'944',
            'session-record':'945',
            'staff-wired':'946',
            'signage':'948',
            'camera':'949',
            'ap':'950',
            'testing_center':'952',
            'devnet':'953',
            'wisp':'954',
            'printer':'959',
            'trunk':''
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

        
    def getOrders(self,personId='',order='help'):
        '''
        Receive the intents of user and execute the actions associated to the intent
        Actions are Objects which API calls to respond back to bot

        '''
    
        in_message = order #Intent
        personId = personId
        msg = ''
        url = ''

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
        elif 'getcmxcount' in in_message:
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
                          \n - username: **{1}** \n - {6}""".format(ipaddr,username,ssid,building,floor,status, maplk,query,personId)
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
            vlan = ''.join(re.findall(r'\bguest-wired\b|\bnoc-wired\b|\bcisco-tv\b|\bphones\b|\breg\b|\bsession-record\b|\bstaff-wired\b|\bsignage\b|\bcamera\b|\bap\b|\bdevnet\b|\bwisp\b|\bwos\b|\btesting_center\b|\bprinter\b|\btrunk\b',msg))
            device_status = self.svl.CheckConnectivity(ip)
            interface_status,current_config = self.svl.CheckInterfaceConfig(ip,interface)
            config = '\n**********Current Config**********\n\n' + current_config['message']
            if device_status['status'] == 200 and interface_status is True:
                final_config = self.svl.ChangeInterfaceConfig(ip,interface,vlan)
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
        elif 'help' in in_message:
           msg = '''
                 Hi <@personId:{0}>,  I'm a API helper. I'll look up info on PRIME, CMX, and any other location where my builders connect me at. To help you just call my name @techx.bot follow by any of this:\n
                 \n - **getprime** : I'll give you the count of Reachables and Unreachables Devices 
                 \n - **getcmxcount** : I'll show you the Actives connection from CMX
                 \n - **whereis x.x.x.x or whereis username** : I'll contact CMX to see where this client is, and I will send you a link with a marked floorplan displaying the location
                 \n - **getdhcp** : I'll contact CNR API to see Stats info of DHCPServer
                 \n - **getipuse** : Top stats of DHCP Scopes in use
                 \n - **changevlan switch_ip port vlan name** :  Change Vlan Configuration
                 \n - **noshut switch_ip port** :  Brings Switch Port UP 
                 \n - **showint switch_ip port** : Shows Interface Configuration 
                 \n - **showsvc** :  Info About Me and the services I'm using
                 \n - **help** : to see this message
                 \n - **and more...**
                  
                 '''.format(personId)
        
        else: #CATCH ALL SWITCH
           msg = "I do not understand the request. **Ask later!!**"
           url = "https://s-media-cache-ak0.pinimg.com/originals/09/37/fd/0937fd67d480736fa7a623944bd89f4b.jpg"    
        
        #Send Response to caller
        return { "msg" : msg , "file" : url }

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
