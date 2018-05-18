'''
TXWATCHGD: BOT TO LOOK OVER APIS AND GET STATUS
THIS SHALL RUN IN THE BACKGROUND AS A SERVICE

VERSION 0.1
CREATED BY FRBELLO AT CISCO DOT COM
DATE NOV 2017



Check every 5 minutes (300secs)
Dampen Notification to every 15 minutes (900secs)


	
'''
#Libraries
import sys,os,datetime,time
import requests
from models import *
from halo import Halo
from pyfiglet import Figlet


#===== Database ORM Libraries =======
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


#============= Disabling Insecure Warning================================#
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



#Common Functions
def DateDiff(dtNew, dtOld):
   diff = round((dtNew - dtOld).total_seconds())
   return diff


def print_banner():
    '''
    Print a Welcome Banner
    '''
    figlet = Figlet(font='slant')
    banner = figlet.renderText('CliveBot')
    print(banner)
    print("[+] 2018 Clive Bot PRIME Continuos Monitoring Tool  www.cisco.com\n")

def DataCollector(p,dbs):
   #REQUESTS ALL Prime Devices
   devs = p.getAllDevices()
   devices = [] 
   devCollected = devs['queryResponse']['@count']
     
   #Process the DataSet
   for dev in devs['queryResponse']['entity']:
      
      devURL = dev['@url']
      devName = dev['devicesDTO']['deviceName'] 
      devIPAdd = dev['devicesDTO']['ipAddress']
      devStatus = dev['devicesDTO']['reachability']
      devID = dev['devicesDTO']['@displayName']
      if 'location' not in dev['devicesDTO']:
         devLocation = ''
      else:
         devLocation = dev['devicesDTO']['location']
       
  
      #Check If device exist in database
      
      record = dbs.query(Notification).filter(Notification.devId == devID).first() 
      if record == None:      #The record doesn't exist in database
         #Process New Record
         sparkCounter = 0
         changeCounter = 0
         if devStatus == 'UNREACHABLE': 
            #Set Notification Active
            botNotify = True
         else:
            #Devices has a Normal status
            botNotify =  False
         
         #Insert the new record
         new_dev = Notification(devId = devID,
                                devName = devName,
                                ipAdd = devIPAdd,
                                url = devURL,
                                location = devLocation,
                                status = devStatus,
                                bot_notify_request = botNotify,
                                last_bot_notify = datetime.datetime.now(),
                                bot_notify_count = sparkCounter,
                                last_status_change = datetime.datetime.now(),
                                status_change_count = changeCounter,
                                record_created=datetime.datetime.now()
                               )
          
         dbs.add(new_dev)
         dbs.commit()
                     
 
                         
      else:     #The device record exist in Table
         #Update Existing Record
         if record.status != devStatus: #Status has changed
            record.status = devStatus
            record.status_change_count = record.status_change_count + 1
         if devStatus == 'UNREACHABLE':
            #LOGIC To Check if 5minutes passed to restart notify is needed here 
            diff = DateDiff(datetime.datetime.now(),record.last_bot_notify)
            if diff > 900: #Notify Window in secs = 15minutes
               record.bot_notify_request = True
               record.last_bot_notify = datetime.datetime.now()
               record.bot_notify_count = record.bot_notify_count + 1
            else:
               record.bot_notify_request = False
         else: #REACHABLE
            #TODO Notify if the Status Change
            record.bot_notify_request = False
         

         dbs.commit()
        
      






      d = {'devName' : devName,
           'ipAddress' : devIPAdd,
           'location' : devLocation,
           'status' : devStatus,
           'devId' : devID,
           'dateScan': str(datetime.datetime.now())
          }

      devices.append(d)






def SparkNotifier(dbs):
   records = dbs.query(Notification).filter(Notification.bot_notify_request==True)
  
   msg = ''
   bot_url = 'http://63.231.220.94:5105/techx/v1/note/'
   msg_header = '\n**Unreachable Device List**\n'
   msg_body = ''
   note = {}   
   url = 'https://www.shareicon.net/data/128x128/2016/08/18/815448_warning_512x512.png'
   headers = {"Accept" : "application/json",
              "Content-Type" : "application/json",
              "cache-control" : "no-cache"
             }    


   for record in records:
      msg_body = msg_body + """\n - Device: **{0}**  \nipAdd: **{1}**  \nlocation: **{2}**  \n[more...]({3})\n\n""".format(record.devName,record.ipAdd,record.location,record.url) 
      record.bot_notify_request = True

      dbs.commit()
   
   msg = msg_header + msg_body
   
   note['msg'] = msg
   note['file'] = url

   payload = json.dumps(note)
   
   r = requests.request('POST',bot_url,data=payload,headers=headers)


   
       



   return {'response' : r.status_code , 'data': msg}





def main():
   print_banner()
   p = PrimeAPI()
   spinner = Halo(spinner='dots')

   db = create_engine('sqlite:///techxdb.db')
   Base.metadata.create_all(db)
   Base.metadata.bind = db
   DBSession = sessionmaker(bind=db)

   dbs = DBSession()
   
   #Process Data
    
   spinner.start(text='Processing Data...')
   devices = DataCollector(p,dbs)
  
   time.sleep(5)
   spinner.succeed(text='Data Collected')

   #Send Message for bot Request = True
   spinner.start(text='Sending Notification...')
   response = SparkNotifier(dbs)     
   spinner.succeed(text='Notification sended')   


   spinner.succeed(text='Process Complete')    
   #return {"response" : "200 OK" }





#Main Program
if __name__ == "__main__":
    main()







