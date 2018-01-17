#!/usr/bin/env python3

import os
import sys
import csv
import time
from datetime import datetime

def humansize(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

folder = ["Folder"]
fileName = ["File Name"]
fileSize = ["File Size"]
createdTime = ["Created On"]
modTime = ["Last Modified On"]

reportDir = input("Drag the folder you want to report on here: ").rstrip()
if os.path.isdir(reportDir):
	reportDirname = os.path.split(reportDir)[1]
	print(reportDirname)
	os.chdir(reportDir)
else:
	print("You got a problem, "+reportDir+" is not a valid directory. Try again, pal!")
	sys.exit()

outputDir = input("Your report will be called: '"+reportDirname+".csv.'\n"
				  "Drag the folder where you want your report to land here (otherwise it will go to the Desktop): ").rstrip()
if os.path.isdir(outputDir):
	csvPath = os.path.join(outputDir,reportDirname+".csv")
else:
	csvPath = os.path.join("~/Desktop",reportDirname+".csv")

for root, dirs, files in os.walk('.'):
    for _file in files:
        if not _file.startswith('.'):
            path = os.path.join(root, _file)
            folder.append(os.path.dirname(path))
            size = os.stat(path).st_size
            hsize = humansize(size)
            created = os.stat(path).st_birthtime
            localCreated = time.localtime(created)
            iso8601Created = time.strftime("%Y-%m-%dT%H:%M:%S",localCreated)
            modded = os.path.getmtime(path)
            localModded = time.localtime(modded)
            iso8601Modded = time.strftime("%Y-%m-%dT%H:%M:%S",localModded)
            fileName.append(_file)
            fileSize.append(hsize)
            createdTime.append(iso8601Created)
            modTime.append(iso8601Modded)
        
outputRows = zip(folder,fileName,fileSize,createdTime,modTime)

with open(csvPath,'w+') as outfile:
    writer = csv.writer(outfile)
    for row in outputRows:
        writer.writerow(row)

