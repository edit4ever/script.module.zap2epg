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

import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import logging

connection_info = {}
isConnectedtoTVH = False
response = ""

def tvh_logsetup(filename, filemode, format, datefmt, level):
    logging.basicConfig(filename=filename, filemode=filemode, format=format, datefmt=datefmt, level=level)

def tvh_connect(ipaddress, port, usern, passw, tvh=None):

    connection_info.update({'ipaddress': ipaddress, 'port': port, 'user': usern, 'password': passw}) #save the connection settings
    global response

    def check_connection(ipaddress, port, string, firstRun: bool, useDigest):
        global response
        url = 'http://' + ipaddress + ':' + port + string
        if useDigest:
            auth = HTTPDigestAuth(usern, passw)
        else:
            auth = HTTPBasicAuth(usern, passw)
        connection_info.update({'auth': auth})

        try:
            response = requests.get(url,auth=auth)
            connection_info.update({"response": response})
            if useDigest:
                if response.status_code == 401:
                    # Wrong authorization type, possible?
                    logging.info( 'Trying with basic authorization')
                    check_connection(ipaddress, port, string, False, False)
        except:
            logging.info(f"The server {ipaddress} is unavailable")
            # Let's try to get the IP address, username and password for the TVH PVR 
            if firstRun:
                ipaddress = tvh['ipaddress']
                port = tvh['port']
                check_connection(ipaddress, port, string, False, useDigest)
                if response is not None:
                    connection_info.update({'ipaddress': ipaddress, 'port': port, 'response': response})
                    logging.info( f'The TVH PVR IP address is: {ipaddress} and port is: {port}.  Would you like to update this addon to use these values?')
                else:
                    logging.info( f'The TVH server IP address was not found or {ipaddress} is not correct.')    

            
    def raise_error(status_code):
        if status_code == 401 or status_code == 403:
            #dialog.ok("Tvheadend Access Error!",f"{status_code}: {tvh_url}\nAuthorization Denied\n\nPlease check your username/password in settings.")
            logging.info( f'{status_code} Authorization denied.')
        elif status_code != 200:
            #dialog.ok("Tvheadend Access Error!", f"{status_code}: {tvh_url}\nCould not connect to Tvheadend server.\nPlease check your Tvheadend server is running or check the IP and port configuration in the settings.")
            logging.info( f'{status_code} Problem with TVH Server')
    
    firstRun = False if tvh is None else True
    
    check_connection(ipaddress, port, '/api/status/connections', firstRun, True)
    if response is not None:
        global isConnectedtoTVH
        logging.info( response)
        if response.status_code != 200:
            isConnectedtoTVH = False
            raise_error(response.status_code)
            return None
        else:
            isConnectedtoTVH = True
            return connection_info
    else:
        logging.info( 'Nothing returned!')
        return None
    
def tvh_getData(string):
    if isConnectedtoTVH:
        url = 'http://' + connection_info['ipaddress'] + ':' + connection_info['port'] + string
        response = requests.get(url, auth=connection_info['auth'])
        logging.info( response)
        return response
    else:
        return None
    

#print(connect_TVH(ipaddress='192.168.52.148',port='9981',usern='osmc',passw='osmc',tvh={'ipaddress': '192.168.52.149', 'port': '9981', 'user': 'osmc', 'password': 'osmc'}))
#print(tvh_getData('/api/channel/grid?all=1&limit=999999999&sort=name'))