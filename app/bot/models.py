'''
MODELS FILES TO HANDLE CONNECTION WITH EXTERNAL SERVICES

'''





import requests
import json
import os, sys, time, datetime

class PrimeAPI():
    def checkStatus(self):
        return "class ok"

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


    def getDevices(self):
        url = "/webacs/api/v1/data/Devices.json?.full=true&.sort=ipAddress&reachability=UNREACHABLE"
        data = self.queryAPI(url)

        return data




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
       #query_url = 'http://data.nba.net/data/1h/prod/{0}/teams_config.json'.format(str(now.year))

       data = self.queryAPI(query_url)

       for team in data['league']['standard']:
           if team['teamId'] == teamId:
               name = team['fullName'] 
               conf = team['confName']
 
       return name,conf



