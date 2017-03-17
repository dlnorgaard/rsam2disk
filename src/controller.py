'''
Created on Feb 7, 2017
@author: dnorgaard
'''
import os, time
from copy import deepcopy
import rsam
import ssam
from obspy.clients.earthworm import Client
from obspy.core import UTCDateTime
from tkinter import messagebox
from threading import Thread
import logging

#===============================================================================
# Controller
#===============================================================================
class Controller(Thread):
    '''
    classdocs
    '''
    fails=0                             # Keeps track of failed connections.
    retry=10                            # Number of retries after failed connections.
    runFlag=True                        # Set to False to stop process
    
    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self, config):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.config=config      
        self.create_directories()
        self.set_connection(self.config.primary_server, self.config.primary_port)
        self.init_station_data()
        print("Controller Initialized")
        
    #===========================================================================
    # create_directories - Create top level directories where the 
    # output files will reside.
    #===========================================================================
    def create_directories(self):
        for t in self.config.rsam_time_frames:
            timedir=os.path.join(self.config.rsam_directory,str(t))
            os.makedirs(timedir, exist_ok=True)
        
        for t in self.config.ssam_time_frames:
            timedir=os.path.join(self.config.ssam_directory,str(t))
            os.makedirs(timedir, exist_ok=True)
            
    #===========================================================================
    # init_station_data
    #===========================================================================
    def init_station_data(self):     
        self.station_data={}   
        for station_id in self.config.stations.keys():
            self.station_data[station_id]=self.create_station_data(station_id)
            
    #===============================================================================
    # create_station_data - Initializes instances of each thread used to query a given
    # network/station/location/channel for a specified duration in earthworm
    # wave server.
    #===============================================================================            
    def create_station_data(self, station_id): 
        # get station data
