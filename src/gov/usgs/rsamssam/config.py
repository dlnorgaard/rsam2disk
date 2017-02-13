'''
Created on Jan 24, 2017

This module reads and stores configuration information for the package.

@author: dnorgaard
'''
import json
from copy import deepcopy
from tkinter import messagebox

class Config(object):    
    
       
    CHECKMARK=u'\u2713'                 # Unicode character for check mark    
    name="RSAM/SSAM"
    
    # Configuration filename on load or save
    filename=""
    
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
    primary_port=16030
    
    secondary_server="pubavo1.wr.usgs.gov"
    secondary_port=16022
    
    # Output directories
    rsam_directory="E:\\Data\RSAM2017"
    ssam_directory="E:\\Data\SSAM2017"
        
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
    def __init__(self, filename):
        self.load(filename)
        print("Configuration initialized")

            
    #===========================================================================
    # load
    #===========================================================================
    def load(self, filename):
        try:
            self.filename=filename
            with open(filename) as json_data_file:
                data = json.load(json_data_file)
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
            #print(self)
    #         except FileNotFoundError:
    #             message=""
    #             if filename=="":
    #                 message="**No configuration filename specified."
    #             else:
    #                 message="**File not found: "+filename
    #             message+="\n**Using previous or system default configurations.\n**You may create a new configuration through the application."
    #             print(message)
            print("Loaded new configuration file "+ filename)
            return True
        except json.decoder.JSONDecodeError:
            message= "ERROR: Improperly formatted configuration file: "+ filename
            print(message)
            return False
        except KeyError as err:
            message= "ERROR: Missing configuration - "
            print(message, err)
            return False
        except Exception as err:
            print(err)
            return False
            
            
                    
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
            print(err)
            message="Unable to write to "+filename 
            message+="\nConfiguration not saved."
            messagebox.showinfo("Configuration",message)
            
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
        text+="\nInventory filter="+str(self.inventory_filter)
        text+="\nStation Settings={"
        for s in self.stations:
            text+="\n  "+str(s)+" "+str(self.stations[s])
        text+="\n}"
        return text
