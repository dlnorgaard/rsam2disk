'''
Created on Feb 6, 2017

@author: dnorgaard
'''
import os
import math as M
import numpy as np
from matplotlib import mlab
        

filename_format="%s_%d%02d%02d_%s_%d.dat"
date_format="%d-%b-%Y %H:%M"
bands=[0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 8, 10, 15, 20 ]

#===============================================================================
# process - calculate SSAM and write to file
#===============================================================================
def process(stream, station_id, et, config, station_data):  
    stream.merge(method=1)  
    data=np.array([])  
    for tr in stream:
        data=np.append(data, tr.data)
    freq, specgram, time = spectrogram(data, stream[0].stats.sampling_rate)
    ssam=calculate_custom(specgram, freq)
    #ssam=calculate(specgram)
    missed=station_data['ssam_missed']
    station_data['ssam_missed']=write(ssam, station_id, et, config, missed)
    return station_data  

#===============================================================================
# calculate
#===============================================================================
def calculate(specgram):
    ssam=[]
    for spec in specgram:
        ssam.append(np.average(spec))
    return ssam

#===============================================================================
# calculate SSAM values for given frequency bands. 
#===============================================================================
def calculate_custom(specgram, freq):  
    ssam=[]
    minf=0
    maxf=0
    for i in range(0,len(bands)):
        b=bands[i]
        maxf=b  
        #print("Band=",b, minf, maxf)
        tempsum=0
        count=0
        for j in range(0, len(freq)):
            f=freq[j]
            if minf <= f and f < maxf:
                favg = np.average(specgram[j])
                tempsum += favg
                count += 1
        v=tempsum/count
        if i==0 and v==7:        
            print("Length specgram: "+str(len(specgram))+"x"+str(len(specgram[0])))
            print(specgram)
        #print(i,b,tempsum/count, minf, maxf)
        ssam.append(v)
        minf=b 
    return ssam
    
#===============================================================================
# _nearest_pow_2 - taken from obspy.imaging.spectrogram
#===============================================================================
def _nearest_pow_2(x):
    """
    Find power of two nearest to x

    >>> _nearest_pow_2(3)
    2.0
    >>> _nearest_pow_2(15)
    16.0

    :type x: float
    :param x: Number
    :rtype: Int
    :return: Nearest power of 2 to x
    """
    a = M.pow(2, M.ceil(np.log2(x)))
    b = M.pow(2, M.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return a
    else:
        return b       
         
#===============================================================================
# spectrogram - modified version of obspy.imaging.spectrogram.spectrogram().
#===============================================================================
def spectrogram(data, samp_rate, per_lap=0.9, wlen=None, log=False, dbscale=False, mult=8.0):
    """
    Computes and plots spectrogram of the input data.

    :param data: Input data
    :type samp_rate: float
    :param samp_rate: Samplerate in Hz
    :type per_lap: float
    :param per_lap: Percentage of overlap of sliding window, ranging from 0
        to 1. High overlaps take a long time to compute.
    :type wlen: int or float
    :param wlen: Window length for fft in seconds. If this parameter is too
        small, the calculation will take forever.
    :type log: bool
    :param log: Logarithmic frequency axis if True, linear frequency axis
        otherwise.
    :type dbscale: bool
    :param dbscale: If True 10 * log10 of color values is taken, if False the
        sqrt is taken.
    :type mult: float
    :param mult: Pad zeros to length mult * wlen. This will make the
        spectrogram smoother.
    """
    # enforce float for samp_rate
    samp_rate = float(samp_rate)

    # set wlen from samp_rate if not specified otherwise
    if not wlen:
        wlen = samp_rate / 100.

    npts = len(data)
    # nfft needs to be an integer, otherwise a deprecation will be raised
    # XXX add condition for too many windows => calculation takes for ever
    nfft = int(_nearest_pow_2(wlen * samp_rate))
    if nfft > npts:
        nfft = int(_nearest_pow_2(npts / 8.0))

    if mult is not None:
        mult = int(_nearest_pow_2(mult))
        mult = mult * nfft
    nlap = int(nfft * float(per_lap))

    data = data - data.mean()

    # Here we call not plt.specgram as this already produces a plot
    # matplotlib.mlab.specgram should be faster as it computes only the
    # arrays
    # XXX mlab.specgram uses fft, would be better and faster use rfft
    specgram, freq, time = mlab.specgram(data, Fs=samp_rate, NFFT=nfft, 
                                         pad_to=mult, noverlap=nlap, detrend='linear')
    

    # db scale and remove zero/offset for amplitude
    if dbscale:
        specgram = 10 * np.log10(specgram[1:, :])
    else:
        specgram = np.sqrt(specgram[1:, :])

    return freq, specgram, time

            
#===============================================================================
# write - write SSAM to file
#===============================================================================
def write(ssam, station_id, et, config, missed):
    text=missed+et.strftime(date_format)
    for v in ssam:
        text += " %05d"%v
    if config.print_data or config.print_debug:
        print(station_id+"     "+text)
    try:
        station=station_id.replace(":","_")
        filename = filename_format%("SSAM", et.year, et.month, et.day, station, 60)
        subdir=os.path.join(config.ssam_directory, str(60))
        full_filename = os.path.join(subdir, filename)
        f = open(full_filename,"a")
        f.write(text+"\n")
        if config.print_data or config.print_debug:
            print(station_id+"     "+text)
        f.close() 
    except Exception:
        return text + "\n"  
    return ""  

