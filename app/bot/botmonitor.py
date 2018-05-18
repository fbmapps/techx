import sys,os,re
from datetime import datetime
import logging
import requests


class botMonitorAPI:
    '''
    Prepare Data to show on Bot Dashboard Web Page
    '''

    def __init__(self):
        self.logfile = 'bot/clivebot.log'
        self.uriFile = 'bot/techxbot.py'
        self.ordersFile = 'bot/models.py'
        self.logger = logging.getLogger('cliveBot.MON')


    def prepareOrderList(self):
        OrderList = {} 
        orderKV = {}
        orderL = []
        
        try:
            with open(self.ordersFile) as f:
                for line in f:
                    if "n - **" in line:
                        regex = r"\bn - +\*+\*.*$"
                        match = line.strip()
                        order = ''.join(re.findall(regex,match))
                        command = order.split('** : ',1)[0]
                        #print(command[6:])
                        info = order.split(': ',1)[1]
                        #print(info)
                        orderKV = {"command" : command[6:],"info" :  info.strip()} 
                        orderL.append(orderKV)
    
            OrderList = {"botCommands" : orderL , "status_code" : 200}
            f.close()
            self.logger.info('Bot Command List extracted sucessfully. {} Commands registered'.format(str(len(orderL))))
        except Exception as e:
            OrderList = {"status_code" : 500}
            self.logger.error('Failed to create a Order list from file message:{}'.format(e))






        return OrderList


    def prepareURIList(self):
        '''Read techxBot.py File and build a list of endpoint'''

        URIList={}
        URL = [] 
        try:
            with open(self.uriFile) as f:
                for line in f:
                    if '/techx/' and '@post' in line:
                        regex = r"\btechx/.*"
                        uri = line.strip()
                        match = ''.join(re.findall(regex,uri))
                        match = match[:-2]
                        URL.append(match)
                        #print(match)
            URIList = {"endpoints" : URL, "status_code" : 200 }
            f.close()  
            self.logger.info('URI List extracted sucessfully. {} Endpoints attached'.format(len(URL))) 
        except Exception as e:
            URIList = {"status_code" : 200 } 
            self.logger.error('Failed to create URI List from file message:{}'.format(e))        
            
        

        return URIList


    def prepareCounters(self):               
        botCounters = {}
    


        return botCounters


    def CheckBackendServices(self):
        botHealth={}
        host = [] 
        hostKV = {}

        try:
            with open(self.ordersFile) as f:
                for line in f:
                    if'_UR' in line:
                        hst = line.strip()
                        check = hst.split("['",1)[1]
                        uri = os.environ[check[0:7]]
                        resp = requests.get(uri,verify=False)
                        if resp.status_code == 200 or resp.status_code == 401:
                            hostKV = {"botService" : check[0:3] , "botStatus" : True} 
                            host.append(hostKV)

            botHealth = {"backend": host,"status_code" : 200}
            f.close()
            self.logger.info('Backend Checked Sucessfully')
        except Exception as e:
            botHealth = {"status_code" :  500}       
            self.logger.error('Failed to check Backend status message: {}'.format(e))


        return botHealth 


#Testing
'''
mon = botMonitorAPI()
endp = {}
cmdp = {}
hlth = {}
endp = mon.prepareURIList()
cmdp = mon.prepareOrderList()
hlth = mon.CheckBackendServices()
print(endp)
print(cmdp)
print(hlth)
'''

