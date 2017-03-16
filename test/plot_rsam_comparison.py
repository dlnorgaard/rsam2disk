'''
Created on Feb 27, 2017

This script will perform the following comparisons between the legacy Rsam2Disk software and the new:
1. RMS, slope, and y-intercept to text file
2. Scatter plot with fitted line
3. Time series line plot

@author: dnorgaard
'''

import matplotlib.pyplot as plt
import numpy as np
import os, math

def parse_filename(filename):
    filename=os.path.basename(filename) # strip out directory
    filename=filename.replace(".dat","")
    parts=filename.split("_")
    if parts[0]=="RSAM":    # assume file being read was created from this module.
        version="RSAM"
        date=parts[1]
        station=parts[2]
        channel=parts[3]
        network=parts[4]
        location=parts[5]
        duration=parts[6]   # not used
    else:                   # assume file being read is from old SSAM2Disk output
        version="Legacy_RSAM"
        date=parts[0]
        station=parts[1]
        channel=parts[2]
        network=parts[3]
        location=""
        duration=60
    return [version, date, station, channel, network, location, duration]

for d in [ "10","11","12"]:
        for station in ["OBSR","STAR","FMW","RCS","RER"]: 
            for duration in [ 60, 600]:
                recdate=d+"-MAR-2017"
                if station=="OBSR":
                    network="CC"
                    channel="BHZ"
                else:
                    network="UW"
                    channel="EHZ"
                if len(station) < 4:
                    station2=station+"_"
                else:
                    station2=station
                # TODO: Need to change month/year as appropriate
                if duration==60:
                    oldrsam="D:\Data\RSAM\\1Minute\\201703_"+network+"_"+station2+"_"+channel+"RSAM1Min.DAT"
                    newrsam="D:\Data\RSAM2017\\60\RSAM_201703"+d+"_"+station+"_"+channel+"_"+network+"__60.csv"
                    outdir="D:\\Data\RSAM2017\Comparison\\" + station
                else:
                    oldrsam="D:\Data\RSAM\\10Minute\\201703_"+network+"_"+station2+"_"+channel+"RSAM10Min.DAT"
                    newrsam="D:\Data\RSAM2017\\600\RSAM_201703"+d+"_"+station+"_"+channel+"_"+network+"__600.csv"
                    outdir="D:\\Data\RSAM2017\Comparison\\" + station
                os.makedirs(outdir, exist_ok=True)
                try:
                    fold=open(oldrsam)
                    fnew=open(newrsam)
                except FileNotFoundError as err:
                    print(err)
                    continue
                oldtime=[]
                olddata=[]
                newtime=[]
                newdata=[]
                # read output from legacy sw
                for line in fold:              
                    row=line.split(",")
                    dt=row[0].split(" ")
                    if dt[0]==recdate:
                        t=dt[1][0:5].replace(":","")            # minute
                        oldtime.append(t)
                        olddata.append(int(row[1].rstrip("\n")))  # rsam
                fold.close()
                numerator=0
                sumnew=0
                sumold=0
                count=0
                # read output from new sw
                for line in fnew:              
                    row=line.split(",")
                    dt=row[0].split(" ")
                    t=dt[1][0:5].replace(":","") 
                    if dt[0].upper()==recdate and t in oldtime: # only if data exists in old output also
                        x1=int(row[1])
                        sumnew+=x1
                        x2=olddata[count]
                        sumold+=x2
                        numerator+=math.pow((x1-x2),2)
                        count+=1
                        newtime.append(t)
                        newdata.append(x1)   # rsam
                fold.close()
                fnew.close()
                if count==0:
                    print(oldrsam)
                    print(newrsam)
                    print("No valid data found. Skipping.")
                    continue
                
                # remove time/data from old output where corresponding data does not exist for new output (e.g. due to tank gaps)
                remove_list=[]
                for i in range(0,len(oldtime)):
                    t=oldtime[i]
                    if t not in newtime:
                        remove_list.append(i)
                oldtime=np.delete(oldtime, remove_list)
                olddata=np.delete(olddata, remove_list)
                
                # get file info and create output file name
                outfile=""
                info=parse_filename(newrsam)
                for i in info:
                    outfile+="%s_"%i
                outfile=outfile.replace(".csv","")
                
                # RMS, slope, and y-intercept
                # rms
                try:
                    rms_out=os.path.join(outdir,"%sRMS.txt"%(outfile))
                    rms=math.sqrt(numerator/count)
                    # m, b
                    x=np.array(olddata)
                    #print(len(olddata), len(newdata))
                    y=np.array(newdata)
                    m, b = np.polyfit(x, y, 1)
                    f=open(rms_out,'w')
                    f.write("%s %d %.1f %.1f"%(recdate, rms, m, b))
                    f.close()
                    print("Created "+rms_out)
                    
                    # scatter plot with line fit
                    plt.plot(x, m*x+b,"r")
                    plt.plot(x, y, '.')
                    plt.ylabel("RSAM (new)")
                    plt.xlabel("RSAM (legacy)")
                    plt.title(outfile)
                    full_out=os.path.join(outdir,"%sscatter.png"%(outfile))
                    plt.savefig(full_out)
                    print("Created "+full_out)
                    plt.close()
                    plt.clf()
                    plt.cla()
                    
                    # line plot 
                    plt.figure(figsize=(24,12))
                    plt.plot(oldtime, olddata, "r--", newtime, newdata, "b--")
                    plt.ylabel("RSAM")
                    plt.xlabel("Time")
                    plt.title(outfile)
                    full_out=os.path.join(outdir,"%sline.png"%(outfile))
                    plt.savefig(full_out)
                    print("Created "+full_out)
                    plt.close()
                    plt.clf()
                    plt.cla()
                    
                except Exception as err:
                    print(oldrsam)
                    print(newrsam)
                    raise err
                