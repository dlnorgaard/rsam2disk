'''
Created on Jan 24, 2017
This module reads and stores configuration information for the package.
@author: dnorgaard
'''
import json
import logging
import sys, os
from copy import deepcopy
from tkinter import messagebox
from config_ui import ConfigUI
#===============================================================================
# Config
#===============================================================================
class Config(object):    
    
    CHECKMARK=u'\u2713'                 # Unicode character for check mark    
    name="RSAM/SSAM"
    
    # Configuration filename on load or save
    filename='default-config.json'
    
    rsam_time_frames=[60, 600]
    ssam_time_frames=[60]
    
    ui=None
    controller=None
    
    runFlag=True
    print_stream=False
    print_data=False
    print_debug=False
    
##  Begin configurable items ##
    
    # WaveServer configurations 
    primary=True    # set to False when switching to secondary server
    primary_server="127.0.0.1"
    primary_port=16022
    
    secondary_server="pubavo1.wr.usgs.gov"
    secondary_port=16022
    
    # Output directories and filenames
    rsam_directory="RSAM"
    ssam_directory="SSAM"
    log_file="RsamSsam.log"
        
    # Limits inventory to check for and display in UI.
    # network, station, channel, location
    inventory_filter={
                    'network':'*',
                    'station':'*',
                    'channel':'*Z',
                    'location':'*'
                }
    
    # NOTE: station ids must be in format station:channel:network:location
    # The values indicate whether the following are enabled:
    # [ RSAM one minute, RSAM ten minute, SSAM one minute]
    # Leave location blank if not applicable.
    stations={
#         "FMW:EHZ:UW:": [1,1,1],
#         "LO2:EHZ:UW:": [1,0,1],
#         "OBSR:BHZ:CC:": [1,1,1],
#         "STAR:EHZ:UW:": [1,1,1]
    }
    
    temp_stations={}    # used to make it thread safe
    
    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self):
        self.load(self.filename)
        logging.info("Configuration initialized")

            
    #===========================================================================
    # load
    #===========================================================================
    def load(self, filename):
        try:
            self.filename=filename
            with open(filename) as json_data_file:
                data = json.load(json_data_file)
            self.log_file=data['log_file']
            if self.log_file=='':
                print('Please configure log_directory in '+filename)
                raise Exception("Missing configuration: log_directory")
            print("Logfile=",self.log_file)
            log_dir=os.path.dirname(self.log_file)
            os.makedirs(log_dir, exist_ok=True)
            logging.basicConfig(filename=self.log_file,level=logging.DEBUG)
            self.primary_server=data['primary_server']
            self.primary_port=data['primary_port']
            self.secondary_server=data['secondary_server']
            self.secondary_port=data['secondary_port']
            self.rsam_directory=data['rsam_directory']
            self.ssam_directory=data['ssam_directory']
            if bool(data['inventory_filter']):
                self.inventory_filter=data['inventory_filter']
            self.stations=data['stations']
            self.temp_stations=deepcopy(self.stations)
            logging.info("Loaded new configuration file "+ filename)
        except json.decoder.JSONDecodeError:
            message= "ERROR: Improperly formatted configuration file: "+ filename
            logging.error(message)
            print(message)
            ConfigUI(self);
        except KeyError as err:
            message= "ERROR: Missing configuration - "
            print(message, err)
            logging.exception(message)
            ConfigUI(self);
        except FileNotFoundError:
            print("default-config.json does not exist. Opening configuration manager.")
            ConfigUI(self);
        except Exception as err:
            print("Unexpected error: ", sys.exc_info()[0])
            logging.exception("Unexpected error: ")
            raise      
                   
    #===========================================================================
    # write
    #===========================================================================
    def write(self,filename):
        try:
            f=open(filename,'w')
            f.write(self.__str__())
            f.close()
            message="Configuration saved to "+filename+"."
            messagebox.showinfo("Configuration",message)
            self.filename=filename
        except Exception as err:
            logging.error(err)
            message="Unable to write to "+filename 
            message+="\nConfiguration not saved."
            messagebox.showinfo("Configuration",message)
            logging.error(message)
            
    #===========================================================================
    # __str__
    #===========================================================================
    def __str__(self):
        data={ 
            'primary_server': self.primary_server,
            'primary_port': self.primary_port,
            'secondary_server': self.secondary_server,
            'secondary_port': self.secondary_port,
            'rsam_directory': self.rsam_directory,
            'ssam_directory': self.ssam_directory,
            'log_file': self.log_file,
            'inventory_filter': self.inventory_filter,
            'stations': self.stations
            }
        return json.dumps(data, indent=4, sort_keys=True)
    
    #===========================================================================
    # pretty_print
    #===========================================================================
    def pretty_print(self):
        text="Primary Server="+self.primary_server+":"+str(self.primary_port)
        text+="\nSecondary Server="+self.secondary_server+":"+str(self.secondary_port)
        text+="\nRSAM output directory="+self.rsam_directory
        text+="\nSSAM output directory="+self.ssam_directory
        text+="\nLog file="+self.log_file
        text+="\nInventory filter="+str(self.inventory_filter)
        text+="\nStation Settings={"
        for s in self.stations:
            text+="\n  "+str(s)+" "+str(self.stations[s])
        text+="\n}"
        return text
    
    #===========================================================================
    # parse_station_id
    #===========================================================================
    def parse_station_id(self, station_id):
        data=station_id.split(":")
        station = data[0]
        channel = data[1]
        network = data[2]
        location = ""
        if len(data) > 3:
            location=data[3]
        return station, channel, network, location