#         data=station_id.split(":")
#         station = data[0]
#         channel = data[1]
#         network = data[2]
#         location = ""
#         if len(data) > 3:
#             location=data[3]
        station, channel, network, location=self.config.parse_station_id(station_id)
        
        # set initial start time
        now = UTCDateTime()
        st = now - (now.timestamp % 60)     # To start from top of previous minute
        st10 = now - (now.timestamp % 600)  # To start from top of previous 10 minutes (e.g. XX:10, XX:20).
                    
        # create station data
        station_data={
            'station': station,
            'channel': channel,
            'network': network,
            'location': location,
            'onemin': self.config.CHECKMARK,
            'onemin_missed': '',    # store previous 1 min rsam data if it could not be written to file
            'tenmin': self.config.CHECKMARK,
            'tenmin_missed': '',    # store previous 10 min rsam data if it could not be written to file
            'ssam_missed': '',      # store previous ssam data if it could not be written to file
            'start_time': st,       # start time when querying 1 min data
            'start_time10': st10,   # start time when queryign 10 min data
            'stream': [],           # used to calculate 10 minute RSAM
            'plot_stream': []       # used to display 10 minute plot
        }
        return station_data
            
    #===========================================================================
    # run
    #===========================================================================
    def run(self):
        while self.config.runFlag:
            try:
                # write to disk
                for station_id in self.config.stations.keys():    
                    if station_id not in self.station_data:
                        # Could be several reasons for this, e.g.:
                        # - Threading issue where station_data is temporarily out of sync with config.stations
                        # - Bad configuration entry of station that does not exist.
                        # - etc.
                        # Don't think there is a need to catch this.
                        continue    
                    network=self.station_data[station_id]['network']       
                    station=self.station_data[station_id]['station']    
                    location=self.station_data[station_id]['location'] 
                    channel=self.station_data[station_id]['channel']
                    station_config=self.config.stations[station_id]
                    
                    # 1 min rsam or ssam
                    if station_config[0]==1 or station_config[2]==1:   
                        self.process_one_min_data(station_id, station, network, location, channel, station_config)
                    # 10 min rsam
                    if station_config[1]==1:   
                        self.process_ten_min_data(station_id, station, network, location, channel, station_config)
                        
                # Update station list
                self.config.stations=deepcopy(self.config.temp_stations)
                time.sleep(2)
            except (ConnectionError, ConnectionRefusedError, TimeoutError) as err:  
                self.handle_connection_error(err)         
             
    
    #===========================================================================
    # process_one_min_data
    #===========================================================================
    def process_one_min_data(self, station_id, station, network, location, channel, station_config):
        st=self.station_data[station_id]['start_time']
        et=st+60    # one min
        if et > UTCDateTime().timestamp:    # if end time is after current time try again later
            return
        
        # Check availability of data 
        response = self.client.get_availability(network, station, location, channel)
        if(len(response)==0 or response[-1][5] < et):    # if available end time is before desired end time, wait a bit and then check again
            return  
        
        # Get station data from Wave Server
        stream = self.client.get_waveforms(network, station, location, channel, st, et) 
        if len(stream)==0 or stream[0].stats.npts==0:        # No data (e.g. tank gap, etc.)
            message="%s %s %s %s %s %s %s"%(self.network, self.station, self.channel, self.location, st, et, " Missing data (tank gap?)")
            logging.warning(message)
            # update start time and end time
            self.station_data[station_id]['start_time']=et  
            return
        self.station_data[station_id]['stream'].append(stream)  
        if self.config.print_stream:
            print(stream) 
            
        # 1 min RSAM
        if station_config[0]==1:               
            data=rsam.calculate(stream)     
            self.station_data[station_id]['onemin']="%d"%data[0]  
            self.station_data[station_id]['onemin_missed']=rsam.write(data, station_id, et, 60, self.config, self.station_data[station_id]['onemin_missed']) 
        # 1 min SSAM
        if station_config[2]==1: 
            data=ssam.calculate(stream)
            self.station_data[station_id]['ssam_missed']=ssam.write(data, station_id, et, self.config, self.station_data[station_id]['ssam_missed'])
         
        # update start time and end time
        self.station_data[station_id]['start_time']=et    
        
        # For successful inventory query, reduce failed connection
        if self.fails > 0:
            self.fails -= 1  
              
        # add to stream list for plotting
        plot_stream=self.station_data[station_id]['plot_stream']
        if len(plot_stream) > 10:
            plot_stream.pop(0)
            plot_stream.append(stream)
        else:
            plot_stream.append(stream) 
            
        
    #===========================================================================
    # process_one_min_data
    #===========================================================================
    def process_ten_min_data(self, station_id, station, network, location, channel, station_config):
        st=self.station_data[station_id]['start_time10']
        et=st+600    # ten min
        if et > UTCDateTime().timestamp:    # if end time is after current time try again later
            return
        
        # Check availability of data 
        response = self.client.get_availability(network, station, location, channel)
        if(len(response)==0 or response[-1][5] < et):    # if available end time is before desired end time, wait a bit and then check again
            return  
        # Get station data from Wave Server
        stream = self.client.get_waveforms(network, station, location, channel, st, et) 
        if len(stream)==0 or stream[0].stats.npts==0:        # No data (e.g. tank gap, etc.)
            message=network, station, channel, self.location, st, et, " Missing data (tank gap?)"
            logging.warning(message)
            # update start time and end time
            self.station_data[station_id]['start_time10']=et  
            return
        if self.config.print_stream:
            print(stream) 

        # 10 min RSAM        
        data=rsam.calculate(stream)       
        self.station_data[station_id]['tenmin']="%d"%data[0]  
        self.station_data[station_id]['tenmin_missed']=rsam.write(data, station_id, et, 600, self.config, self.station_data[station_id]['tenmin_missed'])

        # update start time and end time
        self.station_data[station_id]['start_time10']=et  
          
    #===========================================================================
    # get_inventory - Return WaveServer inventory
    #===========================================================================
    def get_inventory(self):
        try:
            inventory = self.client.get_availability(
                    self.config.inventory_filter['network'],
                    self.config.inventory_filter['station'],
                    self.config.inventory_filter['location'],
                    self.config.inventory_filter['channel'])
            return inventory
        except (ConnectionError, ConnectionRefusedError, TimeoutError) as err:  
            self.handle_connection_error(err)        
        except Exception as err:
            print(err)
               
    #===========================================================================
    # handle_connection_err
    #===========================================================================
    def handle_connection_error(self, err):
        print(err)
        self.fails += 1
        if self.fails <= self.retry:
            print("Retrying with alternate server.")
        else:
            message="Exceeded # of connection retries allowed."
            print(message)
            messagebox.showwarning("Error", message)
            self.config.runFlag=False
            self.fails=0
            return
        time.sleep(10)   # wait a bit before retrying connection
        # alternate attempts between primary and secondary servers
        if self.config.primary:
            self.set_connection(self.config.secondary_server, self.config.secondary_port)
            self.config.primary=False
        else:
            self.set_connection(self.config.primary_server, self.config.primary_port)
            self.config.primary=True
            
    #===========================================================================
    # set_connection
    #===========================================================================
    def set_connection(self, server, port):
        self.client=Client(server, port)  
        self.config.ui.root.title(self.config.name+" ["+server+":"+str(port)+"] "+ self.config.filename)
        print("Connection set to "+server+":"+str(port))