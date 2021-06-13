# zap2epg - Kodi/TVH (TVheadEnd) TV Grabber addon

zap2epg will generate an xmltv.xml file for USA/Canada TV lineups.*

zap2epg is originally designed to be easily setup in Kodi for use as a grabber for tvheadend. It includes the ability to setup your channel list to reduce the amount of data downloaded and speed up the grab. It has an option for downloading extra detail information for programs. (Note: this option will generate an extra http request per episode) It also has an option to append the extra detail information to the description (plot) field, which makes displaying this information in the Kodi EPG easier on many skins.

## Raspberry Pi Kodi+TVH Setup:
1. Install the zap2epg addon in Kodi
2. Run the addon and setup your lineup
3. Configure your channel list (add channels to be downloaded)
4. You can run the program from the addon as a test - not necessary
5. Setup the zap2epg grabber in tvheadend
6. Enjoy your new EPG!

## Synology TVH server:
1. Install `tv_grab_zap2epg` script addon in `/usr/local/bin`
2. Install `zap2epg.xml` configuration file under tvheadend `epggrab/conf` directory such as `/var/packages/tvheadend/target/var/epggrab/conf`
3. Manually adjust `zap2epg.xml` parameters as needed.

## Configuration options (`zap2epg.xml`)
- `<setting id="zipcode">92101</setting>`: US Zip or Canada postal code
- `<setting id="lineupcode">lineupId</setting>`: 
- `<setting id="lineup">Local Over the Air Broadcast</setting>`: 
- `<setting id="device">-</setting>`: 
- `<setting id="days">1</setting>`: Number of TV guide days
- `<setting id="redays">1</setting>`: 
- `<setting id="slist"></setting>`: 
- `<setting id="stitle">false</setting>`: 
- `<setting id="xdetails">true</setting>`: Download extra Movie or Serie details
- `<setting id="xdesc">true</setting>`: Provide extra details to default TV show description
- `<setting id="epgenre">3</setting>`: 
- `<setting id="epicon">1</setting>`: 
- `<setting id="tvhoff">false</setting>`: 
- `<setting id="usern"></setting>`: Username to access TVH server
- `<setting id="passw"></setting>`: Password to access TVH server
- `<setting id="tvhurl">127.0.0.1</setting>`: IP address to TVH server
- `<setting id="tvhport">9981</setting>`: Port of TVH server
- `<setting id="tvhmatch">false</setting>`: 
- `<setting id="chmatch">true</setting>`: 

## `tv_grab_zap2epg`
zap2epg TV guide grabber script provides `baseline` capabilities (ref: http://wiki.xmltv.org/index.php/XmltvCapabilities):
- `--quiet`: Suppress all progress information. When --quiet is used, the grabber shall only print error-messages to stderr.
- `--output FILENAME`: Redirect the xmltv output to the specified file. Otherwise output goes to stdout along with a copy under `epggrab/cache/xmltv.xml`.
- `--days X`: Supply data for X days, limited to 14.
- `--offset X`: Start with data for day today plus X days. The default is 0, today; 1 means start from tomorrow, etc.
- `--config-file FILENAME`: The grabber shall read all configuration data from the specified file.  Otherwise uses default under `epggrab/conf/zap2epg.xml`
It also provide the following "extra" capabilities:
- `--zip` or `--postal` or `--code`: Allow can be used to pass US Zip or Canadian Postal code to be used by the grabber.



Note that zap2epg is a proof of concept and is for personal experimentation only. It is not meant to be used in a commercial product and its use is your own responsibiility.
