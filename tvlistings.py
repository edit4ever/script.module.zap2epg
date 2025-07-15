# TVtvlistings is a connection and grabber tool for gracenote servers
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
from urllib.request import HTTPDigestAuthHandler, build_opener
import base64
from logger import logger
import time

url = ""
opener = ""
isActivated = False
def create_opener(urlsite='https://tvlistings.gracenote.com'):
    global isActivated
    #Create the headers and other info to connect to the tvlistings.gracenote.com website
    headers = [ ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0"), 
        ("Accept", "application/json"), 
        ("Accept-Language", "en-US,en;q=0.9") ]
    global url, opener
    url = urlsite
    opener = urllib.request.build_opener()
    opener.addheaders = headers
    isActivated = True

def fetch_url(string, options):
    data = None                 #initialize variable
    if string == 'postal':      #default.py line 201
        substring = f"/gapzap_webapi/api/Providers/getPostalCodeProviders/{options['country']}/{options['zipcodeNew']}/gapzap/en"
    if string == 'lineup':      #default.py line 113, zap2epg.py line 768
        substring = f"/api/grid?lineupId=&timespan=3&headendId={options['lineupcode']}&country={options['country']}&device={options['device']}&postalCode={options['zipcode']}&time={options['gridtime']}&pref=-&userId=-"
    if string == 'programDetails':  #zap2epg line 566
        substring =  '/api/program/overviewDetails'
        data = options['data_encode']
    
    if not isActivated:
        create_opener()

    if isActivated: 
        try:
            combinedURL = url + substring

            if data is not None:
                if isinstance(data, str):
                    data = data.encode('utf-8')  # encode string to bytes
                with opener.open(combinedURL, data) as response:
                    return response.read()
            else:
                with opener.open(combinedURL) as response:
                    return response.read()

        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP Error: {e.code} - {e.reason}")
            if e.code == 429:   #Too Many Requests
                time.sleep(2)
        except urllib.error.URLError as e:
            logger.warning(f"URL Error: {e.reason}")
        except Exception as e:
            logger.warning(f"Error Type: {type(e).__name__}: {e}")

def returnSite():
    global url
    return url