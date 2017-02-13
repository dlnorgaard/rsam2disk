'''
Created on Feb 6, 2017

@author: dnorgaard
'''
import numpy as np
import os

filename_format="%s_%d%02d%02d_%s_%d.csv"
date_format="%d-%b-%Y %H:%M:%S"

#===============================================================================
# process- Calculate RSAM and write to file.  Return updated station data
#            if successful.
#===============================================================================
def process(stream, station_id, et, duration, config, station_data):
    data=calculate(stream)       
    missed=''
    if duration==60:
        missed=station_data['onemin_missed']
    if duration==600:
        missed=station_data['tenmin_missed']
    text=write(data, station_id, et, duration, config, missed) 
    if duration==60:
        station_data['onemin']="%d"%data[0]
        station_data['onemin_missed']=text
    if duration==600:
        station_data['tenmin']="%d"%data[0]
        station_data['tenmin_missed']=text                   
    return station_data

#===============================================================================
# calculate_rsam - Calculates:
# rsam - RSAM, or time-averaged amplitude for given stream
# max - Maximum amplitude
# min - Minimu amplitude
# npts - Number of points in stream
# dcbias - Estimated DC offset
# Returns array [ rsam, max, min, npts, dcbias ]
#===============================================================================
def calculate(stream):
    smax = 0  # Max amplitude in stream
    ssum = 0  # Sum of valid values before rectifying
    smin = 0  # Min amplitude in stream
    npts = 0  # Number of (valid) values in stream
    # loop through once to approximate DC bias
    for trace in stream:
        data=trace.data
        if np.ma.is_masked(data):
            data=trace.data.compressed()   # returns only the valid entries 
        smax = max(data.max(), smax)
        smin = min(data.min(), smin)
        ssum += data.sum()
        npts += data.size
    dcbias = ssum / npts  # Use this as DC bias for now
    
    # It will error here if there the trace data is a masked array
    # and code above hasn't been fixed to handle it.  I think it has, 
    # but will leave this in longer to be sure.
    try:
        test="%d"%dcbias
    except:     
        print(stream)
        print("ssum",ssum)
        print("npts",npts)
        print(dcbias)
        raise
    
    # loop through again to rectify the data
    ssum = 0  # Now calculate sum of amplitudes with rectified data
    for trace in stream:
        data=trace.data
        if np.ma.is_masked(data):
            data=trace.data.compressed()   # returns only the valid entries 
        bias_array = np.empty(data.size)
        bias_array.fill(dcbias)  # create array of same size as trace data with dcbias as value
        rectified = np.where(np.less(data, bias_array), 2 * bias_array - data, data)
        ssum += sum(rectified)
    rsam = (ssum / npts) - dcbias
    return [rsam, smax, smin, npts, dcbias]

#===============================================================================
# write - write RSAM to file
#===============================================================================
def write(data, station_id, et, duration, config, missed):  
    text=missed+"%s, %d, %d, %d, %d, %d"%(et.strftime(date_format), data[0], data[1], data[2], data[3], data[4])
    if config.print_data or config.print_debug:
        print(station_id+"     "+text)
    try: 
        station=station_id.replace(":","_")
        filename = filename_format%("RSAM", et.year, et.month, et.day, station, duration)
        subdir=os.path.join(config.rsam_directory, str(duration))
        full_filename = os.path.join(subdir, filename)
        f = open(full_filename,"a")
        f.write(text+"\n")
        f.close() 
    except Exception:
        return text + "\n"  
    return ""    
