
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
import _strptime
import calendar
import gzip
import os
import logging
import re
import json
import sys
import html
from html import escape
from os.path import dirname
import xml.etree.ElementTree as ET
from collections import OrderedDict
import hashlib


def mainRun(userdata):
    settingsFile = os.path.join(userdata, 'settings.xml')
    settings = ET.parse(settingsFile)
    root = settings.getroot()
    settingsDict = {}
    xdescOrderDict = {}

#### Language support for Genres (and make it easier to add Genres)
    xLangGenres = { 
        "Lang_en" :  
                { "Level_2" :
                    {  "Movies" : "Movie / Drama",
                        "movie" : "Movie / Drama",
                        "Movie" : "Movie / Drama",
                        'News' : "News / Current affairs" ,
                        'Game show' : "Game show / Quiz / Contest",
                        'Law' : "Show / Game show",
                        'Culture' : "Arts / Culture (without music)",
                        'Art' :  "Arts / Culture (without music)",
                        'Entertainment' : "Popular culture / Traditional Arts",
                        'Politics'  :  "Social / Political issues / Economics",
                        'Social'  :  "Social / Political issues / Economics",
                        'Public affairs' :  "Social / Political issues / Economics",
                        'Education' : "Education / Science / Factual topics",
                        'How-to' : "Leisure hobbies",
                        'Travel' : "Tourism / Travel",
                        'Sitcom' : "Variety show",
                        'Talk' : "Talk show",
                        'Children' : "Children's / Youth programs",
                        'Animated' :  "Cartoons / Puppets",
                        'Music' : "Music / Ballet / Dance"
                   }  
                        ,
                "Level_1" :  
                    {  "Movies" : "Movie / Drama",
                        "movie" : "Movie / Drama",
                        "Movie" : "Movie / Drama",
                        'News' : "News / Current affairs",
                        'News magazine' : "News magazine",
                        'Public affairs' : "News / Current affairs",
                        'Interview' : "Discussion / Interview / Debate",
                        'Game show' : "Game show / Quiz / Contest",
                        'Talk' : "Talk show",
                        'Sports' : "Sports",
                        'sports' : "Sports",
                        'Sitcom' : "Variety show",
                        'Children' : "Children's / Youth programs"
                    },
                "Level_3" : 
                    {   "None" : "None"
                    } ,
                "Level_0" : 
                    {   "None" : "None"
                    }

                } ,
        "Lang_fr" :  
                {"Level_1" : 
                    {  "Movies" : "fr_1_Movies",
                        "movie" : "fr_1_movie",
                        "Movie" : "fr_1_Movie"
                    }  ,
                "Level_2" : 
                    {  "Movies"  : "fr_2_Movies",
                        "movie" : "fr_2_movie",
                        "Movie" : "fr_2_Movie"
                    },
                "Level_3" :
                    {   "None" : "None"
                    },
                "Level_0" : 
                    {   "None" : "None"
                    }
               }
       }

###  For finding Sports and determining Teams
    xCompetitionSports=['Football' ,
                        'Baseball'  ,
                        'Hockey', 
                        'Soccer' , 
                        'Tennis' , 
                        'Volleyball', 'Footvolley',
                        'Boxing',
                        'Auto racing', 
                        'Mixed martial arts' ]
    xSportsTeamSeparators=[' at ', ' vs. ']

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
    for setting in settingsDict:
        if setting == 'slist':
            stationList = settingsDict[setting]
        if setting == 'zipcode':
            zipcode = settingsDict[setting]
        if setting == 'lineup':
            lineup = settingsDict[setting]
        if setting == 'lineupcode':
            lineupcode = settingsDict[setting]
        if setting == 'device':
            device = settingsDict[setting]
        if setting == 'days':
            days = settingsDict[setting]
        if setting == 'redays':
            redays = settingsDict[setting]
        if setting == 'xdetails':
            xdetails = settingsDict[setting]
        if setting == 'xdesc':
            xdesc = settingsDict[setting]
        if setting == 'epicon':
            epicon = settingsDict[setting]
        if setting == 'epgenre':
            epgenre = settingsDict[setting]
        if setting == 'tvhoff':
            tvhoff = settingsDict[setting]
        if setting == 'tvhurl':
            tvhurl = settingsDict[setting]
        if setting == 'tvhport':
            tvhport = settingsDict[setting]
        if setting == 'usern':
            usern = settingsDict[setting]
        if setting == 'passw':
            passw = settingsDict[setting]
        if setting == 'chmatch':
            chmatch = settingsDict[setting]
        if setting == 'tvhmatch':
            tvhmatch = settingsDict[setting]
        if setting == 'stitle':
            stitle = settingsDict[setting]
        if setting.startswith('desc'):
            xdescOrderDict[setting] = (settingsDict[setting])
    xdescOrder = [value for (key, value) in sorted(xdescOrderDict.items())]
    if lineupcode != 'lineupId':
        chmatch = 'false'
        tvhmatch = 'false'
    if zipcode.isdigit():
        country = 'USA'
    else:
        country = 'CAN'

