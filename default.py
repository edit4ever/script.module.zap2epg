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
import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import os
from logger import createLogger, logger
from tvh import tvh_connect, tvh_getData
from tvlistings import create_opener, fetch_url
from xbmcswift2 import Plugin 
import re
import zap2epg
import urllib.request, urllib.error, urllib.parse
import json
from collections import OrderedDict
import time
import datetime

userdata = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
tvhoff = True if xbmcaddon.Addon().getSetting('tvhoff') == 'true' else False
if not os.path.exists(userdata):
    os.mkdir(userdata)
Clist = os.path.join(userdata, 'channels.json')
tvhList =  os.path.join(userdata, 'TVHchannels.json')
cacheDir = os.path.join(userdata, 'cache')
plugin = Plugin()
dialog = xbmcgui.Dialog()
gridtime = (int(time.mktime(time.strptime(str(datetime.datetime.now().replace(microsecond=0,second=0,minute=0)), '%Y-%m-%d %H:%M:%S'))))
connection = None
create_opener #create the connection to the EPG website

def connectTVH(updateSetting = False):
    #import web_pdb; web_pdb.set_trace()
    global tvhoff, connection, tvh_url
    if tvhoff is True:
        tvh_url = xbmcaddon.Addon().getSetting('tvhurl')
        tvh_port = xbmcaddon.Addon().getSetting('tvhport')
        tvh_usern = xbmcaddon.Addon().getSetting('usern')
        tvh_passw = xbmcaddon.Addon().getSetting('passw')
        tvh_digest = True if xbmcaddon.Addon().getSetting('digest') == 'true' else False

        connection = tvh_connect(tvh_url, tvh_port, tvh_usern, tvh_passw, tvh_digest)
        tvhoff = connection
        if tvhoff is False:
            dialog.ok("TVHeadend Server", f'The TVH server {tvh_url} was not found or username / password was incorrect.  Please check TVH settings')
            if updateSetting:
                connection = None
                tvhoff = False
                xbmcaddon.Addon().setSetting(id='tvhoff', value='false')

def getTVHChannels():
    #import web_pdb; web_pdb.set_trace()
    global tvhoff, connection
    if connection is None:
        connectTVH()
    if connection is not None:
        channels = tvh_getData('allchannels')  #returns a JSON string
        try:
            logger.info('Accessing Tvheadend channel list from: %s', tvh_url)
            #channels = response.json()
            with open(tvhList,"w") as f:
                json.dump(channels,f)
        except Exception as e:
            logger.warning(f"Error Type: {type(e).__name__}: {e}")
            tvhoff = False

def get_icon_path(icon_name):
    #import web_pdb; web_pdb.set_trace()
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'resources', 'img', icon_name+".png")

def create_cList(): #channel listings
    #import web_pdb; web_pdb.set_trace()
    tvhClist = []
    if tvhoff is True and not os.path.isfile(tvhList):
        getTVHChannels()
    if tvhoff is True:    
        with open(tvhList) as tvhData:
            tvhDict = json.load(tvhData)
            for ch in tvhDict['entries']:
                channelEnabled = ch['enabled']
                if channelEnabled == True:
                    tvhClist.append(ch['number'])
    lineupcode = xbmcaddon.Addon().getSetting('lineupcode')
    #url = 'http://tvlistings.gracenote.com/api/grid?lineupId=&timespan=3&headendId=' + lineupcode + '&country=' + country + '&device=' + device + '&postalCode=' + zipcode + '&time=' + str(gridtime) + '&pref=-&userId=-'
    options = {'lineupcode': lineupcode, 'country': country, 'device': device, 'zipcode': zipcode, 'gridtime': str(gridtime)}
    #content = urllib.request.urlopen(url).read()
    content = fetch_url('lineup', options)
    contentDict = json.loads(content)
    stationDict = {}
    if 'channels' in contentDict:
        for channel in contentDict['channels']:
            skey = channel.get('channelId')
            stationDict[skey] = {}
            stationDict[skey]['name'] = channel.get('callSign')
            stationDict[skey]['num'] = channel.get('channelNo')
            if channel.get('channelNo') in tvhClist:
                stationDict[skey]['include'] = 'True'
            else:
                stationDict[skey]['include'] = 'False'
    stationDictSort = OrderedDict(sorted(iter(stationDict.items()), key=lambda i: (float(i[1]['num']))))

    #Search the stations for duplicate channel numbers.  Get rid of the non 'DT' channel(s) if so.
    for station in stationDictSort:
        myStations = {k: v for k, v in stationDictSort.items() if v['num'] == stationDictSort[station]['num']}
        if len(myStations) > 1:
            for st in myStations:
                if myStations[st]['name'].find('DT') < 0:
                    stationDictSort[st]['include'] = 'False'
                    
    with open(Clist,"w") as f:
        json.dump(stationDictSort,f)

