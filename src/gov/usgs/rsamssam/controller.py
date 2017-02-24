'''
Created on Feb 7, 2017

NOTE:  THIS CLASS MUST BE RUN IN THE MAIN THREAD.

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
        # set initial start time
        now = UTCDateTime()
        st = now - (now.timestamp % 600)      # To start from top of previous 10 minutes (e.g. XX:10, XX:20). May results in duplicate one minute data being written out.
        #st = now - (now.timestamp % 600)     # To start from top of previous minute
        # get station data
        data=station_id.split(":")
        station = data[0]
        channel = data[1]
        network = data[2]
        location = ""
        if len(data) > 3:
            location=data[3]
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
            'start_time': st,       # start time when querying data
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
                # Update table data
                self.config.ui.update_table(self.get_inventory())
                
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
                    st=self.station_data[station_id]['start_time']
                    et=st+60    # one min
                    # Check availability of data 
                    response = self.client.get_availability(network, station, location, channel)
                    if(len(response)==0 or response[-1][5] < et):    # if available end time is before desired end time, wait a bit and then check again
                        continue 
                    # Get station data from Wave Server
                    stream = self.client.get_waveforms(network, station, location, channel, st, et) 
                    if len(stream)==0 or stream[0].stats.npts==0:        # No data (e.g. tank gap, etc.)
                        print(network, station, channel, st, et, " Missing data (tank gap?)")
                        # update start time and end time
                        self.station_data[station_id]['start_time']=et  
                        continue
                    self.station_data[station_id]['stream'].append(stream)  
                    if self.config.print_stream:
                        print(stream)                    
                    station_config=self.config.stations[station_id]
                    # 1 min RSAM
                    if station_config[0]==1:      
                        if self.config.print_debug:
                            print(station_id, "Calculating 1 Min RSAM")
                        self.station_data[station_id]=rsam.process(stream, station_id, et, 60, self.config, self.station_data[station_id]) 
                    # 1 min SSAM
                    if station_config[2]==1: 
                        if self.config.print_debug:
                            print(station_id, "Calculating 1 Min SSAM")     
                        self.station_data[station_id]=ssam.process(stream, station_id, et, self.config, self.station_data[station_id]) 
                    # 10 min RSAM
                    if station_config[1]==1:  
                        if len(self.station_data[station_id]['stream'])==10:
                            if self.config.print_debug:
                                print(station_id, "Calculating 10 Min RSAM")
                            plot_stream=self.station_data[station_id]['stream']
                            stream10 = plot_stream[0]
                            #print(stream10)
                            if len(plot_stream) > 1:
                                for i in range(1, len(plot_stream) - 1):
                                    stream10 += plot_stream[i]
                                    #print(stream10)
                            stream10.merge(method=1)                        
                            self.station_data[station_id]=rsam.process(stream10, station_id, et, 600, self.config, self.station_data[station_id]) 
                            self.station_data[station_id]['stream']=[]  # reset
                          
                    # update start time and end time
                    self.station_data[station_id]['start_time']=et  

                    # add to stream list for plotting
                    plot_stream=self.station_data[station_id]['plot_stream']
                    if len(plot_stream) > 10:
                        plot_stream.pop(0)
                        plot_stream.append(stream)
                    else:
                        plot_stream.append(stream) 
                        
                    # For successful inventory query, reduce failed connection
                    if self.fails > 0:
                        self.fails -= 1
                    
                # Update station list
                self.config.stations=deepcopy(self.config.temp_stations)
                time.sleep(2)
            except (ConnectionError, ConnectionRefusedError, TimeoutError) as err:  
                self.handle_connection_error(err)         
             
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
