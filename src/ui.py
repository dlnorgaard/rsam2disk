'''
Created on Feb 7, 2017

@author: dnorgaard
'''
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from query_window import QueryWindow

#===============================================================================
# MainUI
#===============================================================================
class MainUI():
    '''
    classdocs
    '''
    # Constants
    date_format="%Y-%m-%d %H:%M"  
    EVENROW="evenrow"
    ODDROW="oddrow"
    MAXROWS=20                  # Maximum number of rows in table

    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self, config):
        '''
        Constructor
        '''
        self.config=config
        self.create_root()
        self.create_menu()
        self.create_table()
        self.create_infobar()
        print("UI initialized")
        
    #===========================================================================
    # run
    #===========================================================================
    def run(self):
        print("Starting UI...")
        self.refresh_table()
        self.root.mainloop()
        
    #===========================================================================
    # create_root
    #===========================================================================
    def create_root(self):
        root = tk.Tk()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.resizable(0, 0)
        root.title()
        root.after(1000)
        self.root=root
        
    #===========================================================================
    # create_table
    #===========================================================================
    def create_table(self):
        self.table=ttk.Treeview(self.root)
        self.table.bind("<Button-1>",self.on_click)         # single left click
        self.table.bind("<Button-3>", self.on_right_click)  # right click
        self.table.bind("<<Refresh>>", self.update_table)
        self.table['show']='headings'
        self.table['selectmode']='browse'
        self.table.tag_configure(self.EVENROW, background='#e8e6e6')
        self.table.tag_configure(self.ODDROW, background='white')
        # define column names, widths, etc.
        self.table['columns']=('station', 'st','et','onemin','tenmin','ssam')
        self.table.heading('station', text="Station")
        self.table.column('station', anchor='center', stretch=False, width='150')
        self.table.heading('st', text="Start")
        self.table.column('st', anchor='center', stretch=False, width='150')
        self.table.heading('et', text="End")
        self.table.column('et', anchor='center', stretch=False, width='150')
        self.table.heading('onemin', text="RSAM 1 Min")
        self.table.column('onemin', anchor='center', stretch=False, width='100')
        self.table.heading('tenmin', text="RSAM 10 Min")
        self.table.column('tenmin', anchor='center', stretch=False, width='100')
        self.table.heading('ssam', text="SSAM 1 Min")
        self.table.column('ssam', anchor='center', stretch=False, width='100')
        self.table.pack()
        
    #===========================================================================
    # create_infobar
    #===========================================================================
    def create_infobar(self):
        self.info=tk.Label(self.root,text="")
        self.info.pack(padx=5, anchor=tk.W)
        
    #===========================================================================
    # refresh_table
    #===========================================================================
    def refresh_table(self):
        self.update_table()
        self.root.after(15000, self.refresh_table)
        
    #===========================================================================
    # update_table
    #===========================================================================
    def update_table(self):
        #print("updating table")
        inventory=self.config.controller.get_inventory()
        if inventory is None:
            return
        for inv in inventory:
            network=inv[0]
            station=inv[1]
            location=inv[2]
            channel=inv[3]
            start_time=inv[4].strftime(self.date_format)
            end_time=inv[5].strftime(self.date_format)
            if location=="--":        # location
                location=""
            station_id="%s:%s:%s:%s"%(station, channel, network, location)  # network, station, channel, location
            onemin=""
            tenmin=""
            ssam=""     
            if station_id in self.config.temp_stations.keys():  
                data=self.config.controller.station_data[station_id]       
                if self.config.temp_stations[station_id][0]==1:  # One minute RSAM is enabled                    
                    onemin=data['onemin']
                if self.config.temp_stations[station_id][1]==1:  # Ten minute RSAM is enabled                    
                    tenmin=data['tenmin']           
                if self.config.temp_stations[station_id][2]==1:  # One minute SSAM is enabled                    
                    ssam=self.config.CHECKMARK 
            values=(station_id,start_time,end_time,onemin,tenmin, ssam)
            found=False
            for child in self.table.get_children():
                if child==station_id:
                    self.table.item(child, values=values)                
                    found=True
                    break
            if not found:
                numitems=len(self.table.get_children())
                if numitems%2==0:
                    tag=self.EVENROW
                else:
                    tag=self.ODDROW
                child=self.table.insert('','end',iid=station_id,values=values, tags=(tag))            
                if self.config.print_debug:
                    print("Added "+station_id)
                
        # Update table height and info bar       
        numdata=len(inventory)
        if numdata > self.MAXROWS:
            self.table['height']=self.MAXROWS
        else:
            self.table['height']=numdata
        self.table.pack(padx=5, pady=5)
        self.info.config(text="Number of stations: "+str(numdata))
        
        
    #===============================================================================
    # create_menu
    #===============================================================================
    def create_menu(self):
        menubar = tk.Menu(self.root)   
        # File Menu
        filemenu = tk.Menu(menubar)
        filemenu.add_command(label="Save", command=self.save, accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...", command=self.saveAs)
        filemenu.add_command(label="Load", command=self.load)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.close)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.bind_all("<Control-q>",self.save)
        
        # Configurations Menu
        configmenu=tk.Menu(self.root)
        configmenu.add_command(label='Show Configuration', command=self.show_config)
        configmenu.add_command(label='Edit Primary Server', command=lambda: self.set_server('Primary'))
        configmenu.add_command(label='Edit Secondary Server', command=lambda: self.set_server('Secondary'))
        menubar.add_cascade(label='Configurations', menu=configmenu)
        
        # Options Menu
        optmenu=tk.Menu(self.root)
        optmenu.add_checkbutton(label="Print Stream", command=self.print_stream)
        optmenu.add_checkbutton(label="Print Data", command=self.print_data)
        optmenu.add_checkbutton(label="Print Debug", command=self.print_debug)
        menubar.add_cascade(label="Options", menu=optmenu)
        
        # Help Menu
        helpmenu = tk.Menu(self.root)
        helpmenu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        
        self.root.config(menu=menubar)
                
    #===========================================================================
    # show_config
    #===========================================================================
    def show_config(self):
        messagebox.showinfo("Configuration", self.config.pretty_print())
        
    #===============================================================================
    # set_server
    #===============================================================================
    def set_server(self, primary_secondary):
        win=tk.Toplevel(self.root)
        win.geometry("250x150")
        win.title(primary_secondary)
        win.resizable(0, 0)
        # labels
        tk.Label(win, text="Server").grid(row=0, sticky=tk.W, padx=15, pady=5)
        tk.Label(win, text="Port").grid(row=1, sticky=tk.W, padx=15, pady=5)
        # textfields
        server=tk.StringVar()
        if primary_secondary=="Primary":
            server.set(self.config.primary_server)
        else:
            server.set(self.config.secondary_server)
        tk.Entry(win, textvariable=server).grid(row=0, column=1, padx=15, pady=5)
        port=tk.IntVar()
        if primary_secondary=="Primary":
            port.set(self.config.primary_port)
        else:
            port.set(self.config.secondary_port)
        tk.Entry(win, textvariable=port).grid(row=1, column=1, padx=15, pady=5)
        # buttons
        tk.Button(win, text='Set', width=15, command=lambda load=False: self.update_server(win, server, port, primary_secondary,load)).grid(row=2, column=1, pady=5)
        tk.Button(win, text='Set and Load', width=15, command=lambda load=True: self.update_server(win, server, port, primary_secondary,load)).grid(row=3, column=1, pady=5)
        
    #===============================================================================
    # update_server
    #===============================================================================
    def update_server(self, win, server, port, primary_secondary, load):
        if(primary_secondary=='Primary'):
            self.config.primary_server=server.get()
            self.config.primary_port=port.get()
        else:
            self.config.secondary_server=server.get()
            self.config.secondary_port=port.get()
        if load:
            self.reload(server.get(),port.get(), primary_secondary) 
        win.destroy()
        
    #===============================================================================
    # print_stream - If enabled, will write to stdout data on streams received.
    #===============================================================================
    def print_stream(self):
        if self.config.print_stream==False:
            self.config.print_stream=True
        else:
            self.config.print_stream=False
            
    #===============================================================================
    # print_data - If enabled, will write to stdout the contents written to disk.
    #===============================================================================
    def print_data(self):
        if self.config.print_data==False:
            self.config.print_data=True
        else:
            self.config.print_data=False
             
    #===============================================================================
    # print_data - If enabled, will write to stdout the contents written to disk.
    #===============================================================================
    def print_debug(self):
        if self.config.print_debug==False:
            self.config.print_debug=True
        else:
            self.config.print_debug=False           
    #===============================================================================
    # about
    #===============================================================================
    def about(self):
        info="RSAM/SSAM 3/31/2017"
        info+="\ndnorgaard@usgs.gov"
        messagebox.showinfo("About", info)
        
    #===============================================================================
    # save - Save configuration to file.
    #===============================================================================
    def save(self):
        if self.config.filename=="":
            self.saveAs()
        else:
            self.config.write(self.config.filename)
        
    #===============================================================================
    # save - Save configuration to a specific file.
    #===============================================================================
    def saveAs(self):
        #filename=filedialog.asksaveasfilename(initialdir=self.config.file_directory, title="Select file", filetypes = (("JSON files","*.json"),("Text files","*.txt"),("All files","*.*")) )
        filename=filedialog.asksaveasfilename(initialdir=".", title="Select file", filetypes = (("JSON files","*.json"),("Text files","*.txt"),("All files","*.*")) )
        if filename:
            self.config.write(filename)
    
        
    #===============================================================================
    # load - Load configuration file.
    #===============================================================================
    def load(self):
        filename=filedialog.askopenfilename(initialdir=".", title="Select file", filetypes = (("JSON files","*.json"),("Text files","*.txt"),("All files","*.*")) )
        if filename:
            result=self.config.load(filename)
            if result:
                self.reload(self.config.primary_server, self.config.primary_port, True)
            else:
                messagebox.showerror("Error", "Problem loading "+filename)
            
    #===============================================================================
    # reload - 
    #===============================================================================
    def reload(self, server, port, primary_secondary):
        self.config.primary=primary_secondary
        self.config.controller.set_connection(server, port)
        self.config.controller.init_station_data()
        self.table.delete(*self.table.get_children())
        self.update_table()           
        
    #===============================================================================
    # close
    #===============================================================================
    def close(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.config.runFlag=False
            self.root.destroy()
            
    #===========================================================================
    # plot
    #===========================================================================
    def plot(self, station_id, spectrogram=False):
        if station_id not in self.config.stations:  # Not configured to get data
            message="Station is not configured to collect one minute data."
            messagebox.showwarning(station_id, message)
#         if not station_id in self.config.controller.station_data:
#             message="Station is not configured to collect one minute data."
#             messagebox.showwarning(station_id, message)
        if self.config.controller.station_data[station_id]['onemin']==self.config.CHECKMARK:   # Don't have one minute data yet
            message="One minute data for the station is not yet available."
            messagebox.showwarning(station_id, message)
            return
        plot_stream=self.config.controller.station_data[station_id]['plot_stream']
        if len(plot_stream)==0:
            return
        stream = plot_stream[0] # only do 1 min for now
        filename=station_id+".png"            
        filename=filename.replace(":","_")
        filename=os.path.join(self.config.rsam_directory,filename)
        if spectrogram:
            title="Spectrogram"
            imgtitle=station_id+"\n"+stream[0].stats.starttime.strftime(self.date_format)+" to "+stream[-1].stats.endtime.strftime(self.date_format)
            stream.spectrogram(outfile=filename, title=imgtitle)
        else:
            title="Waveform"
            stream.plot(outfile=filename)
        win=tk.Toplevel(self.root)
        win.title(title)
        win.resizable(0, 0)
        image=Image.open(filename)
        photo=ImageTk.PhotoImage(image)
        label=tk.Label(win, image=photo)
        label.image=photo
        label.pack()
        # clean up
        if os.path.isfile(filename):
            os.remove(filename)
        
    #===========================================================================
    # open_query_window
    #===========================================================================
    def open_query_window(self, config, station_id, st, et):
        QueryWindow(config, station_id, st, et)      
        
    #===========================================================================
    # on_righ_click - Open right click menu
    #===========================================================================
    def on_right_click(self, event):
        station_id = self.table.identify_row(event.y)
        if station_id == "":        # Not clicked on a station
            return
        item=self.table.item(station_id)   
        #print(item)
        st=item['values'][1]
        et=item['values'][2]
        popup=tk.Menu(self.root, tearoff=0)
        popup.add_command(label="Query Custom Time Range", command=lambda x=self.config:self.open_query_window(x,station_id, st, et))
        popup.add_command(label="Plot Waveform", command=lambda x=station_id:self.plot(x, spectrogram=False))
        popup.add_command(label="Plot Spectrogram", command=lambda x=station_id:self.plot(x, spectrogram=True))
        popup.post(event.x_root, event.y_root)
    
    #===========================================================================
    # on_click - When column 4, 5, 6 are clicked
    #===========================================================================
    def on_click(self, event):
        station_id = self.table.identify_row(event.y)
        if station_id == "":
            return
        column=self.table.identify_column(event.x)

        if column=="#4":        # RSAM 1 min
            idx=0
        elif column=="#5":      # RSAM 10 min
            idx=1
        elif column=="#6":      # SSAM 1 min
            idx=2
        else:
            return
       
        temp_stations=self.config.temp_stations
        if station_id not in temp_stations.keys():
            # Add station info to configuration if nothing was enabled
            self.config.controller.station_data[station_id]=self.config.controller.create_station_data(station_id)
            temp_stations[station_id]=[0,0,0]
            temp_stations[station_id][idx]=1
            print(station_id+" added", temp_stations[station_id])
        else: 
            # Module for station already exists and is running.  Update.
            station_config=temp_stations[station_id]
            if station_config[idx]==1: 
                station_config[idx]=0   # turn off
                if station_config==[0,0,0]: 
                    # Nothing enabled so remove module and config entry
                    temp_stations.pop(station_id, None)
                    del self.config.controller.station_data[station_id]
                    #self.config.controller.station_data.remove(station_id)  
                    print(station_id+" stopped")
                else:
                    if station_config[0]==0:
                        self.config.controller.station_data[station_id]['onemin']=self.config.CHECKMARK                    
                    if station_config[1]==0:
                        self.config.controller.station_data[station_id]['tenmin']=self.config.CHECKMARK
                    print(station_id+" updated "+ str(station_config))
            else:
                station_config[idx]=1
                print(station_id+" updated "+ str(station_config))
                
        #self.config.temp_stations=temp_stations
        self.update_table()  