'''
Alexa Request Server
For CLIVE


Built in in flask
'''
from flask import Flask
from flask_ask import Ask, statement, question, session
import json
import requests
import time
import unidecode

app = Flask(__name__)
ask = Ask(app,"/clive_reader")


def get_clive_info():
    pass

@app.route('/')
def homepage():
    return "hi there, how you doin"


if __name__ == "__main__":
    app.run(debug=True,port=8443)




