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
from tvh import tvh_connect, tvh_getData
from genre import genreSort, countGenres
import codecs
import time
import datetime
import calendar
import gzip
import os
import logging
import re
import json
import xml.etree.ElementTree as ET
from collections import OrderedDict
import html
from collections import Counter

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
    useHex = 0

    for setting in settingsDict:
        if setting == 'slist':                              #station list from gracenote website i.e. 100105
            stationList = settingsDict[setting]
        if setting == 'zipcode':                            #zipcode
            zipcode = settingsDict[setting]
        if setting == 'lineup':                             #Type of lineup to receive from the given zipcode. i.e. cable or OTA
            lineup = settingsDict[setting]
        if setting == 'lineupcode':                         #Lineup Code [string default==lineupid]
            lineupcode = settingsDict[setting]
        if setting == 'device':                             #Device name to be sent to gracenote website
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
            userLangid = {'0': 'en', '1': 'es', '2': 'fr'}.get(userLangid)
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
    logging.info('Running zap2epg-2.1.1 for zipcode: %s and lineup: %s', zipcode, lineup)
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
        if isConnectedtoTVH == True:
            response = tvh_getData('/api/channel/grid?all=1&limit=999999999&sort=name&filter=[{"type":"boolean","value":true,"field":"enabled"}]')
            if response.status_code == 200:
                logging.info('Accessing Tvheadend channel list from: %s', tvhurl)
                try:
                    channels = json.loads(response.content)
                    for ch in channels['entries']:
                        channelName = ch['name']
                        channelNum = ch['number']
                        tvhMatchDict[channelNum] = channelName
                    logging.info('%s Tvheadend channels found...', str(len(tvhMatchDict)))
                except:
                    logging.exception('Exception: tvhMatch - %s', f'Error parsing JSON response')
            else:
                logging.exception('Exception: tvhMatch - %s', f'Reqauest failed with status code {response.status_code}')
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

    def printHeader(fh, enc):           #This is the header for the XMLTV file
        logging.info('Creating xmltv.xml file...')
        fh.write(f'<?xml version=\"1.0\" encoding=\"{enc}\"?>\n')
        #fh.write("<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n\n")
        fh.write("<tv source-info-url=\"http://tvschedule.gracenote.com/\" source-info-name=\"gracenote.com\">\n")

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
                                        genreNewList = genreSort(edict, epgenre, useHex)
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

    def xmltv():            # Routine called after the data has been collected from gracenote website
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

    def parseStations(content):     #Routine downloads the necessary files from gracenote website.
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
                                    url = 'https://tvlistings.gracenote.com/api/program/overviewDetails'
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

    def connect_to_TVH():
        global isConnectedtoTVH 
        isConnectedtoTVH = True if tvh_connect(tvhurl, tvhport, usern, passw) is not None else False
    
    connect_to_TVH()
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
                    url = f"https://tvlistings.gracenote.com/api/grid?lineupId=&timespan=3&headendId={lineupcode}&country={country}&device={device}&postalCode={zipcode}&time={str(gridtime)}&pref=-&userId=-"
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
        counter = dict(sorted(Counter(countGenres()).items()))
        for cnt in counter:
            logging.info(cnt + ": " + str(counter[cnt]))        
        return timeRun, stationCount, episodeCount
    except Exception as e:
        logging.exception('Exception: main')

if __name__ == '__main__':
    userdata = os.getcwd()
    log = os.path.join(userdata, 'zap2epg.log')
    logging.basicConfig(filename=log, filemode='w', format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    mainRun(userdata)
