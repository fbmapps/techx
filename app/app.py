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
from pyfiglet import Figlet
from halo import Halo

__author__ = "Freddy Bello"
__author_email__ = "frbello@cisco.com"
__copyright__ = "Copyright (c) 2016-2018 Cisco and/or its affiliates."
__license__ = "MIT"



#Functions (IF ANY)
def print_banner():
    '''
    Print a Welcome Banner


    '''
    figlet = Figlet(font='slant')
    banner = figlet.renderText('CliveBot')
    print(banner)
    print("[+] 2018 Clive Bot  www.cisco.com\n")




#Main program
if __name__ == '__main__':
    print_banner()
    spinner = Halo(spinner='dots')
    try:
        spinner.start(text='Bot Server is starting')
        spinner.succeed(text='Bot Server is running')
        port = int(os.environ.get('PORT',5105))
        run(host='0.0.0.0',port=port,debug=True,reloader=True)
        #spinner.succeed(text='Bot Server is running')
    except Exception as e:
        spinner.fail(text='Bot Server fails')
        print("\n\nError Starting the bot Server: {}\n".format(e))
        exit(1)

#FOR GUNICORN
app = bottle.default_app()

