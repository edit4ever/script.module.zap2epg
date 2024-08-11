# zap2epg - Kodi addon (script.module.zap2epg)

zap2epg will generate an xmltv.xml file for USA/Canada TV lineups.*

zap2epg is originally designed to be easily setup in Kodi for use as a grabber for tvheadend. It includes the ability to setup your channel list to reduce the amount of data downloaded and speed up the grab. It has an option for downloading extra detail information for programs. (Note: this option will generate an extra http request per episode) It also has an option to append the extra detail information to the description (plot) field, which makes displaying this information in the Kodi EPG easier on many skins.

Setup:
1. Install the zap2epg addon in Kodi
2. Run the addon and setup your lineup
3. Configure your channel list (add channels to be downloaded)
4. You can run the program from the addon as a test - not necessary
5. Setup the zap2epg grabber in tvheadend
6. Enjoy your new EPG!

Language identification is accomplished through a python module 'LandId'.  This module does not have to be installed inside the Kodi interpreter but must be installed in on the device machine.
For debian based machines
1.  sudo apt-get update
2.  sudo apt-get install pip (if not already installed)
3.  sudo apt-get install python3-numpy
4.  pip install langid

If you try to install langid befoure installying numpy, you may get an error as the langid tries to install it but cannot find the required files.

The setting "Use Hex values for genre type instead of textual name" will use the hex values from http://www.etsi.org/deliver/etsi_en/300400_300499/300468/01.11.01_60/en_300468v011101p.pdf
Both Kodi and TVH use those categories as their genre groups.  Kodi understands and stores the genre information as a hex value.  As of now, I can't figure out how to get TVH to recognize the genre hex values.


* Note that zap2epg is a proof of concept and is for personal experimentation only. It is not meant to be used in a commercial product and its use is your own responsibiility.
