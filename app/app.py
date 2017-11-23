'''
TECHX BOT APPLICATION SERVER
CREATED BY: FRBELLO AT CISCO DOT COM
DATE : NOV 2017
VERSION: 0.1
STATE: ALPHA

Main Application Server to run a Socket in port 5105. 
This is the connecting point to invoke techxbot functionality

This in Python 3.6.4
micro framework is bottle

'''

#Libraries
import bottle
from bottle import route,run
import os, sys
from bot import techxbot


#Functions (IF ANY)


#Main program
if __name__ == '__main__':
    port = int(os.environ.get('PORT',5105))
    run(host='0.0.0.0',port=port,debug=True,reloader=True)

#FOR GUNICORN
app = bottle.default_app()

