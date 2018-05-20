'''
TECHX BOT APPLICATION SERVER
CREATED BY: FRBELLO AT CISCO DOT COM
DATE : MAY 2018
VERSION: 0.2
STATE: RC2

Main Application Server to run a Socket in port 5105. 
This is the connecting point to invoke techxbot functionality

This in Python 3.6.5
micro framework is flask

'''

#Libraries
#========= Microframework import =======
from flask import Flask
from bot.techxbot import app
#========= Standard library ============
import os, sys
from bot import techxbot
from pyfiglet import Figlet
from halo import Halo
import logging


__author__ = "Freddy Bello"
__author_email__ = "frbello@cisco.com"
__copyright__ = "Copyright (c) 2016-2018 Cisco and/or its affiliates."
__license__ = "MIT"


logger = logging.getLogger('cliveBot.MAIN') 

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
    #logger = logging.getLogger('cliveBot.MAIN')
    try:
        spinner.start(text='Bot Server is starting')
        spinner.succeed(text='Bot Server is running')
        port = int(os.environ.get('PORT',5105))
        logger.info('Bot Server started Sucessfully!!')
        app.run(host='0.0.0.0',port=port,debug=True)
        logger.info('Bot Server Stop')
    except Exception as e:
        spinner.fail(text='Bot Server fails')
        logger.error("Error Starting the bot Server: {}".format(e))
        exit(1)
