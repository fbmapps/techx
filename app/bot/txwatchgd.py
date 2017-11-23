'''
TXWATCHGD: BOT TO LOOK OVER APIS AND GET STATUS
THIS SHALL RUN IN THE BACKGROUND AS A SERVICE

VERSION 0.1
CREATED BY FRBELLO AT CISCO DOT COM
DATE NOV 2017
	
'''
#Libraries
import sys,os,datetime,time
import requests
from models import *

#===== Database ORM Libraries =======
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#db = create_engine('sqlite:///techxdb.db')
#Base.metadata.create_all(db)
#Base.metadata.bind = db
#DBSession = sessionmaker(bind=db)



#Common Functions
def DataCollector(p,dbs):
   
   #REQUESTS ALL Prime Devices
   devs = p.getAllDevices()
   devices = [] 
   
   devCollected = devs['queryResponse']['@count']
     
   #Process the DataSet
   #new_dev = Notification(devId='111',
   #                       devName='TestDev',
   #                       ipAdd='1.1.1.1',
   #                       location='MyLocation',
   #                       status='UNREACHABLE',
   #                       bot_notify_request=True,
   #                       last_bot_notify=datetime.datetime.now(),
   #                       bot_notify_count=0,
   #                       last_status_change=datetime.datetime.now(),
   #                       status_change_count=0,
   #                       record_created=datetime.datetime.now()
   #                      ) 
   #dbs.add(new_dev)
   #dbs.commit()
      

  
   for dev in devs['queryResponse']['entity']:




      devName = dev['devicesDTO']['deviceName'] 
      devIPAdd = dev['devicesDTO']['ipAddress']
      devLocation = dev['devicesDTO']['location']
      devStatus = dev['devicesDTO']['reachability']
      devID = dev['devicesDTO']['@displayName']
  
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
               record.bot_notify_request = True
            else:
               record.bot_notify_request = False
            dbs.commit()
         else:
             pass
      






      d = {'devName' : devName,
           'ipAddress' : devIPAdd,
           'location' : devLocation,
           'status' : devStatus,
           'devId' : devID,
           'dateScan': str(datetime.datetime.now())
          }

      devices.append(d)


   #Send the response as JSON Dictionary
   return {'this_set_has' : devCollected, 'collection' : devices}




def SparkNotifier():
   pass





def main():
   p = PrimeAPI()

   db = create_engine('sqlite:///techxdb.db', echo=True)
   Base.metadata.create_all(db)
   Base.metadata.bind = db
   DBSession = sessionmaker(bind=db)

   dbs = DBSession()

   devices = DataCollector(p,dbs)

   return devices['this_set_has']





#Main Program
if __name__ == "__main__":
    print(main())







