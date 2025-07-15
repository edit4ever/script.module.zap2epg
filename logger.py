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
 
import logging
import os
import shutil

#create a place holder so earlier function calls will still work before the logger is initialized.
logger = logging.getLogger("zap2epg")

def createLogger(log):
    global logger
    # Create a logger object
    try:
        if logger.hashandlers():
            return logger
    except:
        name, ext = os.path.splitext(log)
        old_file = f'{name}_old{ext}'
        if os.path.exists(log):
            if os.path.exists(old_file):
                os.remove(old_file)
            shutil.move(log, old_file)

        logger = logging.getLogger('zap2epg')
        logger.setLevel(logging.DEBUG)

        # Create a handler that writes to Kodi's log
        handler = logging.FileHandler(log, mode='w')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
        handler.setFormatter(formatter)
        
        # Avoid adding multiple handlers if already configured
        if not logger.hasHandlers():
            logger.addHandler(handler)

        logger.info("Logging started for zap2epg")

        return logger
