# zap2epg tv schedule grabber for kodi
################################################################################
#   This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import urllib.request, urllib.error, urllib.parse
import base64
import codecs
import time
import datetime
#import _strptime
import calendar
import gzip
import os
import logging
import re
import json
#import sys
#from os.path import dirname
import xml.etree.ElementTree as ET
from collections import OrderedDict
#import hashlib
import html

try:
    import langid       #Determine if the langid module has been installed and set a flag if it has been.
    from langid.langid import LanguageIdentifier, model
    LanguageID = LanguageIdentifier.from_modelstring(model, norm_probs=True)
    useLangid = True    #Used in the parse episodes function
except:
    useLangid = False

def mainRun(userdata):
    settingsFile = os.path.join(userdata, 'settings.xml')
    settings = ET.parse(settingsFile)
    root = settings.getroot()
    settingsDict = {}
    xdescOrderDict = {}
    kodiVersion = root.attrib.get('version')
    logging.info('Kodi settings version is: %s', kodiVersion)
    for setting in root.findall('setting'):
        if kodiVersion == '2':
            settingStr = setting.text
        else:
            settingStr = setting.get('value')
            if settingStr == '':
                settingStr = None
        settingID = setting.get('id')
        settingsDict[settingID] = settingStr

        #Setup default values in case the settings XML does not have everything.
        stationList = ""
        zipcode = ""
        lineup="lineup"  
        device = ""
        days = 1
        redays = 0
        xdetails = False
        xdesc = False
        epicon = 0
        epgenre = 0
        tvhoff = False
        tvhurl = "127.0.0.1"
        tvhport = "9981"
        usern = ""
        passw = ""
        chmatch = False
        tvhmatch = False
        safetitle = False
        safeepisode = False
        escapeChar = "_"
        userLangid = False
        useLang = False
        useHex = False
       # xdescOrderDict = []

    for setting in settingsDict:
        if setting == 'slist':                              #station list from zap2it website i.e. 100105
            stationList = settingsDict[setting]
        if setting == 'zipcode':                            #zipcode
            zipcode = settingsDict[setting]
        if setting == 'lineup':                             #Type of lineup to receive from the given zipcode. i.e. cable or OTA
            lineup = settingsDict[setting]
        if setting == 'lineupcode':                         #Lineup Code [string default==lineupid]
            lineupcode = settingsDict[setting]
        if setting == 'device':                             #Device name to be sent to zap2it website
            device = settingsDict[setting]
        if setting == 'days':                               #Number of days to download data (1 to 14)
            days = settingsDict[setting]
        if setting == 'redays':                             #Number of Days to Delete Cache (re-download) for TBA listings (1 to 7)
            redays = settingsDict[setting]
        if setting == 'xdetails':                           #Add extra details from shows and movie listing
            xdetails = settingsDict[setting]
        if setting == 'xdesc':                              #Append Extra Details to Description
            xdesc = settingsDict[setting]
        if setting == 'epicon':                             #Include Episode Thumbnail  [0: None, 1: Series Image, 2: Episode Image]
            epicon = settingsDict[setting]
        if setting == 'epgenre':                            #Include Episode Genres (colored EPG grid) [0: None, 1: Simple, 2: Full, 3: Original]
            epgenre = settingsDict[setting]
        if setting == 'tvhoff':                             #Tvheadend Options Enabled [True, False]
            tvhoff = settingsDict[setting]
        if setting == 'tvhurl':                             #TV Headend URL  [http://]
            tvhurl = settingsDict[setting]
        if setting == 'tvhport':                            #TV Headend Port [9981]
            tvhport = settingsDict[setting]
        if setting == 'usern':                              #TV Headend Username (string)
            usern = settingsDict[setting]
        if setting == 'passw':                              #TV Headend password (string)
            passw = settingsDict[setting]
        if setting == 'chmatch':                            #Append Subchannel Number for OTA" [True, False]
            chmatch = settingsDict[setting]
        if setting == 'tvhmatch':                           #Append Tvheadend Service Name [True, False]
            tvhmatch = settingsDict[setting]
        if setting == 'safetitle':                          #Remove unsafe Windows characters from Show Titles [True, False]
            safetitle = settingsDict[setting]
        if setting == 'safeepisode':                        #Remove unsafe Windows characters from Episode Titles [True, False]
            safeepisode = settingsDict[setting]
        if setting == 'escapechar':                         #Replace unsafe characters with: [string]
            escapeChar =  settingsDict[setting]
            if escapeChar is None: escapeChar = '_'
        if setting == 'langid':                             #Use module LangID to identify language based on the description field [True, False]
            userLangid = settingsDict[setting]
            userLangid = {'1': 'en', '2': 'es', '3': 'fr'}.get(userLangid)
            if userLangid is None: userLangid = 'en'
        if setting == 'useLang':                            #Language to use if LangID is not used or can't determine language [em, es, fr, de, etc...]
            useLang = settingsDict[setting] 
        if setting == 'useHex':                             #0: Returns a string respresentation of the genre text    1: Returns a hex value for the genre
            useHex = 1 if settingsDict[setting] == 'true' else 0
        if setting.startswith('desc'):                      #The array of options for extra details desc01 thru desc20
            xdescOrderDict[setting] = (settingsDict[setting])
    xdescOrder = [value for (key, value) in sorted(xdescOrderDict.items())]
    if lineupcode != 'lineupId':
        chmatch = 'false'
        tvhmatch = 'false'
    if zipcode.isdigit():
        country = 'USA'
    else:
        country = 'CAN'
    logging.info('Running zap2epg-2.1.0 for zipcode: %s and lineup: %s', zipcode, lineup)
    logging.info(f'langid installed: {useLangid}')
    pythonStartTime = time.time()
    cacheDir = os.path.join(userdata, 'cache')
    dayHours = int(days) * 8 # set back to 8 when done testing
    gridtimeStart = (int(time.mktime(time.strptime(str(datetime.datetime.now().replace(microsecond=0,second=0,minute=0)), '%Y-%m-%d %H:%M:%S'))))
    schedule = {}
    tvhMatchDict = {}

    def getLang(desc: str, show: str, title: str) -> str:
        text = ""
        if desc is not None:            #Concatenate show, title and description into one string to send to the langudage detection module
            text = text + " " + desc
        if show is not None:
            text = text + " " + show
        if title is not None:
            text = text + " " + title        
        try:
            if useLangid and useLang and text is not None:  #Is the language module installed and did the user want to use it
                result = LanguageID.classify(text)
                if result[0] in (['en', 'es', 'fr']) and result[1] > .998:       #USA and Canada only broadcast in English, Spanish and French
                    return result[0]
                else:
                    return userLangid       #If the language module returns a random language, return the default language
            else:
                return userLangid # should be the default selected by the user
        except:
                return userLangid   #If there is an error, return the default language

    def tvhMatchGet():
        tvhUrlBase = 'http://' + tvhurl + ":" + tvhport
        channels_url = tvhUrlBase + '/api/channel/grid?all=1&limit=999999999&sort=name&filter=[{"type":"boolean","value":true,"field":"enabled"}]'
        if usern is not None and passw is not None:
            logging.info('Adding Tvheadend username and password to request url...')
            request = urllib.request.Request(channels_url)
            userpass = (usern + ':' + passw)
            userpass_enc = base64.b64encode(userpass.encode('utf-8'))
            request.add_header('Authorization', b'Basic ' + userpass_enc)
            response = urllib.request.urlopen(request)
        else:
            response = urllib.request.urlopen(channels_url)
        try:
            logging.info('Accessing Tvheadend channel list from: %s', tvhUrlBase)
            channels = json.load(response)
            for ch in channels['entries']:
                channelName = ch['name']
                channelNum = ch['number']
                tvhMatchDict[channelNum] = channelName
            logging.info('%s Tvheadend channels found...', str(len(tvhMatchDict)))
        except urllib.error.HTTPError as e:
            logging.exception('Exception: tvhMatch - %s', e.strerror)
            pass

    def deleteOldCache(gridtimeStart):
        logging.info('Checking for old cache files...')
        try:
            if os.path.exists(cacheDir):
                entries = os.listdir(cacheDir)
                for entry in entries:
                    oldfile = entry.split('.')[0]
                    if oldfile.isdigit():
                        fn = os.path.join(cacheDir, entry)
                        if (int(oldfile)) < (gridtimeStart + (int(redays) * 86400)):
                            try:
                                os.remove(fn)
                                logging.info('Deleting old cache: %s', entry)
                            except OSError as e:
                                logging.warning('Error Deleting: %s - %s.' % (e.filename, e.strerror))
        except Exception as e:
            logging.exception('Exception: deleteOldCache - %s', e.strerror)

    def deleteOldShowCache(showList):
        logging.info('Checking for old show cache files...')
        try:
            if os.path.exists(cacheDir):
                entries = os.listdir(cacheDir)
                for entry in entries:
                    oldfile = entry.split('.')[0]
                    if not oldfile.isdigit():
                        fn = os.path.join(cacheDir, entry)
                        if oldfile not in showList:
                            try:
                                os.remove(fn)
                                logging.info('Deleting old show cache: %s', entry)
                            except OSError as e:
                                logging.warning('Error Deleting: %s - %s.' % (e.filename, e.strerror))
        except Exception as e:
            logging.exception('Exception: deleteOldshowCache - %s', e.strerror)

    def convTime(t):
        return time.strftime("%Y%m%d%H%M%S",time.localtime(int(t)))

    def savepage(fn, data):
        if not os.path.exists(cacheDir):
            os.mkdir(cacheDir)
        fileDir = os.path.join(cacheDir, fn)
        with gzip.open(fileDir,"wb+") as f:
            f.write(data)
            f.close()

    def genreSort(EPfilter, EPgenre, edict):
        genreList = []
        updatedgenreList = []

        if epgenre == '1':          #User selected 'Simple'
            for g in EPgenre:
                if g != "Comedy":
                    genreList.append(g)
            if not set(['movie', 'Movie','Movies','movies']).isdisjoint(genreList):
                genreList.insert(0, "Movie / Drama")
            if not set(['News']).isdisjoint(genreList):
                genreList.insert(0, "News / Current affairs")
            if not set(['Game show']).isdisjoint(genreList):
                genreList.insert(0, "Game show / Quiz / Contest")
            if not set(['Law']).isdisjoint(genreList):
                genreList.insert(0, "Show / Game show")
            if not set(['Art','Culture']).isdisjoint(genreList):
                genreList.insert(0, "Arts / Culture (without music)")
            if not set(['Entertainment']).isdisjoint(genreList):
                genreList.insert(0, "Popular culture / Traditional Arts")
            if not set(['Politics', 'Social', 'Public affairs']).isdisjoint(genreList):
                genreList.insert(0, "Social / Political issues / Economics")
            if not set(['Education', 'Science']).isdisjoint(genreList):
                genreList.insert(0, "Education / Science / Factual topics")
            if not set(['How-to']).isdisjoint(genreList):
                genreList.insert(0, "Leisure hobbies")
            if not set(['Travel']).isdisjoint(genreList):
                genreList.insert(0, "Tourism / Travel")
            if not set(['Sitcom']).isdisjoint(genreList):
                genreList.insert(0, "Variety show")
            if not set(['Talk']).isdisjoint(genreList):
                genreList.insert(0, "Talk show")
            if not set(['Children']).isdisjoint(genreList):
                genreList.insert(0, "Children's / Youth programs")
            if not set(['Animated']).isdisjoint(genreList):
                genreList.insert(0, "Cartoons / Puppets")
            if not set(['Music']).isdisjoint(genreList):
                genreList.insert(0, "Music / Ballet / Dance")

            return genreList

        if epgenre == '2':          #User selected 'FULL' epg
            
            for g in EPgenre:
                genreList.append(g)

            #make each element lowercase, romve all spaces and any 's' at the end   
            genreList = list(map(lambda x: x.lower().replace(" ", ""), genreList))
            if (len(genreList) > 0 and genreList[0] != ''):
                genreList = list(map(lambda x: x[0:-1] if x[-1] == 's' else x, genreList))
            desc = f'{edict["epdesc"]} {edict["eptitle"]} {edict["epshow"]} {edict["epdesc"]}' 
            desc = desc.lower()

            #Movies   
            # TVHeadend Docs: https://github.com/tvheadend/tvheadend/blob/master/src/epg.c#L1775 line 1775    
            # Kodi Docs: https://github.com/xbmc/xbmc/blob/cda8e8c37190881fab4ea972d0d17cb54d5618d8/xbmc/addons/kodi-dev-kit/include/kodi/c-api/addon-instance/pvr/pvr_epg.h#L63 line 63
            # Look in the strings.po for the language selected to determine the text that will be displayed inside KODi for each code
            if not set(['movie']).isdisjoint(genreList):
                if not set(['adultsonly','erotic','Gay/lesbian','LGBTQ']).isdisjoint(genreList):
                    updatedgenreList.append(["Adult movie","0x18"][useHex])                                           #Adult movie                    0x18   
                elif not set(['detective','thriller','crime','crimedrama','mystery']).isdisjoint(genreList):
                    updatedgenreList.append(["Detective/Thriller","0x11"][useHex])                                    #Detectivc/Thriller             0x11
                elif not set(['sciencefiction','fantasy','horror','paranormal']).isdisjoint(genreList):
                    updatedgenreList.append(["Science fiction/Fantasy/Horror","0x13"][useHex])                        #Science Fiction/Fantasy/Horror 0x13
                elif not set(['comedy','comedydrama','darkcomedy']).isdisjoint(genreList):
                    updatedgenreList.append(["Comedy","0x14"][useHex])                                               #Comedy                         0x14
                elif not set(['western','war','military']).isdisjoint(genreList):
                    updatedgenreList.append(["Adventure/Western/War","0x12"][useHex])                                #Adventure/Western/War          0x12
                elif not set(['soap', 'melodrama','folkloric', 'music','musical','musicalcomedy']).isdisjoint(genreList):
                    updatedgenreList.append(["Soap/Melodrama/Folkloric","0x15"][useHex])                             #Soap/Melodrama/Folkloric       0x15
                elif not set(['romance', 'romanticcomedy']).isdisjoint(genreList):
                    updatedgenreList.append(["Romance","0x16"][useHex])                                              #Romance                        0x16
                elif not set(['seriou','classical', 'religiou', 'historicaldrama', 'biography', 'documentary', 'docudrama']).isdisjoint(genreList):
                    updatedgenreList.append(["Serious/Classical/Religious/Historical movie/Drama","0x17"][useHex])   #Serious/Classical/Religious/Historical Movie/Drama     0x17
                elif not set(['adventure']).isdisjoint(genreList):
                    updatedgenreList.append(["Adventure/Western/War","0x12"][useHex])                                #Adventure/Western/War          0x12
                else:
                    updatedgenreList.append(["Movie / drama","0x10"][useHex])                                        #Movie/Drana                    0x10
            
            #Adult TV Shows
            elif not set(['adultsonly','erotic','Gay/lesbian','LGBTQ']).isdisjoint(genreList):
                    updatedgenreList.append(["Adult movie","0xF8"][useHex])                                          #Adult Show                     0xF8

            #Children Programming
            elif not set(['children', 'youth']).isdisjoint(genreList):
                if edict['eprating'] == 'TV-Y':
                    updatedgenreList.append(["Pre-school children's programs","0x51"][useHex])                       #Pre-school Children's Programmes           0x51
                elif edict['eprating'] == 'TV-Y7':
                    updatedgenreList.append(["Entertainment programs for 6 to 14","0x52"][useHex])                   #Entertainment Programmes for 6 to 14       0x52
                elif edict['eprating'] == 'TV-G':
                    updatedgenreList.append(["Entertainment programs for 10 to 16","0x53"][useHex])                  #Entertainment Programmes for 10 to 16      0x53                                      
                elif not set(['informational','educational','science','technology']).isdisjoint(genreList):
                    updatedgenreList.append(["Informational/Educational/School programs","0x54"][useHex])            #Informational/Educational/School Programme 0x54        
                elif not set(['anime', 'animated']).isdisjoint(genreList):
                    updatedgenreList.append(["Cartoons/Puppets","0x55"][useHex])                                     #Cartoons/Puppets                           0x55 
                else: 
                    updatedgenreList.append(["Children's / Youth programs","0x50"][useHex])                          #Children's/Youth Programs                  0x50
            
            #MLeisure/Hobbies
            elif not set(['advertisement', 'archery', 'auto', 'bodybuilding', 'consumer', 'cooking', 'exercise', 'fishing', 'fitnes', 
                    'fitness&amp;health', 'gardening', 'handicraft', 'health', 'hobbie', 'homeimprovement', 'house/garden', 'how-to', 'hunting', 
                    'motoring', 'outdoor', 'selfimprovement', 'shopping', 'tourism', 'travel']).isdisjoint(genreList):
                
                if not set(['tourism','travel']).isdisjoint(genreList):
                    updatedgenreList.append(["Tourism / Travel","0xA1"][useHex])                                     #Tourism/Travel             0xA1
                elif not set(['handicraft','homeimprovement','house/garden','how-to']).isdisjoint(genreList):
                    updatedgenreList.append(["Handicraft","0xA2"][useHex])                                           #Handicraft                 0xA2         
                elif not set(['motoring', 'auto']).isdisjoint(genreList):
                    updatedgenreList.append(["Motoring","0xA3"][useHex])                                             #Motoring                   0xA3
                elif not set(['fitnes','health', 'fitness&amp;health','selfimprovement','bodybuilding','exercise']).isdisjoint(genreList):
                    updatedgenreList.append(["Fitness and health","0xA4"][useHex])                                   #Fitness & Health           0xA4
                elif not set(['cooking']).isdisjoint(genreList):
                    updatedgenreList.append(["Cooking","0xA5"][useHex])                                              #Cooking                    0xA5
                elif not set(['advertisement','shopping','consumer']).isdisjoint(genreList):
                    updatedgenreList.append(["Advertisement / Shopping","0xA6"][useHex])                             #Advertisement/Shopping     0xA6
                elif not set(['gardening']).isdisjoint(genreList):
                    updatedgenreList.append(["Gardening","0xA7"][useHex])                                            #Gardening                  0xA7
                else: 
                    updatedgenreList.append(["Leisure hobbies","0xA0"][useHex])                                      #Leisure/Hobbies            0xA0
               
            #News 
            elif not set(['currentaffair', 'documentary', 'interview', 'new', 'newsmagazine']).isdisjoint(genreList):
                
                if not set(['weather']).isdisjoint(genreList):
                    updatedgenreList.append(["News/Weather report","0x21"][useHex])                                  #News/Weather Report            0x21
                elif not set(['newsmagazine']).isdisjoint(genreList):
                    updatedgenreList.append(["News magazine","0x22"][useHex])                                        #News Magazine                  0x22         
                elif not set(['documentary']).isdisjoint(genreList):
                    updatedgenreList.append(["Documentary","0x23"][useHex])                                          #Documentary                    0x23
                elif not set(['discussion', 'interview', 'debate']).isdisjoint(genreList):
                    updatedgenreList.append(["Discussion/Interview/Debate","0x24"][useHex])                          #Discussion/Interview/Debate    0x24
                else:
                    updatedgenreList.append(["News/Current affairs","0x20"][useHex])                                 #News/Current Affair            0x20

            #Sports        
            elif not set(['actionsport', 'australianrulesfootball', 'autoracing', 'baseball', 'basketball', 'beachvolleyball', 'billiard', 'bmxracing', 
                    'boatracing', 'bobsled', 'bowling', 'boxing', 'bullriding', 'cheerleading', 'cricket', 'cycling', 'diving', 'dragracing', 'equestrian', 
                    'esport', 'fencing', 'fieldhockey', 'figureskating', 'fishing', 'football', 'footvolley', 'golf', 'gymnastic', 'hockey', 'horse', 'horseracing', 
                    'karate', 'lacrosse', 'martialart', 'mixedmartialart', 'motorcycle', 'motorcycleracing', 'motorsport', 'multisportevent', 'olympic', 
                    'paralympic', 'pickleball', 'prowrestling', 'racing', 'rodeo', 'rugby', 'rugbyleague', 'running', 'sailing', 'skating', 'skiing', 
                    'snowboarding', 'soccer', 'softball', 'squash', 'superbowl', 'surfing', 'swimming', 'tabletenni', 'tenni', 'track/field', 'volleyball', 
                    'waterpolo', 'watersport', 'weightlifting', 'wintersport', 'worldcup', 'wrestling']).isdisjoint(genreList):
                if not set(['documentary','sportstalk']).isdisjoint(genreList):
                    updatedgenreList.append(["Sports magazines","0x42"][useHex])                                     #Sports magazines                                   0x42
                elif not set(['final','superbowl','worldcup','olympic','paralympic']).isdisjoint(genreList):
                    updatedgenreList.append(["Special events (Olympic Games, World Cup, etc.)","0x41"][useHex])      #Special events (Olympic Games, World Cup, etc.)    0x41
                elif not set(['football','soccer','australianrulesfootball']).isdisjoint(genreList):
                    updatedgenreList.append(["Football/Soccer","0x43"][useHex])                                      #Football/Soccer                                    0x43
                elif not set(['tenni','squash']).isdisjoint(genreList):
                    updatedgenreList.append(["Tennis/Squash","0x44"][useHex])                                        #Tennis/Squash                                      0x44           
                elif not set(['basketball', 'hockey','baseball','softball', 'gymnastic','volleyball','track/field','fieldhockey', 
                        'lacrosse','rugby','cricket','fieldhockey']).isdisjoint(genreList):
                    updatedgenreList.append(["Team sports (excluding football)","0x45"][useHex])                     #Team sports (excluding football)                   0x45
                elif not set(['running','snowboarding','wrestling','cycling']).isdisjoint(genreList):
                    updatedgenreList.append(["Athletics","0x46"][useHex])                                            #Athletics                                          0x46
                elif not set(['autoracing','dragracing','motorcycle','motorcycleracing','motorsport']).isdisjoint(genreList):
                    updatedgenreList.append(["Motor sport","0x47"][useHex])                                          #Motor sports                                       0x47
                elif not set(['bmxracing', 'boatracing', 'diving', 'fishing', 'sailing', 'surfing', 'swimming', 'waterpolo', 'watersport']).isdisjoint(genreList):
                    updatedgenreList.append(["Water sport","0x48"][useHex])                                          #Water sport                                        0x48
                elif not set(['wintersport', 'skiing', 'bobsled', 'figureskating', 'skating','snowboarding']).isdisjoint(genreList):
                    updatedgenreList.append(["Winter sports","0x49"][useHex])                                        #Winter sports                                      0x49
                elif not set(['horse', 'equestrian', 'horseracing','rodeo','bullriding']).isdisjoint(genreList):
                    updatedgenreList.append(["Equestrian","0x4A"][useHex])                                           #Equestrian                                         0x4A
                elif not set(['martialart', 'mixedmartialart','karate']).isdisjoint(genreList):
                    updatedgenreList.append(["Martial sports","0x4B"][useHex])                                       #Martial sports                                     0x4B
                else:
                    updatedgenreList.append(["Sports","0x40"][useHex])                                               #Sports                                             0x40

            #Show
            elif not set(['competition', 'competitionreality', 'contest', 'gameshow', 'quiz', 'reality', 'talk', 'talkshow', 'variety', 
                    'varietyshow']).isdisjoint(genreList):
                if not set(['gameshow','quiz','contest']).isdisjoint(genreList):
                    updatedgenreList.append(["Game show/Quiz/Contest","0x31"][useHex])                               #Game show/Quiz/Contest             0x31
                elif not set(['variety','varietyshow', 'competition', 'competitionreality', 'reality']).isdisjoint(genreList):
                    updatedgenreList.append(["Variety show","0x32"][useHex])                                         #Variety Show                       0x32              
                elif not set(['talk', 'talkshow']).isdisjoint(genreList):
                    updatedgenreList.append(["Talk show","0x33"][useHex])                                            #Talk Show                          0x33
                else:
                    updatedgenreList.append(["Show / Game show","0x30"][useHex])                                     #Show/Game Show                     0x30

            #Music/Ballet/Dance
            elif not set(['ballet', 'classicalmusic', 'dance', 'folk', 'jazz', 'music', 'musical', 'opera', 'pop', 'rock', 'traditionalmusic']).isdisjoint(genreList):
                if not set(['rock','pop']).isdisjoint(genreList):
                    updatedgenreList.append(["Rock/Pop","0x61"][useHex])                                             #Rock/Pop                           0x61
                elif not set(['seriou','classicalmusic']).isdisjoint(genreList):
                    updatedgenreList.append(["Serious music/Classical music","0x62"][useHex])                        #Seriouis/Classical Music           0x62      
                elif not set(['folk','traditionalmusic']).isdisjoint(genreList):
                    updatedgenreList.append(["Folk/Traditional music","0x63"][useHex])                               #Folk/Traditional Music             0x63
                elif not set(['jazz']).isdisjoint(genreList):
                    updatedgenreList.append(["Jazz","0x64"][useHex])                                                 #Jazz                               0x64
                elif not set(['musical','opera']).isdisjoint(genreList):
                    updatedgenreList.append(["Musical/Opera","0x65"][useHex])                                        #Musical/Opera                      0x65
                elif not set(['ballet']).isdisjoint(genreList):
                    updatedgenreList.append(["Ballet","0x66"][useHex])                                               #Ballet                             0x66
                else:
                    updatedgenreList.append(["Music / Ballet / Dance","0x60"][useHex])                               #Music/Ballet/Dance                 0x60

            #Arts/Culture
            elif not set(['art', 'arts/craft', 'artsmagazine', 'broadcasting', 'cinema', 'culture', 'culturemagazine', 'experimentalfilm', 'fashion', 'film', 
                'fineart', 'literature', 'newmedia', 'performingart', 'popularculture', 'pres', 'religion', 'religiou', 'traditionalart', 'video']).isdisjoint(genreList):

                if not set(['performingart']).isdisjoint(genreList):
                    updatedgenreList.append(["Performing arts","0x71"][useHex])                                      #Performing Arts                    0x71
                elif not set(['fineart']).isdisjoint(genreList):
                    updatedgenreList.append(["Fine arts","0x72"][useHex])                                            #Fine Arts                          0x72            
                elif not set(['religion','religiou']).isdisjoint(genreList):
                    updatedgenreList.append(["Religion","0x73"][useHex])                                             #Religion                           0x73
                elif not set(['popculture','traditionalart']).isdisjoint(genreList):
                    updatedgenreList.append(["Popular culture/Traditional arts","0x74"][useHex])                     #Pop Culture/Traditional Arts       0x74
                elif not set(['literature']).isdisjoint(genreList):
                    updatedgenreList.append(["Literature","0x75"][useHex])                                           #Literature                         0x75
                elif not set(['film','cinema']).isdisjoint(genreList):
                    updatedgenreList.append(["Film/Cinema","0x76"][useHex])                                          #Film/Cinema                        0x76        
                elif not set(['experimentalfilm','video']).isdisjoint(genreList):
                    updatedgenreList.append(["Experimental film/Video","0x77"][useHex])                              #Experimental Film/Video            0x77
                elif not set(['broadcasting','pres']).isdisjoint(genreList):
                    updatedgenreList.append(["Broadcasting/Press","0x78"][useHex])                                   #Broadcasting/Press                 0x78
                elif not set(['newmedia']).isdisjoint(genreList):
                    updatedgenreList.append(["New media","0x79"][useHex])                                            #New Media                          0x79
                elif not set(['artmagazine','culturemagazine','magazine']).isdisjoint(genreList):
                    updatedgenreList.append(["Arts magazines/Culture magazines","0x7A"][useHex])                     #Arts/Culture Magazine              0x7A
                elif not set(['fashion']).isdisjoint(genreList):
                    updatedgenreList.append(["Fashion","0x7B"][useHex])                                              #Fashion                            0x7B
                else:    
                    updatedgenreList.append(["Arts / Culture (without music)","0x70"][useHex])                       #Arts/Culture                       0x70

            #Social/Politics/Economics
            elif not set(['community', 'documentary', 'economic', 'magazine', 'politic', 'political', 'publicaffair', 
                    'remarkablepeople', 'report', 'social', 'socialadvisory']).isdisjoint(genreList):

                if not set(['magazine','report','documentary']).isdisjoint(genreList):
                    updatedgenreList.append(["Magazines/Reports/Documentary","0x81"][useHex])                        #Magazines/Reports/Documentary      0x81
                elif not set(['economic','socialadvisory']).isdisjoint(genreList):
                    updatedgenreList.append(["Economics/Social advisory","0x82"][useHex])                            #Economics/Social Advisory          0x82            
                elif not set(['remarkablepeople']).isdisjoint(genreList):
                    updatedgenreList.append(["Remarkable people","0x83"][useHex])                                    #Remarkable People                  0x83
                else:
                    updatedgenreList.append(["Social/Political issues/Economics","0x80"][useHex])                    #Social/Political/Economics         0x80

            #MEducational/Science
            elif not set(['adulteducation', 'animal', 'dogshow', 'education', 'educational', 'environment', 'expedition', 'factual', 'foreigncountrie', 
                    'furthereducation', 'health', 'language', 'medical', 'medicine', 'naturalscience', 'nature', 'outdoor', 'physiology', 'psychology', 
                    'science', 'social', 'spiritualscience', 'technology']).isdisjoint(genreList):
                
                if not set(['nature','animal','environment','outdoor','dogshow']).isdisjoint(genreList):
                    updatedgenreList.append(["Nature/Animals/Environment","0x91"][useHex])                           #Nature/Animals/Environment         0x91          
                elif not set(['technology','naturalscience']).isdisjoint(genreList):
                    updatedgenreList.append(["Technology/Natural sciences","0x92"][useHex])                          #Technology/Natural Sciences        0x92
                elif not set(['medicine','physiology','psychology','health','medical']).isdisjoint(genreList):
                    updatedgenreList.append(["Medicine/Physiology/Psychology","0x93"][useHex])                       #Medicine/Physiology/Psychology     0x93
                elif not set(['foreigncountrie','expedition']).isdisjoint(genreList):
                    updatedgenreList.append(["Foreign countries/Expeditions","0x94"][useHex])                        #Foreign Countries/Expeditions      0x94
                elif not set(['social','spiritualscience']).isdisjoint(genreList):
                    updatedgenreList.append(["Social/Spiritual sciences","0x95"][useHex])                            #Social/Spiritual Sciences          0x95
                elif not set(['furthereducation','adulteducation']).isdisjoint(genreList):
                    updatedgenreList.append(["Further education","0x96"][useHex])                                    #Further Education                  0x96
                elif not set(['language']).isdisjoint(genreList):
                    updatedgenreList.append(["Languages","0x97"][useHex])                                            #Languages                          0x97
                else:
                    updatedgenreList.append(["Education / Science / Factual topics","0x90"][useHex])                 #Education/Science                  0x90

            # TVHeadend does not recognize the non-movie genres below.  0xF# are user defined genres per the specification and TVH
            # does not use them.  Kodi does use these user defined values.  I could not figure out a way to pass the hex code to TVH
            # instead of the string to be recoginzed correctly.  When TVH is modified to accept a hex value for the genre we can then
            # use these codes to get correct EPG colored grids.  One color for movies with it's separate color and one for TV shows.

            elif not set(['crime', 'crimedrama', 'detective', 'mystery', 'thriller']).isdisjoint(genreList):
                    updatedgenreList.append(["Detective/Thriller","0xF1"][useHex])                                   #Detective/Thriller                 0xF1

            elif not set(['fantasy', 'horror', 'paranormal', 'sciencefiction']).isdisjoint(genreList):
                    updatedgenreList.append(["Science fiction/Fantasy/Horror","0xF3"][useHex])                       #Science Fiction/Fantasy/Horror     0xF3
                    
            elif not set(['western','war','military']).isdisjoint(genreList):
                    updatedgenreList.append(["Adventure/Western/War","0xF2"][useHex])                                #Adventure/Western/War              0xF2

            elif not set(['comedy', 'comedydrama', 'darkcomedy', 'sitcom']).isdisjoint(genreList):
                    updatedgenreList.append(["Comedy","0xF4"][useHex])                                               #Comedy                             0xF4

            elif not set(['folk', 'folkloric', 'melodrama', 'music', 'musical', 'musicalcomedy', 'soap']).isdisjoint(genreList):
                    updatedgenreList.append(["Soap/Melodrama/Folkloric","0xF5"][useHex])                             #Soap/Melodrama/Folkloric           0xF5

            elif not set(['romance','romanticcomedy']).isdisjoint(genreList):
                    updatedgenreList.append(["Romance","0xF6"][useHex])                                              #Romance                            0xF6

            elif not set(['biography', 'classical', 'classicalreligion', 'docudrama', 'historical', 'historicaldrama', 'religion', 'seriou']).isdisjoint(genreList):
                    updatedgenreList.append(["Serious/Classical/Religious/Historical movie/Drama","0xF7"][useHex])  #Serious/Classical/Religion/Historical  0xF7

            elif not set(['adventure']).isdisjoint(genreList):
                    updatedgenreList.append(["Adventure/Western/War","0xF2"][useHex])                               #Adventure/Western/War              0xF2

            elif not set(['drama']).isdisjoint(genreList):
                    updatedgenreList.append(["Movie / Drama","0xF0"][useHex])                                       #Drama                              0xF0

            return updatedgenreList


        if epgenre == '2':               #User selected 'original' epg tag
            for g in EPgenre:
                genreList.append(g)
        return genreList

    def printHeader(fh, enc):           #This is the header for the XMLTV file
        logging.info('Creating xmltv.xml file...')
        fh.write(f'<?xml version=\"1.0\" encoding=\"{enc}\"?>\n')
        #fh.write("<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n\n")
        fh.write("<tv source-info-url=\"http://tvschedule.zap2it.com/\" source-info-name=\"zap2it.com\">\n")

    def printFooter(fh):                #This is the footer for the XMLTV file
        fh.write("</tv>")

    def printStations(fh):              #Take the data collected in edict variable and parse it, to writhe the XMLTV file
        global stationCount
        stationCount = 0
        try:
            logging.info('Writing Stations to xmltv.xml file...')
            try:
                scheduleSort = OrderedDict(sorted(iter(schedule.items()), key=lambda x: x[1]['chnum']))
            except:
                scheduleSort = OrderedDict(sorted(iter(schedule.items()), key=lambda x: x[1]['chfcc']))
            for station in scheduleSort:
                fh.write(f'\t<channel id=\"{station}.zap2epg\">\n')
                if 'chtvh' in scheduleSort[station] and scheduleSort[station]['chtvh'] is not None:
                    xchtvh = html.escape(scheduleSort[station]['chtvh'], quote=True)
                    fh.write(f'\t\t<display-name>{xchtvh}</display-name>\n')
                if 'chnum' in scheduleSort[station] and 'chfcc' in scheduleSort[station]:
                    xchnum = scheduleSort[station]['chnum']
                    xchfcc = scheduleSort[station]['chfcc']
                    xchfcc = html.escape(xchfcc, quote=True)
                    fh.write(f'\t\t<display-name>{xchnum} {xchfcc}</display-name>\n')
                    fh.write(f'\t\t<display-name>{xchfcc}</display-name>\n')
                    fh.write(f'\t\t<display-name>{xchnum}</display-name>\n')
                elif 'chfcc' in scheduleSort[station]:
                    xchnum = scheduleSort[station]['chfcc']
                    xcfcc = html.escape(xcfcc, quote=True)
                    fh.write(f'\t\t<display-name>{xcfcc}</display-name>\n')
                elif 'chnum' in scheduleSort[station]:
                    xchnum = scheduleSort[station]['chnum']
                    fh.write(f'\t\t<display-name>{xchnum}</display-name>\n')
                if 'chicon' in scheduleSort[station]:
                    fh.write(f'\t\t<icon src=\"http:{scheduleSort[station]["chicon"]}\" />\n')
                fh.write("\t</channel>\n")
                stationCount += 1
        except Exception as e:
            logging.exception('Exception: printStations')

    def printEpisodes(fh):                  #Take the data collected in edict variable and parse it, to writhe the XMLTV file
        global episodeCount
        episodeCount = 0
        try:
            logging.info('Writing Episodes to xmltv.xml file...')
            if xdesc is True:
                logging.info('Appending Xdetails to description for xmltv.xml file...')
            for station in schedule:
                sdict = schedule[station]
                for episode in sdict:
                    if not episode.startswith("ch"):
                        try:
                            edict = sdict[episode]
                            if 'epstart' in edict:
                                lang = getLang(edict['epdesc'], edict['epshow'], edict['eptitle'])
                                edict['lang'] = lang
                                startTime = convTime(edict['epstart'])
                                is_dst = time.daylight and time.localtime().tm_isdst > 0
                                TZoffset = "%.2d%.2d" %(- (time.altzone if is_dst else time.timezone)/3600, 0)
                                stopTime = convTime(edict['epend'])
                                fh.write(f'\t<programme start=\"{startTime} {TZoffset}\" stop=\"{stopTime} {TZoffset}\" channel=\"{station}.zap2epg\">\n')
                                dd_progid = edict['epid']
                                fh.write(f'\t\t<episode-num system=\"dd_progid\">{dd_progid[:-4]}.{dd_progid[-4:]}</episode-num>\n')
                                if edict['epshow'] is not None:
                                    titleShow = edict['epshow']
                                    if safetitle == "true":
                                        titleShow = re.sub('[\\/*?:"<>|]', escapeChar, titleShow)
                                    titleShow = html.escape(titleShow, quote=True)
                                    titleShow = f'\t\t<title lang=\"{lang}">{titleShow}</title>\n'
                                    fh.write(titleShow)
                                if edict['eptitle'] is not None:
                                    titleEpisode = edict['eptitle']
                                    if safeepisode == "true":
                                        titleEpisode = re.sub('[\\/*?:"<>|]', escapeChar, titleEpisode)
                                    titleEpisode = html.escape(titleEpisode, quote=True)
                                    titleEpisode = f'\t\t<sub-title lang="{lang}">{titleEpisode}</sub-title>\n'
                                    fh.write(titleEpisode)

                                if xdesc == 'true':
                                    xdescSort = addXDetails(edict)
                                    xdescSort = html.escape(xdescSort, quote=True)
                                    fh.write(f'\t\t<desc lang="{lang}">{xdescSort}</desc>\n')
                                if xdesc == 'false':
                                    if edict['epdesc'] is not None:
                                        epdesc = html.escape(f"{edict['epdesc']}\nLang: {lang}", quote=True)
                                        fh.write(f'\t\t<desc lang="{lang}">{epdesc}</desc>\n')
                                if edict['epsn'] is not None and edict['epen'] is not None:
                                    fh.write(f'\t\t<episode-num system=\"onscreen\">S{edict["epsn"].zfill(2)}E{edict["epen"].zfill(2)}</episode-num>\n')
                                    fh.write(f'\t\t<episode-num system=\"xmltv_ns\">{str(int(edict["epsn"])-1)}.{str(int(edict["epen"])-1)}.</episode-num>\n')
                                if edict['epyear'] is not None:
                                    fh.write(f'\t\t<date>{edict["epyear"]}</date>\n')
                                if not episode.startswith("MV"):
                                    if epicon == '1':
                                        if edict['epimage'] is not None and edict['epimage'] != '':
                                            fh.write(f'\t\t<icon src="https://zap2it.tmsimg.com/assets/{edict["epimage"]}.jpg" />\n')
                                        else:
                                            if edict['epthumb'] is not None and edict['epthumb'] != '':
                                                fh.write(f'\t\t<icon src="https://zap2it.tmsimg.com/assets/{edict["epthumb"]}.jpg" />\n')
                                    if epicon == '2':
                                        if edict['epthumb'] is not None and edict['epthumb'] != '':
                                            fh.write(f'\t\t<icon src="https://zap2it.tmsimg.com/assets/{edict["epthumb"]}.jpg" />\n')
                                if episode.startswith("MV"):
                                    if edict['epthumb'] is not None and edict['epthumb'] != '':
                                        fh.write(f'\t\t<icon src="https://zap2it.tmsimg.com/assets/{edict["epthumb"]}.jpg" />\n')
                                if not any(i in ['New', 'Live'] for i in edict['epflag']):
                                    fh.write("\t\t<previously-shown ")
                                    if edict['epoad'] is not None and int(edict['epoad']) > 0:
                                        fh.write(f'start=\"{convTime(edict["epoad"])} {TZoffset}\" ')
                                    fh.write("/>\n")
                                if edict['epflag'] is not None:
                                    if 'New' in edict['epflag']:
                                        fh.write("\t\t<new />\n")
                                    if 'Live' in edict['epflag']:
                                        fh.write("\t\t<live />\n")
                                if edict['eprating'] is not None:
                                    fh.write(f'\t\t<rating>\n\t\t\t<value>{edict["eprating"]}</value>\n\t\t</rating>\n')
                                if edict['epstar'] is not None:
                                    fh.write(f'\t\t<star-rating>\n\t\t\t<value>{edict["epstar"]}/4</value>\n\t\t</star-rating>\n')
                                if epgenre != '0':
                                   if edict['epfilter'] is not None and edict['epgenres'] is not None:
                                        genreNewList = genreSort(edict['epfilter'], edict['epgenres'], edict)
                                        for genre in genreNewList:
                                            genre = html.escape(genre, quote=True)
                                            fh.write(f'\t\t<category lang=\"en\">{genre}</category>\n')
                                fh.write("\t</programme>\n")
                                episodeCount += 1
                        except Exception as e:
                            logging.exception('No data for episode %s:', episode)
                            #fn = os.path.join(cacheDir, episode + '.json')
                            #os.remove(fn)
                            #logging.info('Deleting episode %s:', episode)
        except Exception as e:
            logging.exception('Exception: printEpisodes')

    def xmltv():            # Routine called after the data has been collected from zap2it website
        try:
            enc = 'UTF-8'
            outFile = os.path.join(userdata, 'xmltv.xml')
            fh = codecs.open(outFile, 'w+b', encoding=enc)
            printHeader(fh, enc)
            printStations(fh)
            printEpisodes(fh)
            printFooter(fh)
            fh.close()
        except Exception as e:
            logging.exception('Exception: xmltv')

    def parseStations(content):     #Routine downloads the necessary files from zap2it website.
        try:
            ch_guide = json.loads(content)
            for station in ch_guide['channels']:
                skey = station.get('channelId')
                if stationList is not None:
                    if skey in stationList:
                        schedule[skey] = {}
                        chName = station.get('callSign')
                        schedule[skey]['chfcc'] = chName
                        schedule[skey]['chicon'] = station.get('thumbnail').split('?')[0]
                        chnumStart = station.get('channelNo')
                        if '.' not in chnumStart and chmatch == 'true' and chName is not None:
                            chsub = re.search('(\d+)$', chName)
                            if chsub is not None:
                                chnumUpdate = chnumStart + '.' + chsub.group(0)
                            else:
                                chnumUpdate = chnumStart + '.1'
                        else:
                            chnumUpdate = chnumStart
                        schedule[skey]['chnum'] = chnumUpdate
                        if tvhmatch == 'true' and '.' in chnumUpdate:
                            if chnumUpdate in tvhMatchDict:
                                schedule[skey]['chtvh'] = tvhMatchDict[chnumUpdate]
                            else:
                                schedule[skey]['chtvh'] = None
                else:
                    schedule[skey] = {}
                    chName = station.get('callSign')
                    schedule[skey]['chfcc'] = chName
                    schedule[skey]['chicon'] = station.get('thumbnail').split('?')[0]
                    chnumStart = station.get('channelNo')
                    if '.' not in chnumStart and chmatch == 'true' and chName is not None:
                        chsub = re.search('(\d+)$', chName)
                        if chsub is not None:
                            chnumUpdate = chnumStart + '.' + chsub.group(0)
                        else:
                            chnumUpdate = chnumStart + '.1'
                    else:
                        chnumUpdate = chnumStart
                    schedule[skey]['chnum'] = chnumUpdate
                    if tvhmatch == 'true' and '.' in chnumUpdate:
                        if chnumUpdate in tvhMatchDict:
                            schedule[skey]['chtvh'] = tvhMatchDict[chnumUpdate]
                        else:
                            schedule[skey]['chtvh'] = None
        except Exception as e:
            logging.exception('Exception: parseStations')

    def parseEpisodes(content):
        CheckTBA = "Safe"
        try:
            ch_guide = json.loads(content)
            for station in ch_guide['channels']:
                skey = station.get('channelId')
                if stationList is not None:
                    if skey in stationList:
                        episodes = station.get('events')
                        for episode in episodes:
                            epkey = str(calendar.timegm(time.strptime(episode.get('startTime'), '%Y-%m-%dT%H:%M:%SZ')))
                            schedule[skey][epkey] = {}
                            schedule[skey][epkey]['epid'] = episode['program'].get('tmsId')
                            schedule[skey][epkey]['epstart'] = str(calendar.timegm(time.strptime(episode.get('startTime'), '%Y-%m-%dT%H:%M:%SZ')))
                            schedule[skey][epkey]['epend'] = str(calendar.timegm(time.strptime(episode.get('endTime'), '%Y-%m-%dT%H:%M:%SZ')))
                            schedule[skey][epkey]['eplength'] = episode.get('duration')
                            schedule[skey][epkey]['epshow'] = episode['program'].get('title')
                            schedule[skey][epkey]['eptitle'] = episode['program'].get('episodeTitle')
                            schedule[skey][epkey]['epdesc'] = episode['program'].get('shortDesc')
                            schedule[skey][epkey]['epyear'] = episode['program'].get('releaseYear')
                            schedule[skey][epkey]['eprating'] = episode.get('rating')
                            schedule[skey][epkey]['epflag'] = episode.get('flag')
                            schedule[skey][epkey]['eptags'] = episode.get('tags')
                            schedule[skey][epkey]['epsn'] = episode['program'].get('season')
                            schedule[skey][epkey]['epen'] = episode['program'].get('episode')
                            schedule[skey][epkey]['epthumb'] = episode.get('thumbnail')
                            schedule[skey][epkey]['epoad'] = None
                            schedule[skey][epkey]['epstar'] = None
                            schedule[skey][epkey]['epfilter'] = episode.get('filter')
                            schedule[skey][epkey]['epgenres'] = None
                            schedule[skey][epkey]['epcredits'] = None
                            schedule[skey][epkey]['epxdesc'] = None
                            schedule[skey][epkey]['epseries'] = episode.get('seriesId')
                            schedule[skey][epkey]['epimage'] = None
                            schedule[skey][epkey]['epfan'] = None
                            if "TBA" in schedule[skey][epkey]['epshow']:
                                CheckTBA = "Unsafe"
                            elif schedule[skey][epkey]['eptitle']:
                                if "TBA" in schedule[skey][epkey]['eptitle']:
                                    CheckTBA = "Unsafe"
                else:
                    episodes = station.get('events')
                    for episode in episodes:
                        epkey = str(calendar.timegm(time.strptime(episode.get('startTime'), '%Y-%m-%dT%H:%M:%SZ')))
                        schedule[skey][epkey] = {}
                        schedule[skey][epkey]['epid'] = episode['program'].get('tmsId')
                        schedule[skey][epkey]['epstart'] = str(calendar.timegm(time.strptime(episode.get('startTime'), '%Y-%m-%dT%H:%M:%SZ')))
                        schedule[skey][epkey]['epend'] = str(calendar.timegm(time.strptime(episode.get('endTime'), '%Y-%m-%dT%H:%M:%SZ')))
                        schedule[skey][epkey]['eplength'] = episode.get('duration')
                        schedule[skey][epkey]['epshow'] = episode['program'].get('title')
                        schedule[skey][epkey]['eptitle'] = episode['program'].get('episodeTitle')
                        schedule[skey][epkey]['epdesc'] = episode['program'].get('shortDesc')
                        schedule[skey][epkey]['epyear'] = episode['program'].get('releaseYear')
                        schedule[skey][epkey]['eprating'] = episode.get('rating')
                        schedule[skey][epkey]['epflag'] = episode.get('flag')
                        schedule[skey][epkey]['eptags'] = episode.get('tags')
                        schedule[skey][epkey]['epsn'] = episode['program'].get('season')
                        schedule[skey][epkey]['epen'] = episode['program'].get('episode')
                        schedule[skey][epkey]['epthumb'] = episode.get('thumbnail')
                        schedule[skey][epkey]['epoad'] = None
                        schedule[skey][epkey]['epstar'] = None
                        schedule[skey][epkey]['epfilter'] = episode.get('filter')
                        schedule[skey][epkey]['epgenres'] = None
                        schedule[skey][epkey]['epcredits'] = None
                        schedule[skey][epkey]['epxdesc'] = None
                        schedule[skey][epkey]['epseries'] = episode.get('seriesId')
                        schedule[skey][epkey]['epimage'] = None
                        schedule[skey][epkey]['epfan'] = None
                        if "TBA" in schedule[skey][epkey]['epshow']:
                            CheckTBA = "Unsafe"
                        elif schedule[skey][epkey]['eptitle']:
                            if "TBA" in schedule[skey][epkey]['eptitle']:
                                CheckTBA = "Unsafe"
        except Exception as e:
            logging.exception('Exception: parseEpisodes')
        return CheckTBA

    def parseXdetails():
        showList = []
        failList = []
        try:
            for station in schedule:
                sdict = schedule[station]
                for episode in sdict:
                    if not episode.startswith("ch"):
                        edict = sdict[episode]
                        EPseries = edict['epseries']
                        showList.append(edict['epseries'])
                        filename = EPseries + '.json'
                        fileDir = os.path.join(cacheDir, filename)
                        try:
                            if not os.path.exists(fileDir) and EPseries not in failList:
                                retry = 3
                                while retry > 0:
                                    logging.info('Downloading details data for: %s', EPseries)
                                    url = 'https://tvlistings.zap2it.com/api/program/overviewDetails'
                                    data = 'programSeriesID=' + EPseries
                                    data_encode = data.encode('utf-8')
                                    try:
                                        URLcontent = urllib.request.Request(url, data=data_encode)
                                        JSONcontent = urllib.request.urlopen(URLcontent).read()
                                        if JSONcontent:
                                            with open(fileDir,"wb+") as f:
                                                f.write(JSONcontent)
                                                f.close()
                                            retry = 0
                                        else:
                                            time.sleep(1)
                                            retry -= 1
                                            logging.warning('Retry downloading missing details data for: %s', EPseries)
                                    except urllib.error.URLError as e:
                                        time.sleep(1)
                                        retry -= 1
                                        logging.warning('Retry downloading details data for: %s  -  %s', EPseries, e)
                            if os.path.exists(fileDir):
                                fileSize = os.path.getsize(fileDir)
                                if fileSize > 0:
                                    with open(fileDir, 'rb') as f:
                                        EPdetails = json.loads(f.read())
                                        f.close()
                                    logging.info('Parsing %s', filename)
                                    edict['epimage'] = EPdetails.get('seriesImage')
                                    edict['epfan'] = EPdetails.get('backgroundImage')
                                    EPgenres = EPdetails.get('seriesGenres')
                                    if filename.startswith("MV"):
                                        edict['epcredits'] = EPdetails['overviewTab'].get('cast')
                                        EPgenres = 'Movie|' + EPgenres
                                    edict['epgenres'] = EPgenres.split('|')
                                    #edict['epstar'] = EPdetails.get('starRating')
                                    EPlist = EPdetails['upcomingEpisodeTab']
                                    EPid = edict['epid']
                                    for airing in EPlist:
                                        if EPid.lower() == airing['tmsID'].lower():
                                            if not episode.startswith("MV"):
                                                try:
                                                    origDate = airing.get('originalAirDate')
                                                    if origDate != '':
                                                        EPoad = re.sub('Z', ':00Z', airing.get('originalAirDate'))
                                                        edict['epoad'] = str(calendar.timegm(time.strptime(EPoad, '%Y-%m-%dT%H:%M:%SZ')))
                                                except Exception as e:
                                                    logging.exception('Could not parse oad for: %s - %s', episode, e)
                                                try:
                                                    TBAcheck = airing.get('episodeTitle')
                                                    if TBAcheck != '':
                                                        if "TBA" in TBAcheck:
                                                            try:
                                                                os.remove(fileDir)
                                                                logging.info('Deleting %s due to TBA listings', filename)
                                                                showList.remove(edict['epseries'])
                                                            except OSError as e:
                                                                logging.warning('Error Deleting: %s - %s.' % (e.filename, e.strerror))
                                                except Exception as e:
                                                    logging.exception('Could not parse TBAcheck for: %s - %s', episode, e)
                                else:
                                    logging.warning('Could not parse data for: %s - deleting file', filename)
                                    os.remove(fileDir)
                            else:
                                logging.warning('Could not download details data for: %s - skipping episode', episode)
                                failList.append(EPseries)
                        except Exception as e:
                            logging.exception('Could not parse data for: %s - deleting file  -  %s', episode, e)
                            #os.remove(fileDir)
        except Exception as e:
            logging.exception('Exception: parseXdetails')
        return showList

    def addXDetails(edict):
        try:
            ratings = ""
            date = ""
            myear = ""
            new = ""
            live = ""
            hd = ""
            cc = ""
            cast = ""
            season = ""
            epis = ""
            episqts = ""
            prog = ""
            plot= ""
            descsort = ""
            genre = ""
            lang = ""
            bullet = "\u2022 "
            hyphen = "\u2013 "
            newLine = "\n"
            space = " "
            colon = "\u003A "
            vbar = "\u007C "
            slash = "\u2215 "
            comma = "\u002C "

            def getSortName(opt):
                return {
                    1: bullet,  2: newLine,     3: hyphen,  4: space,
                    5: colon,   6: vbar,        7: slash,   8: comma,
                    9: plot,    10: new,        11: hd,     12: cc, 
                    13: season, 14: ratings,    15: date,   16: prog,
                    17: epis,   18: episqts,    19: cast,   20: myear,
                    21: genre,  22: lang
                }.get(opt, None)

            def cleanSortList(optList):
                cleanList=[]
                optLen = len(optList)
                for opt in optList:
                    thisOption = getSortName(int(opt))
                    if thisOption:
                        cleanList.append(int(opt))
                for _ in reversed(cleanList):
                    if cleanList[-1] <= 8:
                        del cleanList[-1]
                return cleanList

            def makeDescsortList(optList):
                sortOrderList =[]
                lastOption = 1
                cleanedList = cleanSortList(optList)
                for opt in cleanedList:
                    thisOption = getSortName(int(opt))
                    if int(opt) <= 8 and lastOption <= 8:
                        if int(opt) == 2 and len(sortOrderList) > 1:
                            del sortOrderList[-1]
                            sortOrderList.append(thisOption)
                        lastOption = int(opt)
                    elif thisOption and lastOption:
                        sortOrderList.append(thisOption)
                        lastOption = int(opt)
                    elif thisOption:
                        lastOption = int(opt)
                return sortOrderList

            if edict['epoad'] is not None and int(edict['epoad']) > 0:
                is_dst = time.daylight and time.localtime().tm_isdst > 0
                TZoffset = (time.altzone if is_dst else time.timezone)
                origDate = int(edict['epoad']) + TZoffset
                finalDate = datetime.datetime.fromtimestamp(origDate).strftime('%B %d%% %Y')
                finalDate = re.sub('%', ',', finalDate)
                date = "First aired: " + finalDate + space
            if edict['epyear'] is not None:
                myear = "Released: " + edict['epyear'] + space
            if edict['eprating'] is not None:
                ratings = edict['eprating'] + space
            if edict['epflag'] != []:
                flagList = edict['epflag']
                new = ' - '.join(flagList).upper() + space
            #if edict['epnew'] is not None:
                #new = edict['epnew'] + space
            #if edict['eplive'] is not None:
                #new = edict['eplive'] + space
            #if edict['epprem'] is not None:
                #new = edict['epprem'] + space
            #if edict['epfin'] is not None:
                #new = edict['epfin'] + space
            if edict['eptags'] != []:
                tagsList = edict['eptags']
                cc = ' | '.join(tagsList).upper() + space
            #if edict['ephd'] is not None:
                #hd = edict['ephd'] + space
            if edict['epsn'] is not None and edict['epen'] is not None:
                s = re.sub('S', '', edict['epsn'])
                sf = "Season " + str(int(s))
                e = re.sub('E', '', edict['epen'])
                ef = "Episode " + str(int(e))
                season = sf + " - " + ef + space
            if edict['epcredits'] is not None:
                cast = "Cast: "
                castlist = ""
                prev = None
                EPcastList = []
                for c in edict['epcredits']:
                    EPcastList.append(c['name'])
                for g in EPcastList:
                    if prev is None:
                        castlist = g
                        prev = g
                    else:
                        castlist = castlist + ", " + g
                cast = cast + castlist + space
            if edict['epshow'] is not None:
                prog = edict['epshow'] + space
            if edict['eptitle'] is not None:
                epis = edict['eptitle'] + space
                episqts = '\"' + edict['eptitle'] + '\"' + space
            if edict['epdesc'] is not None:
                plot = edict['epdesc'] + space
            if edict['epgenres'] is not None:
                genre = ", ".join(edict["epgenres"]) + space
            if edict['lang'] is not None:
                langdict = {'en': 'English', 'es': 'Español', 'fr': 'Français'}
                lang = langdict.get(edict["lang"]) + space

        # todo - handle star ratings

            descsort = "".join(makeDescsortList(xdescOrder))
            return descsort
        except Exception as e:
            logging.exception('Exception: addXdetails to description')


    try:
        if not os.path.exists(cacheDir):
            os.mkdir(cacheDir)
        count = 0
        gridtime = gridtimeStart
        if stationList is None:
            logging.info('No channel list found - adding all stations!')
        if tvhoff == 'true' and tvhmatch == 'true':
            tvhMatchGet()
        deleteOldCache(gridtimeStart)
        while count < dayHours:
            filename = str(gridtime) + '.json.gz'
            fileDir = os.path.join(cacheDir, filename)
            if not os.path.exists(fileDir):
                try:
                    logging.info('Downloading guide data for: %s', str(gridtime))
                    url = f"http://tvlistings.zap2it.com/api/grid?lineupId=&timespan=3&headendId={lineupcode}&country={country}&device={device}&postalCode={zipcode}&time={str(gridtime)}&pref=-&userId=-"
                    saveContent = urllib.request.urlopen(url).read()
                    savepage(fileDir, saveContent)
                except:
                    logging.warning('Could not download guide data for: %s', str(gridtime))
                    logging.warning('URL: %s', url)
            if os.path.exists(fileDir):
                try:
                    with gzip.open(fileDir, 'rb') as f:
                        content = f.read()
                        f.close()
                    logging.info('Parsing %s', filename)
                    if count == 0:
                        parseStations(content)
                    TBAcheck = parseEpisodes(content)
                    if TBAcheck == "Unsafe":
                        try:
                            os.remove(fileDir)
                            logging.info('Deleting %s due to TBA listings', filename)
                        except OSError as e:
                            logging.warning('Error Deleting: %s - %s.' % (e.filename, e.strerror))
                except:
                    logging.warning('JSON file error for: %s - deleting file', filename)
                    os.remove(fileDir)
            count += 1
            gridtime = gridtime + 10800
        if xdetails == 'true':
            showList = parseXdetails()
        else:
            showList = []
        xmltv()
        deleteOldShowCache(showList)
        timeRun = round((time.time() - pythonStartTime),2)
        logging.info('zap2epg completed in %s seconds. ', timeRun)
        logging.info('%s Stations and %s Episodes written to xmltv.xml file.', str(stationCount), str(episodeCount))
        return timeRun, stationCount, episodeCount
    except Exception as e:
        logging.exception('Exception: main')

if __name__ == '__main__':
    userdata = os.getcwd()
    log = os.path.join(userdata, 'zap2epg.log')
    logging.basicConfig(filename=log, filemode='w', format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    mainRun(userdata)
