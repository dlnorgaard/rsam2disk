'''
Created on Feb 7, 2017

@author: dnorgaard
'''
import sys
from gov.usgs.rsamssam.ui import MainUI
from gov.usgs.rsamssam.controller import Controller
from gov.usgs.rsamssam.config import Config
      
config=Config('default-config.json') 
if config==False:
    sys.exit()
# set up UI
ui=MainUI(config)             
config.ui=ui
# set up controller
controller=Controller(config)   
config.controller=controller
# Start the UI and controller
controller.start()
#ui.update_table(controller.get_inventory())
ui.run()