@plugin.route('/channels') #Menu item Configure Channel List
def channels():
   # import web_pdb; web_pdb.set_trace()
    lineupcode = xbmcaddon.Addon().getSetting('lineupcode')
    if lineup is None or zipcode is None:
        dialog.ok('Location not configured!', 'Please setup your location before configuring channels.')
    if not os.path.isfile(Clist):
        create_cList()
    else:
        newList = dialog.yesno('Existing Channel List Found', 'Would you like to download a new channel list or review your current list?', 'Review', 'Download')
        if newList:
            os.remove(Clist)
            create_cList()
    with open(Clist) as data:
        stationDict = json.load(data)
    stationDict = OrderedDict(sorted(iter(stationDict.items()), key=lambda i: (float(i[1]['num']))))
    stationCode = []
    stationListName = []
    stationListNum = []
    stationListInclude = []
    for station in stationDict:
        stationCode.append(station)
        stationListName.append(stationDict[station]['name'])
        stationListNum.append(stationDict[station]['num'])
        stationListInclude.append(stationDict[station]['include'])  
    stationPre = [i for i, x in enumerate(stationListInclude) if x == 'True']
    stationListFull = list(zip(stationListNum, stationListName))
    stationList = ["%s %s" % x for x in stationListFull]
    selCh = dialog.multiselect('Click to Select Channels to Include', stationList, preselect=stationPre)
    for station in stationDict:
        stationDict[station]['include'] = 'False'
    stationListCodes = []
    if selCh:
        for channel in selCh:
            skey = stationCode[channel]
            stationDict[skey]['include'] = 'True'
            stationListCodes.append(skey)
    with open(Clist,"w") as f:
        json.dump(stationDict,f)
    xbmcaddon.Addon().setSetting(id='slist', value=','.join(stationListCodes))

@plugin.route('/location') #Menu item: Change Current Location 
def location():
    #import web_pdb; web_pdb.set_trace()
    global country
    countryPick = ['USA', 'CAN']
    countryNew = dialog.select('Select your country', list=countryPick)
    if countryNew == 0:
        zipcodeNew = dialog.input('Enter your zipcode', defaultt=zipcode, type=xbmcgui.INPUT_NUMERIC)
    if countryNew == 1:
        zipcodeNew = dialog.input('Enter your zipcode', defaultt=zipcode, type=xbmcgui.INPUT_ALPHANUM)
    if not 'zipcodeNew' in vars() or 'zipcodeNew' in globals():
        return
    zipcodeNew = re.sub(' ', '', zipcodeNew)
    zipcodeNew = zipcodeNew.upper()
    xbmcaddon.Addon().setSetting(id='zipcode', value=zipcodeNew)

    if countryNew == 0:
        options = {'country': 'USA', 'zipcodeNew': zipcodeNew}
        #url = 'https://tvlistings.gracenote.com/gapzap_webapi/api/Providers/getPostalCodeProviders/USA/' + zipcodeNew + '/gapzap/en'
        lineupsN = ['AVAILABLE LINEUPS', 'TIMEZONE - Eastern', 'TIMEZONE - Central', 'TIMEZONE - Mountain', 'TIMEZONE - Pacific', 'TIMEZONE - Alaskan', 'TIMEZONE - Hawaiian']
        lineupsC = ['NONE', 'DFLTE', 'DFLTC', 'DFLTM', 'DFLTP', 'DFLTA', 'DFLTH']
        deviceX = ['-', '-', '-', '-', '-', '-', '-']
    if countryNew == 1:
        options = {'country': 'CAN', 'zipcodeNew': zipcodeNew}
        #url = 'https://tvlistings.gracenote.com/gapzap_webapi/api/Providers/getPostalCodeProviders/CAN/' + zipcodeNew + '/gapzap/en'
        lineupsN = ['AVAILABLE LINEUPS', 'TIMEZONE - Eastern', 'TIMEZONE - Central', 'TIMEZONE - Mountain', 'TIMEZONE - Pacific']
        lineupsC = ['NONE', 'DFLTEC', 'DFLTCC', 'DFLTMC', 'DFLTPC']
        deviceX = ['-', '-', '-', '-', '-']
    content = fetch_url('postal', options)
    if content is not None: 
        lineupDict = json.loads(content)
        if 'Providers' in lineupDict:
            for provider in lineupDict['Providers']:
                lineupName = provider.get('name')
                lineupLocation = provider.get('location')
                if lineupLocation != '':
                    lineupCombo = lineupName + '  (' + lineupLocation + ')'
                    lineupsN.append(lineupCombo)
                else:
                    lineupsN.append(lineupName)
                lineupsC.append(provider.get('headendId'))
                deviceGet = provider.get('device')
                if deviceGet == '' or deviceGet == ' ':
                    deviceGet = '-'
                deviceX.append(deviceGet)

        else:
            dialog.ok('Error - No Providers!', 'No providers were found - please check zipcode and try again.')
            return
        lineupSel = dialog.select('Select a lineup', list=lineupsN)
        if lineupSel:
            lineupSelCode = lineupsC[lineupSel]
            lineupSelName = lineupsN[lineupSel]
            deviceSel = deviceX[lineupSel]
            xbmcaddon.Addon().setSetting(id='lineupcode', value=lineupSelCode)
            xbmcaddon.Addon().setSetting(id='lineup', value=lineupSelName)
            xbmcaddon.Addon().setSetting(id='device', value=deviceSel)
            if os.path.exists(cacheDir):
                entries = os.listdir(cacheDir)
                for entry in entries:
                    oldfile = entry.split('.')[0]
                    if oldfile.isdigit():
                        fn = os.path.join(cacheDir, entry)
                        try:
                            os.remove(fn)
                        except:
                            pass
            xbmc.executebuiltin('Container.Refresh')
        else:
            xbmc.executebuiltin('Container.Refresh')
            return
    else:
        return    

