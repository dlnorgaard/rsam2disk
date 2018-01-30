'''
Created on Mar 31, 2017

@author: Diana
'''

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import sys

class ConfigUI(object):
    '''
    classdocs
    '''

    def __init__(self, config):
        '''
        Constructor
        '''
        self.config=config
        self.win=self.create_ui()
        self.win.wait_window(window=None)
        
    #===========================================================================
    # create_ui
    #===========================================================================
    def create_ui(self):
        root=tk.Tk()
        root.withdraw()
        #root.protocol("WM_DELETE_WINDOW", sys.exit())
        win=tk.Toplevel(master=root)
        win.title("Configuration Manager")
        
        # wave server host and port
        row=1
        tk.Label(win, text="Wave Server Host:").grid(row=row, column=1, padx=10, pady=10, sticky=tk.W) 
        self.primary_server=tk.StringVar();
        self.primary_server.set(self.config.primary_server)
        tk.Entry(win, textvariable=self.primary_server).grid(row=row, column=2, padx=10, pady=1, sticky=tk.W)   
        tk.Label(win, text="Port:").grid(row=row, column=3, padx=10, pady=1, sticky=tk.W) 
        self.primary_port=tk.IntVar();
        self.primary_port.set(self.config.primary_port)
        tk.Entry(win, textvariable=self.primary_port).grid(row=row, column=4, padx=10, pady=1, sticky=tk.W)   
          
        # RSAM output directory
        row += 1
        tk.Label(win, text="RSAM Output Directory:").grid(row=row, column=1, padx=10, pady=15, sticky=tk.E)
        self.rsam_directory=tk.StringVar()
        self.rsam_directory.set(self.config.rsam_directory)
        tk.Entry(win, textvariable=self.rsam_directory).grid(row=row, column=2, padx=10, pady=5, sticky=tk.W)
        tk.Button(win, text="...", command=lambda var=self.rsam_directory:self.choose_dir(var)).grid(row=row, column=3, pady=5, sticky=tk.W)
            
        # SSAM output directory
        row += 1
        tk.Label(win, text="SSAM Output Directory:").grid(row=row, column=1, padx=10, pady=15, sticky=tk.E)
        self.ssam_directory=tk.StringVar()
        self.ssam_directory.set(self.config.ssam_directory)
        tk.Entry(win, textvariable=self.ssam_directory).grid(row=row, column=2, padx=10, pady=5, sticky=tk.W)
        tk.Button(win, text="...", command=lambda var=self.ssam_directory:self.choose_dir(var)).grid(row=row, column=3, pady=5, sticky=tk.W)
        
        # Save button
        row += 1
        tk.Button(win, text="Save", width=10, command=self.save).grid(row=row, column=2, pady=10)
        
        return win
        
    #===========================================================================
    # choose_dir
    #===========================================================================
    def choose_dir(self, var):
        dirname=filedialog.askdirectory(initialdir=".", title="Select file", mustexist=True )
        if dirname:
            var.set(dirname)
            
    #===========================================================================
    # validate
    #===========================================================================
    def validate(self):
        if self.primary_server.get()=="":
            return False
        if self.primary_port.get()==0:
            return False
        if self.rsam_directory.get()=="":
            return False
        if self.ssam_directory.get()=="":
            return False      
        return True
    #===========================================================================
    # save
    #===========================================================================
    def save(self):
        if not self.validate():
            messagebox.showerror("Configuration Error", "All fields require entry.")
            return
        self.config.primary_server=self.primary_server.get()
        self.config.primary_port=self.primary_port.get()
        self.config.secondary_server=self.primary_server.get()
        self.config.secondary_port=self.primary_port.get()
        self.config.rsam_directory=self.rsam_directory.get()
        self.config.ssam_directory=self.ssam_directory.get()
        self.config.write(self.config.filename)
        self.config.loaded=True
        self.win.destroy()
                    