'''
Created on Mar 10, 2017

@author: Diana
'''
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import logging
from obspy.core.utcdatetime import UTCDateTime
import gov.usgs.rsamssam.rsam as rsam
import gov.usgs.rsamssam.ssam as ssam

class QueryWindow(object):
    '''
    classdocs
    '''
    dateformat="YYYY-mm-dd HH:MM"
    onvalue='on'
    offvalue='off'
    dirname=""
    fails=0                             # Keeps track of failed connections.
    retry=10                            # Number of retries after failed connections.
    
    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self, config, station_id, st, et):
        '''
        Constructor
        '''
        self.config=config
        self.client=config.controller.client
        self.station_id=station_id
        # break out station data
        self.station, self.channel, self.network, self.location=self.config.parse_station_id(self.station_id)
        self.win=self.create_ui(st, et)
        
    #===========================================================================
    # create_ui
    #===========================================================================
    def create_ui(self, default_st, default_et):
        win=tk.Toplevel(master=None)
        win.title(self.station_id)
        win.resizable(0, 0)
        
        # RSAM/SSAM options
        row=1
        self.rsam60=tk.StringVar()
        self.rsam60.set('on')
        tk.Checkbutton(win, text="1 Min RSAM", variable=self.rsam60, onvalue=self.onvalue, offvalue=self.offvalue).grid(row=row, column=1, padx=10, pady=5, sticky=tk.E)
        self.rsam600=tk.StringVar()
        self.rsam600.set('on')
        tk.Checkbutton(win, text="10 Min RSAM", variable=self.rsam600, onvalue=self.onvalue, offvalue=self.offvalue).grid(row=row, column=2, padx=10, pady=5)
        self.ssam60=tk.StringVar()
        self.ssam60.set('on')
        tk.Checkbutton(win, text="1 Min SSAM", variable=self.ssam60, onvalue=self.onvalue, offvalue=self.offvalue).grid(row=row, column=3, padx=10, pady=5, sticky=tk.W)
        
        # Time range
        row += 1
        tk.Label(win, text="From").grid(row=row, column=2, padx=10, pady=1, sticky=tk.W)
        tk.Label(win, text="To").grid(row=row, column=3, padx=10, pady=1, sticky=tk.W)
        row += 1
        tk.Label(win, text="Time Range:").grid(row=row, column=1, padx=10, pady=1, sticky=tk.E)
        self.st=tk.StringVar()
        self.st.set(default_st)
        tk.Entry(win, textvariable=self.st).grid(row=row, column=2, padx=10, pady=1, sticky=tk.W)
        self.et=tk.StringVar()
        self.et.set(default_et)
        tk.Entry(win, textvariable=self.et).grid(row=row, column=3, padx=10, pady=1, sticky=tk.W)
        
        # Output directory
        row += 1
        tk.Label(win, text="Output Directory:").grid(row=row, column=1, padx=10, pady=15, sticky=tk.E)
        self.dirname=tk.StringVar()
        tk.Entry(win, textvariable=self.dirname).grid(row=row, column=2, padx=10, pady=5, sticky=tk.W)
        tk.Button(win, text="...", command=self.open_dir_chooser).grid(row=row, column=3, pady=5, sticky=tk.W)
        
        # Go button
        row += 1
        tk.Button(win, text="Go", width=10, command=self.go).grid(row=row, column=2, pady=5)
        
        return win
        
    #===========================================================================
    # open_dir_chooser
    #===========================================================================
    def open_dir_chooser(self):
        dirname=filedialog.askdirectory(initialdir=".", title="Select file", mustexist=True )
        if dirname:
            self.dirname.set(dirname)
        
    #===========================================================================
    # go
    #===========================================================================
    def go(self): 
        self.win.config(cursor='wait')
        # Check at least one option is checked
        if self.rsam60.get()=='off' and self.rsam600.get()=='off' and self.ssam60.get()=='off':
            message="Please select at least one RSAM or SSAM option."
            messagebox.showerror("Invalid Options", message)
            return
                           
        # Validate output directories
        dirname=self.dirname.get()
        if dirname=="":
            message="Please choose an output directory."
            messagebox.showerror("Invalid Output Directory", message)
            return
            
        if not os.path.isdir(dirname):          
            message=dirname+" is not a valid directory"
            messagebox.showerror("Invalid Output Directory", message)
            return
        
        # Get start/end time
        start_time=UTCDateTime(self.st.get())
        end_time=UTCDateTime(self.et.get())
        
        # check availability
        response = self.client.get_availability(self.network, self.station, self.location, self.channel)
        if len(response)==0:
            self.fail+=1
            if self.fail >= self.retry:
                message="Lost connection: "+str(self.client)
                logging.error(message)
            return False
        if response[0][4] > start_time:
            start_time=response[0][4]
        if response[-1][5] < end_time:    
            end_time=response[-1][5]
            
        # one min
        st=start_time + (start_time.timestamp%60)
        if self.rsam60.get()=='on' or self.ssam60.get()=='on':
            missed_rsam_60=""
            missed_ssam_60=""
            while st < (end_time-60):    
                et=st+60   
                # Get station data from Wave Server
                stream = self.client.get_waveforms(self.network, self.station, self.location, self.channel, st, et) 
                if len(stream)==0 or stream[0].stats.npts==0:        # No data (e.g. tank gap, etc.)
                    message="%s %s %s %s %s %s %s"%(self.network, self.station, self.channel, self.location, st, et, " Missing data (tank gap?)")
                    logging.warning(message)
                    st += 60
                    continue
                
                # calculate RSAM
                if self.rsam60.get()=='on':
                    data=rsam.calculate(stream)                         
                    missed_rsam_60=rsam.write(data, self.station_id, et, 60, self.config, missed_rsam_60, dirname=dirname) 
                    
                # calculate SSAM
                if self.ssam60.get()=='on':
                    data=ssam.calculate(stream)
                    missed_ssam_60=ssam.write(data, self.station_id, et, self.config, missed_ssam_60, dirname=dirname)
                    
                st += 60
                if self.fails > 0:
                    self.fails -= 1  
                    
        # one min
        st=start_time + (start_time.timestamp%600)
        if self.rsam600.get()=='on':
            missed_rsam_600=""
            while st < (end_time-600):    
                et=st+600   
                # Get station data from Wave Server
                stream = self.client.get_waveforms(self.network, self.station, self.location, self.channel, st, et) 
                if len(stream)==0 or stream[0].stats.npts==0:        # No data (e.g. tank gap, etc.)
                    message="%s %s %s %s %s %s %s"%(self.network, self.station, self.channel, self.location, st, et, " Missing data (tank gap?)")
                    logging.warning(message)
                    st += 600
                    continue
                
                # calculate RSAM
                data=rsam.calculate(stream)      
                missed_rsam_600=rsam.write(data, self.station_id, et, 600, self.config, missed_rsam_600, dirname=dirname)                     
                    
                st += 600
                if self.fails > 0:
                    self.fails -= 1  
                    
        logging.info("Done with custom query for %s"%self.station_id)
        messagebox.showinfo("Custom Query", "Done!")
        self.win.config(cursor='')
        #self.win.destroy()