###  DEFAULTING this to "en" for now and should add it as a settings when the Genre table gets populated with other languages
    lang = 'en'

    logging.info('Running zap2epg-2.0.4 for zipcode: %s and lineup: %s', zipcode, lineup)
    pythonStartTime = time.time()
    cacheDir = os.path.join(userdata, 'cache')
    dayHours = int(days) * 8 # set back to 8 when done testing
    gridtimeStart = (int(time.mktime(time.strptime(str(datetime.datetime.now().replace(microsecond=0,second=0,minute=0)), '%Y-%m-%d %H:%M:%S'))))
    schedule = {}
    tvhMatchDict = {}

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

    def genreSort(EPfilter, EPgenre):
        genreList = []
        xEpgenre1_found = 0

        for g in EPgenre:
            if (g == 'Comedy') and (epgenre == '2'):
                    pass
            else :
                genreList.append(g)
        myLang = 'Lang_' + lang
        myLevel = "Level_" + str(epgenre)
        myGenDict = xLangGenres[myLang][myLevel]
        for g in myGenDict:
            if g in genreList :
                if epgenre == '1' : 
                    genreList.clear()
                    genreList.append (myGenDict[g])
                    xEpgenre1_found = 1 
                elif epgenre == '2' : 
                    genreList.insert(0,myGenDict[g])
                else:
                    pass
