# TVH is a connection and grabber tool for TVH servers
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

import urllib.request
from urllib.request import HTTPDigestAuthHandler, build_opener
from urllib.error import URLError, HTTPError
import base64
from logger import logger
import json

isConnectedtoTVH = False
hostname = ''
port = ''
username = ''
password = ''
useDigest = False


def tvh_connect(ipaddress, portNumber, usern, passw, userDigest=False, tvh=None ):

    #save the connection info to the global variables
    global hostname, port, username, password, useDigest, isConnectedtoTVH
    hostname = ipaddress
    port = portNumber
    username = usern
    password = passw
    useDigest = userDigest

    #make an initial attempt to connect to the server wiht line 49
    def check_connection():
        response = tvh_getData('connection') 
        if response is not None:
            return response
        else:
            return None

    response = check_connection()
    
    #read the response and respond
    if response is not None:
        isConnectedtoTVH = True
        logger.info("Connected to TVH server")
        return True       
    else:
        isConnectedtoTVH = False
        logger.info('Nothing returned!')
        return False
    
def tvh_getData(string):
    global isConnectedtoTVH
    def digest(url): #newer encryption style
        #header = [ ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0"), 
        #            ("Accept", "application/json"), 
        #            ("Accept-Language", "en-US,en;q=0.9") ]
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0", 
                    "Accept": "application/json", 
                     "Accept-Language": "en-US,en;q=0.9"} 
        
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        digest_auth_handler = HTTPDigestAuthHandler(password_mgr)
        #opener = build_opener(digest_auth_handler)
        #opener.addheaders = headers
        
        opener = urllib.request.build_opener(digest_auth_handler)
        request = urllib.request.Request(url, headers=headers)


        try:
            with opener.open(request, timeout=10) as response:
                raw = response.read().decode('utf-8')
                return json.loads(raw)
        except HTTPError as e:
            logger.info(f'Error: HTTP Error {e.code}: {e.reason}')
            if (e.reason == 401 or e.reason == 403):
                #dialog.ok("Tvheadend Access Error!",f"{e.reasone}: {url}\nAuthorization Denied\n\nPlease check your username/password in settings.")
                return None
        except URLError as e:
            logger.info(f'Error: URL Error: {e.reason}')
            if (e.reason != 200):
                #dialog.ok("Tvheadend Access Error!", f"{e.reason}: {url}\nCould not connect to Tvheadend server.\nPlease check your Tvheadend server is running or check the IP and port configuration in the settings.")
                return None
        except json.JSONDecodeError as e:
            logger.info(f'Error: JSON Decode Error: {e.msg}')
            return None
        except Exception as e:
            logger.warning("Exception in digest authentication - %s", e)        

    def basicAuth(url): #Older encryption style
        credentials = f"{username}:{password}"
        userpass_enc = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers_basic = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0", 
                            "Accept": "application/json", 
                            "Accept-Language": "en-US,en;q=0.9",
                            "Authorization": f"Basic {userpass_enc}"} 

        request = urllib.request.Request(url, headers=headers_basic)

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = response.read().decode('utf-8')
                return json.loads(raw)
        except HTTPError as e:
            logger.info(f'Error: HTTP Error {e.code}: {e.reason}')
            if (e.reason == 401 or e.reason == 403):
                #dialog.ok("Tvheadend Access Error!",f"{e.reasone}: {url}\nAuthorization Denied\n\nPlease check your username/password in settings.")
                return None
        except URLError as e:
            logger.info(f'Error: URL Error: {e.reason}')
            if (e.reason != 200):
                #dialog.ok("Tvheadend Access Error!", f"{e.reason}: {url}\nCould not connect to Tvheadend server.\nPlease check your Tvheadend server is running or check the IP and port configuration in the settings.")
                return None
        except json.JSONDecodeError as e:
            logger.info(f'Error: JSON Decode Error: {e.msg}')
            return None
        except Exception as e:
            logger.warning("Exception in basic authentication - %s", e)

    #Strings used to connect to TVH and pull station listings
    if string == 'connection':  #this py line 42
        isConnectedtoTVH = True 
        substring = '/api/status/connections'
    if string == 'channels':    #default.ph  line 97
        substring = '/api/channel/grid?all=1&limit=999999999&sort=name&filter=[{"type":"boolean","value":true,"field":"enabled"}]'
    if string == 'allchannels':
        substring = '/api/channel/grid?all=1&limit=999999999&sort=name'   

    if isConnectedtoTVH:
        url = f'http://{hostname}:{port}{substring}'
        if useDigest:
            data = digest(url)
        else:
            data = basicAuth(url)    
        return data
    else:
        return None