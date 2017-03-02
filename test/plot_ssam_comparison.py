'''
Created on Feb 27, 2017

@author: dnorgaard
'''
import numpy as np
import matplotlib.pyplot as plt
import os, math

def parse_filename(filename):
    filename=os.path.basename(filename) # strip out directory
    filename=filename.replace(".dat","")
    parts=filename.split("_")
    if parts[0]=="SSAM":    # assume file being read was created from this module.
        version="SSAM"
        date=parts[1]
        station=parts[2]
        channel=parts[3]
        network=parts[4]
        location=parts[5]
        duration=parts[6]   # not used
    else:                   # assume file being read is from old SSAM2Disk output
        version="Legacy_SSAM"
        date=parts[0]
        station=parts[1]
        channel=parts[2]
        network=parts[3]
        location=""
        duration=60
    return [version, date, station, channel, network, location, duration]


# TODO: Account for changes in month/year below
# Update dates (d) and station list as needed.
for d in [ "25", "26", "27"]:
    for station in ["RER","STAR","FMW","RCS"]: 
        recdate=d+"-FEB-2017"
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
        oldrsam="D:\Data\SSAM\\16channel\\"+station2+"\\201702"+d+"_"+station+"_"+channel+"_"+network+".DAT"
        newrsam="D:\Data\SSAM2017\\60\SSAM_201702"+d+"_"+station+"_"+channel+"_"+network+"__60.dat"
        outdir="D:\\Data\SSAM2017\Comparison\\" + station
        os.makedirs(outdir, exist_ok=True)
        fold=open(oldrsam)
        fnew=open(newrsam)
        olddate=[]
        oldtime=[]
        olddata=[]
        # read output from legacy sw
        for line in fold:              
            row=line.split(" ")
            row[-1]=row[-1].rstrip()
            olddate.append(row[0])
            oldtime.append(row[1].replace(":",""))
            numdata=[int(d) for d in row[2:]]
            olddata.append(numdata)
        fold.close()
        #print(olddata)
        # read output from new sw
        newdate=[]
        newtime=[]
        newdata=[]
        for line in fnew:              
            row=line.split(" ")
            row[-1]=row[-1].rstrip()
            newdate.append(row[0])
            t=row[1].replace(":","")
            if t in oldtime:
                newtime.append(t)
                numdata=[int(d) for d in row[2:]]
                newdata.append(numdata)
        fnew.close()
        #print(newdata)
        
        # Rotate data -90 degrees and flip along x-axis
        olddata=np.rot90(olddata, -1)
        olddata=np.fliplr(olddata)
        newdata=np.rot90(newdata, -1)
        newdata=np.fliplr(newdata)
        print("Old data len: ",len(olddata))
        print("New data len: ",len(newdata))
        
        # get file info and create output file name
        outfile=""
        info=parse_filename(newrsam)
        for i in info:
            outfile+="%s_"%i
        outfile=outfile.replace(".dat","")    
        
        # RMS
        numerator=0
        count=0
        for i in range(0,16): # TODO: change to 17 once new Ssam2Disk is running
            for j in range(0,len(newdata)):
                numerator+=math.pow(newdata[i][j]-olddata[i][j],2)
                count+=1
        rms=math.sqrt(numerator/count)
        rms_out=os.path.join(outdir,"%s_rms.txt"%(outfile))
        f=open(rms_out,"w")
        f.write(str(rms))
        f.close()
        print("Created "+rms_out)
        
        # Scatter plot
        for i in range(0,len(newdata)):
            x=olddata[i]
            y=newdata[i]
            m, b = np.polyfit(x, y, 1)
            plt.plot(x, m*x+b,"r")
            plt.plot(x, y, '.')
            plt.ylabel("New")
            plt.xlabel("Legacy")
            plt.title("%s%03d"%(outfile,i))
            sdir=os.path.join(outdir,"%s %s Scatter"%(recdate, station))
            os.makedirs(sdir, exist_ok=True)
            full_out=os.path.join(sdir,"%s%03d_scatter.png"%(outfile,i))
            plt.savefig(full_out)
            plt.close()
            print("Created "+full_out)
            
        # Line plot
        for i in range(0,len(newdata)):
            plt.figure(figsize=(24,12))
            plt.plot(oldtime, olddata[i], newtime, newdata[i])
            plt.ylabel("SSAM")
            plt.xlabel("Time")
            plt.title("%s%03d"%(outfile,i))
            sdir=os.path.join(outdir,"%s %s Line"%(recdate, station))
            os.makedirs(sdir, exist_ok=True)
            full_out=os.path.join(sdir,"%s%03d_line.png"%(outfile,i))
            plt.savefig(full_out)
            plt.close()
            print("Created "+full_out)