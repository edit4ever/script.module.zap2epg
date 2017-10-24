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

import urllib2
import codecs
import time
import datetime
import gzip
import os
import logging
import re
import json
import sys
from os.path import dirname
import xml.etree.ElementTree as ET
try:
    from bs4 import BeautifulSoup
except ImportError:
    kodiPath = dirname(dirname(dirname(os.getcwd())))
    bs4Path = os.path.join(kodiPath, 'addons/script.module.beautifulsoup4/lib')
    sys.path.append(bs4Path)
    from bs4 import BeautifulSoup

stationList = []
def mainRun(userdata):
    global stationList
    try:
        settingsFile = os.path.join(userdata, 'settings.xml')
        settings = ET.parse(settingsFile)
        root = settings.getroot()
        settingsDict = {}
        xdescOrderDict = {}
        for setting in root.findall('setting'):
            settingStr = setting.get('value')
            settingID = setting.get('id')
            settingsDict[settingID] = settingStr
        for setting in settingsDict:
            if setting == 'slist':
                stationList = settingsDict[setting].split(",")
            if setting == 'zipcode':
                zipcode = settingsDict[setting]
            if setting == 'lineup':
                lineup = settingsDict[setting]
            if setting == 'lineupcode':
                lineupcode = settingsDict[setting]
            if setting == 'days':
                days = settingsDict[setting]
            if setting == 'xdetails':
                xdetails = settingsDict[setting]
            if setting == 'xdesc':
                xdesc = settingsDict[setting]
            if setting.startswith('desc'):
                xdescOrderDict[setting] = (settingsDict[setting])
        xdescOrder = [value for (key, value) in sorted(xdescOrderDict.items())]
        if zipcode == '' or lineupcode == '':
            logging.warn('No lineup configured - quitting zap2epg')
            print 'No lineup configured - please setup zap2epg location in Kodi'
            sys.exit(1)
    except Exception as e:
        logging.exception('Exception: Main settings - no lineup configured')
        print 'No lineup configured - please setup zap2epg location in Kodi'
        sys.exit(1)
    logging.info('Running zap2epg for zipcode: %s and lineup: %s', zipcode, lineup)
    pythonStartTime = time.time()
    cacheDir = os.path.join(userdata, 'cache')
    dayHours = int(days) * 8 # set to 8 when finished
    gridtimeStart = (int(time.mktime(time.strptime(str(datetime.datetime.now().replace(microsecond=0,second=0,minute=0)), '%Y-%m-%d %H:%M:%S'))))*1000
    schedule = {}

    def deleteOldCache(gridtimeStart):
        logging.info('Checking for old cache files...')
        try:
            if os.path.exists(cacheDir):
                entries = os.listdir(cacheDir)
                for entry in entries:
                    oldfile = entry.split('.')[0]
                    if oldfile.isdigit():
                        fn = os.path.join(cacheDir, entry)
                        if (int(oldfile) + 10800000) < gridtimeStart:
                            try:
                                os.remove(fn)
                                logging.info('Deleting old cache: %s', entry)
                            except OSError, e:
                                logging.warn('Error Deleting: %s - %s.' % (e.filename, e.strerror))
                    elif not oldfile.isdigit():
                        episodeSet = {j for i in schedule.values() for j in i}
                        episodeList = list(episodeSet)
                        fn = os.path.join(cacheDir, entry)
                        if oldfile not in episodeList:
                            try:
                                os.remove(fn)
                                logging.info('Deleting old cache: %s', entry)
                            except OSError, e:
                                logging.warn('Error Deleting: %s - %s.' % (e.filename, e.strerror))
        except Exception as e:
            logging.exception('Exception: deleteOldCache')

    def tget(episode, tag):
        text = episode.find(True,{'class':tag})
        if text is not None:
            success = text.get_text()
            success = re.sub('&','&amp;', success)
            return success
        else:
            return None

    def iget(episode, tag, match):
        icons = episode.find_all(True,{'class':tag})
        for icon in icons:
            if icon is not None:
                result = icon.get_text().strip()
                result = re.sub('\n','', result)
                result = re.sub(' +',' ', result)
                if match in result:
                    return result
        else:
            return None

    def convTime(t):
        return time.strftime("%Y%m%d%H%M%S",time.localtime(int(t)/1000))

    def savepage(fn, data):
        if not os.path.exists(cacheDir):
            os.mkdir(cacheDir)
        fileDir = os.path.join(cacheDir, fn)
        with gzip.open(fileDir,"wb+") as f:
            f.write(data)
            f.close()

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
            for station in schedule:
                fh.write('\t<channel id=\"' + station + '.zap2epg\">\n')
                if 'chnum' in schedule[station] and 'chfcc' in schedule[station]:
                    xchnum = schedule[station]['chnum']
                    xchfcc = schedule[station]['chfcc']
                    fh.write('\t\t<display-name>' + xchnum + ' ' + xchfcc + '</display-name>\n')
                    fh.write('\t\t<display-name>' + xchfcc + '</display-name>\n')
                    fh.write('\t\t<display-name>' + xchnum + '</display-name>\n')
                elif 'chfcc' in schedule[station]:
                    xchnum = schedule[station]['chfcc']
                    fh.write('\t\t<display-name>' + xcfcc + '</display-name>\n')
                elif 'chnum' in schedule[station]:
                    xchnum = schedule[station]['chnum']
                    fh.write('\t\t<display-name>' + xchnum + '</display-name>\n')
                fh.write("\t</channel>\n")
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
            for station in schedule:
                lang = 'en'
                sdict = schedule[station]
                for episode in sdict:
                    try:
                        edict = sdict[episode]
                        if 'epstart' in edict:
                            startTime = convTime(edict['epstart'])
                            is_dst = time.daylight and time.localtime().tm_isdst > 0
                            TZoffset = "%.2d%.2d" %(- (time.altzone if is_dst else time.timezone)/3600, 0)
                            stopTime = convTime(int(edict['epstart']) + (int(edict['eplength'])*60000))
                            fh.write('\t<programme start=\"' + startTime + ' ' + TZoffset + '\" stop=\"' + stopTime + ' ' + TZoffset + '\" channel=\"' + station + '.zap2epg' + '\">\n')
                            fh.write('\t\t<episode-num system=\"dd_progid\">' + episode + '</episode-num>\n')
                            if edict['epshow'] is not None:
                                fh.write('\t\t<title lang=\"' + lang + '\">' + edict['epshow'] + '</title>\n')
                            if edict['eptitle'] is not None:
                                fh.write('\t\t<sub-title lang=\"'+ lang + '\">' + edict['eptitle'] + '</sub-title>\n')
                            if xdesc is True:
                                xdescSort = addXDetails(edict)
                                fh.write('\t\t<desc lang=\"' + lang + '\">' + xdescSort + '</desc>\n')
                            if xdesc is False:
                                if edict['epdesc'] is not None and edict['epxdesc'] is None:
                                    fh.write('\t\t<desc lang=\"' + lang + '\">' + edict['epdesc'] + '</desc>\n')
                                if edict['epxdesc'] is not None:
                                    fh.write('\t\t<desc lang=\"' + lang + '\">' + edict['epxdesc'] + '</desc>\n')
                            if edict['epsn'] is not None or edict['epen'] is not None:
                                fh.write("\t\t<episode-num system=\"onscreen\">" + edict['epsn'] + edict['epen'] + "</episode-num>\n")
                            if edict['epyear'] is not None:
                                fh.write('\t\t<date>' + edict['epyear'] + '</date>\n')
                            if edict['epnew'] is None and edict['eplive'] is None:
                                fh.write("\t\t<previously-shown ")
                                if edict['epoad'] is not None:
                                    fh.write("start=\"" + edict['epoad'] + " " + TZoffset + "\"")
                                fh.write(" />\n")
                            if edict['epnew'] is not None:
                                fh.write("\t\t<new />\n")
                            if edict['eplive'] is not None:
                                fh.write("\t\t<live />\n")
                            if edict['epcc'] is not None:
                                fh.write("\t\t<subtitles type=\"teletext\" />\n")
                            if edict['eprating'] is not None:
                                fh.write('\t\t<rating>\n\t\t\t<value>' + edict['eprating'] + '</value>\n\t\t</rating>\n')
                            if edict['epstar'] is not None:
                                fh.write('\t\t<star-rating>\n\t\t\t<value>' + edict['epstar'] + '/4</value>\n\t\t</star-rating>\n')
                            if edict['epgenres'] is not None:
                                for genre in edict['epgenres']:
                                    fh.write("\t\t<category lang=\"" + lang + "\">" + genre + "</category>\n")
                            fh.write("\t</programme>\n")
                            episodeCount += 1
                    except:
                        logging.warn('No data for episode %s:', episode)
                        fn = os.path.join(cacheDir, episode + '.json')
                        os.remove(fn)
                        logging.info('Deleting episode %s:', episode)
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
        global stationList
        try:
            soup = BeautifulSoup(content, "html.parser")
            ch_guide = soup.find_all('table', {'class':'zc-row'})
            if stationList == ['']:
                logging.info('Channels not configured - adding all channels in lineup...')
