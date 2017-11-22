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



#Common Functions
def main():
   p = PrimeAPI()
   devs = p.getDevices()
   
   devices = []

   for dev in devs['queryResponse']['entity']:
      devName = dev['devicesDTO']['deviceName'] 
      devIPAdd = dev['devicesDTO']['ipAddress']
      devLocation = dev['devicesDTO']['location']
      devStatus = dev['devicesDTO']['reachability'] 

      if devStatus != 'REACHABLE':         

         d = {'devName' : devName,
              'ipAddress' : devIPAdd,
              'location' : devLocation,
              'status' : devStatus,
              'dateScan': str(datetime.datetime.now())
             }

         devices.append(d)
 

   return devices





#Main Program
if __name__ == "__main__":
    print(main())