@plugin.route('/run')  #Menu item:  Run zap2epg and Update Guide Data
def run():
    #import web_pdb; web_pdb.set_trace()
    status = zap2epg.mainRun(userdata)
    dialog.ok('zap2epg Finished!', 'zap2epg completed in ' + str(status[0]) + ' seconds.\n' + str(status[1]) + ' Stations and ' + str(status[2]) + ' Episodes written to xmltv.xml file.')

@plugin.route('/open_settings') #Menu item Configure Settings and Options
def open_settings():
    #import web_pdb; web_pdb.set_trace()
    plugin.open_settings() 
    global tvhoff, connection
    # Test the connection to TVH if tvhoff is true
    tvhoff = True if xbmcaddon.Addon().getSetting('tvhoff') == 'true' else False
    if tvhoff is True:
        connectTVH(True)
        try: 
            os.remove(tvhList) 
        except: 
            pass     
        if connection is not None:
            getTVHChannels()
        else:
            tvhoff = False
            xbmcaddon.Addon().setSetting(id='tvhoff', value='false')

@plugin.route('/')
def index():
    items = []
    items.append(
    {
        'label': 'Run zap2epg and Update Guide Data',
        'path': plugin.url_for('run'),
        'thumbnail':get_icon_path('run'),
    })
    items.append(
    {
        'label': 'Change Current Location | Zipcode: ' + zipcode + ' &  Lineup: ' + lineup,
        'path': plugin.url_for('location'),
        'thumbnail':get_icon_path('antenna'),
    })
    items.append(
    {
        'label': 'Configure Channel List',
        'path': plugin.url_for('channels'),
        'thumbnail':get_icon_path('channel'),
    })
    items.append(
    {
        'label': 'Configure Settings and Options',
        'path': plugin.url_for('open_settings'),
        'thumbnail':get_icon_path('settings'),
    })
    return items


if __name__ == '__main__':
    log = os.path.join(userdata, 'zap2epg.log')
    createLogger(log)
    logger.info("We have connected to the logging program!")
    try:
        zipcode = xbmcaddon.Addon().getSetting('zipcode')
        if zipcode.isdigit():
            country = 'USA'
        else:
            country = 'CAN'
        lineup = xbmcaddon.Addon().getSetting('lineup')
        device = xbmcaddon.Addon().getSetting('device')
        if zipcode == '' or lineup == '':
            zipConfig = dialog.yesno('No Lineup Configured!', 'You need to configure your lineup location before running zap2epg.\n\nWould you like to setup your lineup?')
            if zipConfig:
                location()
                xbmc.executebuiltin('Container.Refresh')
    except:
        dialog.ok('No Lineup Configured!', '', 'Please configure your zipcode and lineup under Change Current Location.')
    plugin.run()