### And if it isn't one of the Level1 categories, then make it a default.
        if epgenre== '1' and xEpgenre1_found == 0 : 
            genreList = ["Variety show"]

        if 'Movie' in genreList:
            genreList.remove('Movie')
            genreList.insert(0, 'Movie')
        return genreList

    def printHeader(fh, enc):
        logging.info('Creating xmltv.xml file...')
        fh.write("<?xml version=\"1.0\" encoding=\""+ enc + "\"?>\n")
        fh.write("<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n\n")
        fh.write("<tv source-info-url=\"http://tvschedule.zap2it.com/\" source-info-name=\"zap2it.com\">\n")

    def printFooter(fh):
        fh.write("</tv>\n")

    def printStations(fh):
        global stationCount
        stationCount = 0
        try:
            logging.info('Writing Stations to xmltv.xml file...')
            try:
                scheduleSort = OrderedDict(sorted(iter(schedule.items()), key=lambda x: float(x[1]['chnum'])))
            except:
                logging.exception('Could not sort by chnum: %s ',  e)
                logging.info('exception ordering by chnum... sorting by chfcc')
                scheduleSort = OrderedDict(sorted(iter(schedule.items()), key=lambda x: x[1]['chfcc']))
            for station in scheduleSort:
                fh.write('\t<channel id=\"' + station + '.zap2epg\">\n')
                if 'chtvh' in scheduleSort[station] and scheduleSort[station]['chtvh'] is not None:
                    xchtvh = html.escape(scheduleSort[station]['chtvh'], quote=True )
                    fh.write('\t\t<display-name>' + xchtvh + '</display-name>\n')
                if 'chnum' in scheduleSort[station] and 'chfcc' in scheduleSort[station]:
                    xchnum = scheduleSort[station]['chnum']
                    xchfcc = scheduleSort[station]['chfcc']
                    fh.write('\t\t<display-name>' + xchnum + ' ' + html.escape(xchfcc, quote=True) + '</display-name>\n')
                    fh.write('\t\t<display-name>' + html.escape(xchfcc, quote=True) + '</display-name>\n')
                    fh.write('\t\t<display-name>' + xchnum + '</display-name>\n')
                elif 'chfcc' in scheduleSort[station]:
                    xchfcc = scheduleSort[station]['chfcc']
                    fh.write('\t\t<display-name>' + html.escape(xchfcc,quote=True) + '</display-name>\n')
                elif 'chnum' in scheduleSort[station]:
                    xchnum = scheduleSort[station]['chnum']
                    fh.write('\t\t<display-name>' + xchnum + '</display-name>\n')
                if 'chicon' in scheduleSort[station]:
                    fh.write("\t\t<icon src=\"http:" + scheduleSort[station]['chicon'] + "\" />\n")
                fh.write("\t</channel>\n")
                logging.info(station + ',' + xchnum + ' ' + html.escape(xchfcc, quote=True) )
                stationCount += 1
        except Exception as e:
            logging.exception('Exception: printStations')

    def printEpisodes(fh):
        global episodeCount
        episodeCount = 0
        try:
            logging.info('Writing Episodes to xmltv.xml file...')
            if xdesc is True:
                logging.info('Appending Xdetails to description for xmltv.xml file...')
            try:
                scheduleSort = OrderedDict(sorted(iter(schedule.items()), key=lambda x: float(x[1]['chnum'])))
            except:
                logging.exception('Could not sort by chnum: %s ',  e)
                logging.info('exception ordering by chnum... sorting by chfcc')
                scheduleSort = OrderedDict(sorted(iter(schedule.items()), key=lambda x: x[1]['chfcc']))

            for station in scheduleSort:
                sdict = scheduleSort[station]  
                for episode in sdict:
                    if not episode.startswith("ch"):
                        try:
                            edict = sdict[episode]
                            if 'epstart' in edict:
                                startTime = convTime(edict['epstart'])
                                is_dst = time.daylight and time.localtime().tm_isdst > 0
                                TZoffset = "%.2d%.2d" %(- (time.altzone if is_dst else time.timezone)/3600, 0)
                                stopTime = convTime(edict['epend'])
                                fh.write('\t<programme start=\"' + startTime + ' ' + TZoffset + '\" stop=\"' + stopTime + ' ' + TZoffset + '\" channel=\"' + station + '.zap2epg' + '\">\n')
                                dd_progid = edict['epid']
                                fh.write('\t\t<episode-num system=\"dd_progid\">' + dd_progid[:-4] + '.' + dd_progid[-4:] + '</episode-num>\n')
                                if edict['epshow'] is not None:
                                    fh.write('\t\t<title lang=\"' + lang + '\">' + html.escape(edict['epshow'], quote=True ) + '</title>\n')
                                if edict['eptitle'] is not None:
                                    showTitle = edict['eptitle']
                                    showTitle = showTitle.replace('\\\"','\"')
                                    fh.write('\t\t<sub-title lang=\"'+ lang + '\">' + html.escape(showTitle, quote=True ) + '</sub-title>\n')
                                if xdesc == 'true':
                                    xdescSort = addXDetails(edict)
                                    xdescSort = xdescSort.replace('\\\"','\"')
                                    fh.write('\t\t<desc lang=\"' + lang + '\">' + html.escape(xdescSort, quote=True ) + '</desc>\n')
                                if xdesc == 'false':
                                    if edict['epdesc'] is not None:
                                        xdescSort = edict['epdesc']
                                        xdescSort = xdescSort.replace('\\\"','\"')
                                        fh.write('\t\t<desc lang=\"' + lang + '\">' +  html.escape(xdescSort, quote=True ) + '</desc>\n')
                                if edict['epsn'] is not None and edict['epen'] is not None:
                                    fh.write("\t\t<episode-num system=\"onscreen\">" + 'S' + edict['epsn'].zfill(2) + 'E' + edict['epen'].zfill(2) + "</episode-num>\n")
                                    fh.write("\t\t<episode-num system=\"xmltv_ns\">" + str(int(edict['epsn'])-1) +  "." + str(int(edict['epen'])-1) + ".</episode-num>\n")
                                if edict['epyear'] is not None:
                                    fh.write('\t\t<date>' + edict['epyear'] + '</date>\n')
                                if not episode.startswith("MV"):
                                    if epicon == '1':
                                        if edict['epimage'] is not None and edict['epimage'] != '':
                                            fh.write('\t\t<icon src="https://zap2it.tmsimg.com/assets/' + edict['epimage'] + '.jpg" />\n')
                                        else:
                                            if edict['epthumb'] is not None and edict['epthumb'] != '':
                                                fh.write('\t\t<icon src="https://zap2it.tmsimg.com/assets/' + edict['epthumb'] + '.jpg" />\n')
                                    if epicon == '2':
                                        if edict['epthumb'] is not None and edict['epthumb'] != '':
                                            fh.write('\t\t<icon src="https://zap2it.tmsimg.com/assets/' + edict['epthumb'] + '.jpg" />\n')
                                if episode.startswith("MV"):
                                    if edict['epthumb'] is not None and edict['epthumb'] != '':
                                        fh.write('\t\t<icon src="https://zap2it.tmsimg.com/assets/' + edict['epthumb'] + '.jpg" />\n')
                                if not any(i in ['New', 'Live'] for i in edict['epflag']):
                                    fh.write("\t\t<previously-shown ")
                                    if edict['epoad'] is not None and int(edict['epoad']) > 0:
                                        fh.write("start=\"" + convTime(edict['epoad']) + " " + TZoffset + "\"")
                                    fh.write(" />\n")
                                if edict['epflag'] is not None:
                                    if 'New' in edict['epflag']:
                                        fh.write("\t\t<new />\n")
                                    if 'Live' in edict['epflag']:
                                        fh.write("\t\t<live />\n")
                                if edict['eprating'] is not None:
                                    fh.write('\t\t<rating>\n\t\t\t<value>' + edict['eprating'] + '</value>\n\t\t</rating>\n')
                                if edict['epstar'] is not None:
                                    fh.write('\t\t<star-rating>\n\t\t\t<value>' + edict['epstar'] + '/4</value>\n\t\t</star-rating>\n')
                                if epgenre != '0':
                                    if edict['epfilter'] is not None and edict['epgenres'] is not None:
                                        genreNewList = genreSort(edict['epfilter'], edict['epgenres'])
                                        for genre in genreNewList:
                                            fh.write("\t\t<category lang=\"" + lang + "\">" + genre + "</category>\n")
                                for this_sport in genreNewList:
                                    if this_sport in xCompetitionSports:
                                        fh.write("\t\t<sport lang=\"" + lang + "\">" + this_sport + "</sport>\n")
                                        for this_separator in xSportsTeamSeparators:
                                            if edict['eptitle'] is not None:
                                                xthisTitle = re.sub('&','&amp;', edict['eptitle'])
                                                xMyTeams = xthisTitle.split(this_separator)
                                                if len(xMyTeams) > 1:
                                                    fh.write("\t\t<team lang=\"" + lang + "\">" +  xMyTeams[0] +  "</team>\n")             
                                                    fh.write("\t\t<team lang=\"" + lang + "\">" +  xMyTeams[1] +  "</team>\n")
                                                    if 'Sports' not in genreNewList:
                                                        fh.write("\t\t<category lang=\"" + lang + "\">Sports</category>\n")
                                            
                                fh.write("\t</programme>\n")
                                episodeCount += 1
                        except Exception as e:
                            logging.exception('No data for episode %s:', episode)
                            #fn = os.path.join(cacheDir, episode + '.json')
                            #os.remove(fn)
                            #logging.info('Deleting episode %s:', episode)
        except Exception as e:
            logging.exception('Exception: printEpisodes')

    def xmltv():
        try:
            enc = 'utf-8'
            outFile = os.path.join(userdata, 'xmltv.xml')
            fh = codecs.open(outFile, 'w+b', encoding=enc)
            printHeader(fh, enc)
            printStations(fh)
            printEpisodes(fh)
            printFooter(fh)
            fh.close()
        except Exception as e:
            logging.exception('Exception: xmltv')

    def parseStations(content):
        try:
            ch_guide = json.loads(content)
            for station in ch_guide['channels']:
                skey = station.get('channelId')
                if stationList is None or skey in stationList:
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
                if stationList is None or skey in stationList:
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
        cacheDict = {}
        try:
            for station in schedule:
                sdict = schedule[station]
                for episode in sdict:
                    if not episode.startswith("ch"):
                        edict = sdict[episode]
                        EPseries = edict['epseries']
                        showList.append(edict['epseries'])
                        if EPseries not in cacheDict: 
                            logging.info('Adding series %s to cacheDict', EPseries)
                            filename = EPseries + '.json'
                            fileDir = os.path.join(cacheDir, filename)
                            cacheDict[EPseries] = {}
                            cacheDict[EPseries]['filename']= filename 
                            cacheDict[EPseries]['epcredits']= None
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
                                        cacheDict[EPseries]['epimage'] = EPdetails.get('seriesImage')
                                        cacheDict[EPseries]['epfan'] = EPdetails.get('backgroundImage')
                                        EPgenres = EPdetails.get('seriesGenres')
                                        if filename.startswith("MV"):
                                            cacheDict[EPseries]['epcredits'] = EPdetails['overviewTab'].get('cast')
                                            EPgenres = 'Movie|' + EPgenres
                                        cacheDict[EPseries]['epgenres'] = EPgenres.split('|')
                                        #edict['epstar'] = EPdetails.get('starRating')
                                        cacheDict[EPseries]['upcomingEpisodeTab'] = EPdetails['upcomingEpisodeTab']
                                        EPlist = cacheDict[EPseries]['upcomingEpisodeTab']
                                        EPid = edict['epid']
                                        for airing in EPlist:
                                            try: 
                                                if EPid.lower() == airing['tmsID'].lower():
                                                    if not episode.startswith("MV"):
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
                                            except Exception as e:
                                                logging.exception('Could not find OAD for %s in file ', EPseries )
                                    else:
                                        logging.warning('Could not parse data for file - size <= 0  : %s - deleting file', filename)
                                        os.remove(fileDir)
                                else:
                                    logging.warning('Could not download details data for: %s - skipping episode', EPseries)
                                    failList.append(EPseries)
                                    del cacheDict[EPseries]   # Delete from cache to indicate we failed.
                            except Exception as e:
                                logging.exception('Could not parse data for episode : %s - deleting file  -  %s', episode, e)
                            #os.remove(fileDir)
                        if EPseries in cacheDict:  # it won't if the download failed.   
                            edict['epimage'] = cacheDict[EPseries]['epimage']
                            edict['epfan'] = cacheDict[EPseries]['epfan']
                            if cacheDict[EPseries]['epcredits'] is not None:
                                edict['epcredits'] = cacheDict[EPseries]['epcredits']
                            edict['epgenres'] = cacheDict[EPseries]['epgenres']
                            EPlist = cacheDict[EPseries]['upcomingEpisodeTab']
                            EPid = edict['epid']
                            for airing in EPlist:
                                try: 
                                    if EPid.lower() == airing['tmsID'].lower():
                                        if not episode.startswith("MV"):
                                            try:
                                                origDate = airing.get('originalAirDate')
                                                if origDate != '':
                                                    EPoad = re.sub('Z', ':00Z', airing.get('originalAirDate'))
                                                    edict['epoad'] = str(calendar.timegm(time.strptime(EPoad, '%Y-%m-%dT%H:%M:%SZ')))
                                            except Exception as e:
                                                logging.exception('Could not parse oad for: %s - %s', episode, e)
                                except Exception as e:
                                    logging.exception(' Could not operate on OAD for %s ', EPseries )
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
                    1: bullet,
                    2: newLine,
                    3: hyphen,
                    4: space,
                    5: colon,
                    6: vbar,
                    7: slash,
                    8: comma,
                    9: plot,
                    10: new,
                    11: hd,
                    12: cc,
                    13: season,
                    14: ratings,
                    15: date,
                    16: prog,
                    17: epis,
                    18: episqts,
                    19: cast,
                    20: myear,
                }.get(opt, None)

            def cleanSortList(optList):
                cleanList=[]
                optLen = len(optList)
                for opt in optList:
                    thisOption = getSortName(int(opt))
                    if thisOption:
                        cleanList.append(int(opt))
                for item in reversed(cleanList):
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
                    logging.info('Downloading guide data for: %s (%s)', str(gridtime),datetime.datetime.fromtimestamp(gridtime).strftime('%Y-%m-%d %H:%M:%S'))
                    url = 'http://tvlistings.zap2it.com/api/grid?lineupId=&timespan=3&headendId=' + lineupcode + '&country=' + country + '&device=' + device + '&postalCode=' + zipcode + '&time=' + str(gridtime) + '&pref=-&userId=-'
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
    log = os.path.join(userdata, 'zap2epg_P3.log')
    logging.basicConfig(filename=log, filemode='w', format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    mainRun(userdata)
