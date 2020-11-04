#!/usr/bin/env python3

import argparse
import ast
import csv
from datetime import datetime
import os
import subprocess
import sys
import time

def set_args():
	parser = argparse.ArgumentParser()
	desktop = os.path.expanduser("~/Desktop")
	parser.add_argument(
		'-p','--inventoryPath',
		help=(
			"Path to the root directory you want to inventory.\n"
			"Please make it the full filesystem path!"
			),
		required=True
		)
	parser.add_argument(
		'-o','--outPath',
		default=desktop,
		help=("Output path for the inventory CSV. Default is `~/Desktop`."
			),
		required=False
		)
	parser.add_argument(
		'-t','--mimeType',
		default='video/mp4',
		help=("Set the mimeType you want to declare for all the files on upload.\n"
			"Default is 'mp4.' You can add more options in `mimeTypes.json` in "
			"this directory."
			),
		required=False
		)

	return parser.parse_args()

def humansize(nbytes):
	suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	if nbytes == 0: return '0 B'
	i = 0
	while nbytes >= 1024 and i < len(suffixes)-1:
		nbytes /= 1024.
		i += 1
	f = ('%.2f' % nbytes).rstrip('0').rstrip('.')

	return '%s %s' % (f, suffixes[i])

def file_signature(filePath):
	command = [
	"sf",
	"-json",
	filePath
	]

	output = subprocess.run(
		command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)

	format = ""
	error = ""
	fullSiegfried = ""

	fullSiegfried = output.stdout.decode()
	error = output.stderr.decode()
	format = ast.literal_eval(
		output.stdout.decode()
		)['files'][0]['matches'][0]['format']

	if format == "":
		format = ast.literal_eval(
		output.stdout.decode()
		)['files'][0]['matches'][0]['warning']

	print(format)

	return format, error, fullSiegfried

def inventory(inventoryPath):
	folder = ["Folder"]
	fileName = ["File Name"]
	fileSize = ["File Size"]
	createdTime = ["Created On"]
	modTime = ["Last Modified On"]
	fileFormat = ["File Format"]
	fullSiegfriedJSON = ["Full Siegfried Output"]
	siegfriedError = ["Siegfried Error Messages"]
	
	for root, dirs, files in os.walk(inventoryPath):
		for _file in files:
			if not _file.startswith('.'):
				filePath = os.path.join(root, _file)
				
				# GET THE FILE SIGNATURE
				format, sfError, fullSiegfried = file_signature(filePath)				
				
				# GET THE FILE SIZE
				size = os.stat(filePath).st_size
				hsize = humansize(size)
				
				# GET CREATED/MODIFIED  DATES
				created = os.stat(filePath).st_birthtime
				localCreated = time.localtime(created)
				iso8601Created = time.strftime("%Y-%m-%dT%H:%M:%S",localCreated)
				modded = os.path.getmtime(filePath)
				localModded = time.localtime(modded)
				iso8601Modded = time.strftime("%Y-%m-%dT%H:%M:%S",localModded)
				

				# APPEND ALL THE VALUES TO EACH COLUMN
				folder.append(os.path.dirname(filePath))
				fileName.append(_file)
				fileSize.append(hsize)
				createdTime.append(iso8601Created)
				modTime.append(iso8601Modded)
				fileFormat.append(format)
				fullSiegfriedJSON.append(fullSiegfried)
				siegfriedError.append(sfError)
	
	# TURN EACH LIST INTO A ROW FOR CSV	
	inventoryRows = zip(
		folder,
		fileName,
		fileSize,
		createdTime,
		modTime,
		fileFormat,
		fullSiegfriedJSON,
		siegfriedError
		)

	return inventoryRows

def write_inventory(inventoryRows,inventoryPathDirname,outPath):
	csvPath = os.path.join(outPath,inventoryPathDirname) + '.csv'
	with open(csvPath,'a') as outfile:
		writer = csv.writer(outfile)
		for row in inventoryRows:
			writer.writerow(row)
	return csvPath

def main():
	args = set_args()
	inventoryPath = args.inventoryPath
	inventoryPathDirname = os.path.basename(inventoryPath)
	outPath = args.outPath

	if not os.path.isdir(inventoryPath):
		print(
			"Your selected input path ({}) is not a valid path!".format(
				inventoryPath
				)
			)
		sys.exit()
	else:
		inventoryRows = inventory(inventoryPath)

	csvPath = write_inventory(inventoryRows,inventoryPathDirname,outPath)

	print("you should now have an inventory CSV file at {}".format(csvPath))

if __name__ == '__main__':
	main()
