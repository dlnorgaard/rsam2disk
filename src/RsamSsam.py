'''
Created on Feb 7, 2017

@author: dnorgaard
'''

from ui import MainUI
from controller import Controller
from config import Config
      
config=Config('default-config.json') 
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