#                stationListTemp = []
                for station in ch_guide:
                    skey = station.get('id')
                    schedule[skey] = {}
                    schedule[skey]['chnum'] = station.find('span', {'class':'zc-st-n'}).get_text('a')
                    schedule[skey]['chfcc'] = station.find('span', {'class':'zc-st-c'}).get_text('a')
                    stationList.append(skey)
#                stationList = ','.join(stationListTemp)
            else:
                for station in ch_guide:
                    skey = station.get('id')
                    if skey in stationList:
                        schedule[skey] = {}
                        schedule[skey]['chnum'] = station.find('span', {'class':'zc-st-n'}).get_text('a')
                        schedule[skey]['chfcc'] = station.find('span', {'class':'zc-st-c'}).get_text('a')
        except Exception as e:
            logging.exception("Exception: parseStations")

    def parseEpisodes(content):
        try:
            soup = BeautifulSoup(content, "html.parser")
            ch_guide = soup.find_all('table', {'class':'zc-row'})
            for station in ch_guide:
                skey = station.get('id')
                if skey in stationList:
                    episodes = station.find_all('td', {'class':'zc-pg'})
                    for episode in episodes:
                        epbase = episode.get('onclick')
                        epkey = epbase.split(',')[1].replace("'", "")
                        schedule[skey][epkey] = {}
                        schedule[skey][epkey]['epstart'] = epbase.split(',')[2].replace("'", "")
                        schedule[skey][epkey]['eplength'] = epbase.split(',')[3].replace(")", "")
                        schedule[skey][epkey]['epshow'] = tget(episode, 'zc-pg-t')
                        schedule[skey][epkey]['eptitle'] = tget(episode, 'zc-pg-e')
                        schedule[skey][epkey]['epdesc'] = tget(episode, 'zc-pg-d')
                        schedule[skey][epkey]['epyear'] = tget(episode, 'zc-pg-y')
                        schedule[skey][epkey]['eprating'] = iget(episode, 'zc-ic-tvratings', 'TV')
                        schedule[skey][epkey]['eplive'] = iget(episode, 'zc-ic-live', 'LIVE')
                        schedule[skey][epkey]['epcc'] = iget(episode, 'zc-ic-cc', 'CC')
                        schedule[skey][epkey]['epnew'] = iget(episode, 'zc-ic-ne', 'NEW')
                        schedule[skey][epkey]['epprem'] = iget(episode, 'zc-ic-premiere', 'PREMIERE')
                        schedule[skey][epkey]['epfin'] = iget(episode, 'zc-ic-finale', 'FINALE')
                        schedule[skey][epkey]['ephd'] = iget(episode, 'zc-ic', 'HD')
                        schedule[skey][epkey]['epxdesc'] = None
                        schedule[skey][epkey]['epsn'] = None
                        schedule[skey][epkey]['epen'] = None
                        schedule[skey][epkey]['epoad'] = None
                        schedule[skey][epkey]['epstar'] = None
                        schedule[skey][epkey]['epgenres'] = None
                        schedule[skey][epkey]['epcredits'] = None
        except Exception as e:
            logging.exception('Exception: parseEpisodes')

    def parseXdetails():
        try:
            for station in schedule:
                sdict = schedule[station]
                for episode in sdict:
                    try:
                        if not episode.startswith("ch"):
                            edict = sdict[episode]
                            filename = episode + '.json'
                            fileDir = os.path.join(cacheDir, filename)
                            if not os.path.exists(fileDir):
                                retry = 3
                                while retry > 0:
                                    logging.info('Downloading details data for: %s', episode)
                                    url = 'http://tvlistings.zap2it.com/tvlistings/gridDetailService?pgmId=' + episode
                                    try:
                                        contentLoad = urllib2.urlopen(url)
                                        content = contentLoad.read().decode('iso-8859-1')
                                        JSONcontent = re.sub(r'.* = ', '', content)
                                        if len(JSONcontent) > 100:
                                            with open(fileDir,"wb+") as f:
                                                f.write(JSONcontent)
                                                f.close()
                                            retry = 0
                                        else:
                                            time.sleep(1)
                                            retry -= 1
                                            logging.warn('Retry downloading missing details data for: %s', episode)
                                    except urllib2.URLError, e:
                                        time.sleep(1)
                                        retry -= 1
                                        logging.warn('Retry downloading details data for: %s - %s', episode, e)
                            if os.path.exists(fileDir):
                                fileSize = os.path.getsize(fileDir)
                                if fileSize > 0:
                                    with open(fileDir, 'rb') as f:
                                        EPdetails = json.loads(f.read())
                                        f.close()
                                    if 'program' in EPdetails:
                                        logging.info('Parsing %s', filename)
                                        Xprog = EPdetails['program']
                                        edict['epoad'] = Xprog.get('originalAirDate')
                                        edict['epsn'] = Xprog.get('seasonNumber')
                                        edict['epen'] = Xprog.get('episodeNumber')
                                        edict['epxdesc'] = Xprog.get('description')
                                        edict['epstar'] = Xprog.get('starRating')
                                        edict['epgenres'] = Xprog.get('genres')
                                        edict['epcredits'] = Xprog.get('credits')
                                    else:
                                        logging.warn('Could not parse data for: %s - deleting file', filename)
                                        os.remove(fileDir)
                                else:
                                    logging.warn('Could not parse data for: %s - deleting file', filename)
                                    os.remove(fileDir)
                            else:
                                logging.warn('Could not download details data for: %s - skipping episode', episode)
                    except:
                        logging.warn('Could not parse data for: %s - deleting file', filename)
                        os.remove(fileDir)
        except Exception as e:
            logging.exception('Exception: parseXdetails %s', filename)

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
            bullet = u"\u2022 "
            hyphen = u"\u2013 "
            newLine = "\n"
            space = " "
            colon = u"\u003A "
            vbar = u"\u007C "
            slash = u"\u2215 "
            comma = u"\u002C "

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
                        lastOption = int(opt)
                    elif thisOption and lastOption:
                        sortOrderList.append(thisOption)
                        lastOption = int(opt)
                    elif thisOption:
                        lastOption = int(opt)
                return sortOrderList

            if edict['epoad'] is not None:
                origDate = int(edict['epoad'])/1000
                finalDate = datetime.datetime.fromtimestamp(origDate).strftime('%B %d%% %Y')
                finalDate = re.sub('%', ',', finalDate)
                date = "First aired: " + finalDate + space
            if edict['epyear'] is not None:
                myear = "Released: " + edict['epyear'] + space
            if edict['eprating'] is not None:
                ratings = edict['eprating'] + space
            if edict['epnew'] is not None:
                new = edict['epnew'] + space
            if edict['eplive'] is not None:
                new = edict['eplive'] + space
            if edict['epprem'] is not None:
                new = edict['epprem'] + space
            if edict['epfin'] is not None:
                new = edict['epfin'] + space
            if edict['epcc'] is not None:
                cc = edict['epcc'] + space
            if edict['ephd'] is not None:
                hd = edict['ephd'] + space
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
                for g in edict['epcredits']:
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
            if edict['epdesc'] is not None and edict['epxdesc'] is None:
                plot = edict['epdesc'] + space
            if edict['epxdesc'] is not None:
                plot = edict['epxdesc'] + space

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
        while count < dayHours:
            params = "&lineupId=" + lineupcode + "&zipcode=" + zipcode
            filename = str(gridtime) + '.html.gz'
            fileDir = os.path.join(cacheDir, filename)
            if not os.path.exists(fileDir):
                try:
                    logging.info('Downloading guide data for: %s', str(gridtime))
                    url = 'http://tvlistings.zap2it.com/tvlistings/ZCGrid.do?isDescriptionOn=true&fromTimeInMillis=' + str(gridtime) + params + '&aid=tvschedule'
                    saveContent = urllib2.urlopen(url).read()
                    savepage(fileDir, saveContent)
                except:
                    logging.warn('Could not download guide data for: %s', str(gridtime))
            if os.path.exists(fileDir):
                with gzip.open(fileDir, 'rb') as f:
                    content = f.read()
                    f.close()
                logging.info('Parsing %s', filename)
                if count == 0:
                    parseStations(content)
                parseEpisodes(content)
            count += 1
            gridtime = gridtime + 10800000
        if xdetails == 'true':
            parseXdetails()
        xmltv()
        deleteOldCache(gridtimeStart)
        timeRun = round((time.time() - pythonStartTime),2)
        logging.info('zap2epg completed in %s seconds. ', timeRun)
        logging.info('%s Stations and %s Episodes written to xmltv.xml file.', str(stationCount), str(episodeCount))
        print (str(stationCount), ' Stations and ', str(episodeCount), 'Episodes written to xmltv.xml file.')
        return timeRun, stationCount, episodeCount
    except Exception as e:
        logging.exception('Exception: main')

if __name__ == '__main__':
    currentDir = os.getcwd()
    if os.name == 'nt':
        pattern = '^(.*?)Kodi'
    else:
        pattern = '^(.*?)kodi'
    splitDir = re.match(pattern, currentDir).group(0)
    userdata = os.path.join(splitDir, 'userdata', 'addon_data', 'script.module.zap2epg')
    log = os.path.join(userdata, 'zap2epg.log')
    logging.basicConfig(filename=log, filemode='w', format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    mainRun(userdata)
