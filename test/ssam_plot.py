'''
Created on Feb 17, 2017

@author: dnorgaard
'''

import gov.usgs.rsamssam.ssam as ssam
from tkinter import filedialog

filename=filedialog.askopenfilename(initialdir=".", title="Select SSAM file", multiple=True, filetypes = (("DAT files","*.dat"),("All files","*.*")) )
for f in filename:
    ssam.plot(f)