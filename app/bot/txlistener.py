#Coded for Python 3.6
'''
This LISTEN to NOTIFICATIONS Sended to a socket from external suscriptor 
parse the json format

Version 0.1

'''

import sys
import socket
import json


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('0.0.0.0' , 8999)
sock.bind(server_address)

print (sys.stderr,'using %s port %s' % sock.getsockname())
sock.listen(1)

while True:
   print (sys.stderr, 'waiting for a connection')
   connection, client_address = sock.accept()
   
   try:
       data = connection.recv(2048)
       print(sys.stderr, 'received "%s"' % data)
       if data:
          connection.sendall(data)
       else:  
          break
   except (KeyboardInterrupt, SystemExit):
       raise
   finally:
       connection.close()


