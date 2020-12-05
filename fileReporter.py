#!/usr/bin/env python3

import argparse
import ast
import csv
from datetime import datetime
import json
import os
import pyjq
import subprocess
import sys
import time

av_detail_dict = {
	# 'CSV header name':'__Mediainfo Field Name',
	'File Format (MediaInfo)':'Format',
	'Format term':'Format_String',
	'Duration':'Duration_String',
	'Format Profile':'Format_Profile',
	'Sample Rate':'SamplingRate_String',
	'Bit Depth':'BitDepth_String',
	'Bitrate':'BitRate_String',
	'Channels':'Channels',
	'Frame rate':'FrameRate_String',
	'Width':'Width_String',
	'Height':'Height_String',
	'CodecID':'CodecID',
	'Aspect ratio':'DisplayAspectRatio_String',
	'Audio Channels':'AudioCount'
}

general_siegfried_dict = {
		"File Name":[],
		"File Size":[],
		"File Format (Siegfried)":[],
		"Folder":[],
		"Created On":[],
		"Last Modified On":[],
		"Full Siegfried Output":[],
		"Siegfried Error Messages":[]
	}

def set_args():
	parser = argparse.ArgumentParser()
	desktop = os.path.expanduser("~/Desktop")
	parser.add_argument(
		'-p','--inventory_path',
		help=(
			"Path to the root directory you want to inventory.\n"
			"Please make it the full filesystem path!"
			),
		required=True
		)
	parser.add_argument(
		'-o','--out_path',
		default=desktop,
		help=("Output path for the inventory CSV. Default is `~/Desktop`."
			),
		required=False
		)
	parser.add_argument(
		'-m','--mediainfo',
		action='store_true',
		default=False,
		help=("Run mediainfo on input files to get details of AV files.\n"
			"Default is False."
			),
		required=False
		)

	return parser.parse_args()


def av_sniffer(input_path):
	'''
	Run `mediainfo` on a file to see if it's AV.
	Return audio/video/image/not_av along with mediainfo output JSON
	'''
	mediainfo_command = [
		'mediainfo',
		'-f',
		'--Output=JSON',
		input_path
		]

	try:
		mediainfo_out = subprocess.run(mediainfo_command,stdout=subprocess.PIPE)
		out = mediainfo_out.stdout.decode('utf-8')
		# print(out)
		output = json.loads(out)

		general_track = pyjq.first(
			'.media.track[] | select(.["@type"] == "General")',
			output
			)
		if 'VideoCount' in general_track:
			format = 'Video'
		elif 'AudioCount' in general_track:
			format = 'Audio'
		elif 'ImageCount' in general_track:
			format = 'Image'
		else:
			output = None
			format = 'not_av'
	except:
		output = None
		format = None

	return output,format

def av_details(mediainfo_output,input_format):
	details = av_detail_dict
	temp = {}
	for field in details.keys():
		try:
			temp[field] = pyjq.first(
				'.media.track[] | select(."@type" == "{}") | .{}'.format(
					input_format,details[field]
					),
				mediainfo_output
				)
			# print(field)
		except:
			pass
	if input_format == 'Video':
		try:
			temp['Audio Channels'] = pyjq.first(
				'.media.track[] | select(."@type" == "General") | .AudioCount',
				mediainfo_output
				)
		except:
			pass

	filtered = {k: v for k, v in temp.items() if v is not None}
	details = filtered
	# print(details)

	return details


def humansize(nbytes):
	suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	if nbytes == 0: return '0 B'
	i = 0
	while nbytes >= 1024 and i < len(suffixes)-1:
		nbytes /= 1024.
		i += 1
	f = ('%.2f' % nbytes).rstrip('0').rstrip('.')

	return '%s %s' % (f, suffixes[i])

def file_signature(file_path):
	command = [
	"sf",
	"-json",
	file_path
	]

	output = subprocess.run(
		command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)

	format = ""
	error = ""
	full_Siegfried = ""

	full_Siegfried = output.stdout.decode()
	error = output.stderr.decode()
	format = pyjq.first(
		'.files[].matches[].format',
		json.loads(full_Siegfried)
		)
	# If no format was returned, look for 'id'
	if format == "":
		format = pyjq.first(
		'.files[].matches[].id',
		json.loads(full_Siegfried)
		)
	# If that fails too, look for 'warning'
	if format == "":
		format = pyjq.first(
		'.files[].matches[].warning',
		json.loads(full_Siegfried)
		)

	return format, error, full_Siegfried

def inventory(inventory_path,mediainfo):
	# initiate a list for dicts about each file
	inventory_dicts = []
	# get the general dict of siegfried details
	sf_details = general_siegfried_dict
	
	if mediainfo:
		# add empty values for AV information
		for k in av_detail_dict.keys():
			sf_details[k] = ""

	for root, dirs, files in os.walk(inventory_path):
		for _file in files:
			print(_file)
			if not _file.startswith('.'):
				# Start an individual dict for each file
				item_details = sf_details

				file_path = os.path.join(root, _file)
				
				# GET THE FILE SIGNATURE
				format, sf_Error, full_Siegfried = file_signature(file_path)				
				
				# GET THE FILE SIZE
				size = os.stat(file_path).st_size
				hsize = humansize(size)
				
				# GET CREATED/MODIFIED  DATES
				created = os.stat(file_path).st_birthtime
				localCreated = time.localtime(created)
				iso8601Created = time.strftime("%Y-%m-%dT%H:%M:%S",localCreated)
				
				modded = os.path.getmtime(file_path)
				localModded = time.localtime(modded)
				iso8601Modded = time.strftime("%Y-%m-%dT%H:%M:%S",localModded)

				# ASSIGN VALUES TO EACH FIELD
				item_details["Folder"] = os.path.dirname(file_path)
				item_details["File Name"] = _file
				item_details["File Size"] = hsize
				item_details["Created On"] = iso8601Created
				item_details["Last Modified On"] = iso8601Modded
				item_details["File Format (Siegfried)"] = format
				item_details["Full Siegfried Output"] = full_Siegfried
				item_details["Siegfried Error Messages"] = sf_Error

				# RUN MEDIAINFO ON AV STUFF
				if mediainfo:
					output,av_format = av_sniffer(file_path)
					av_file_details = av_details(output,av_format)
					# add mediainfo info to item dict
					for k,v in av_file_details.items():
						item_details[k] = v
					# or if the value was absent, append empty string
					for k in av_detail_dict.keys():
						if not k in av_file_details:
							# print(sf_details)
							item_details[k] = ""

				# print(item_details)
				# add the item to the inventory
				inventory_dicts.append(item_details.copy())
	# print(inventory_dicts)

	return inventory_dicts

def write_inventory(
	inventory_dicts,
	inventory_path_dirname,
	out_path,
	mediainfo
	):
	header_order = [
	'File Name', 'File Size', 'File Format (Siegfried)', 'Folder', 
	'Created On', 'Last Modified On',  'File Format (MediaInfo)', 
	'Format term', 'Duration', 'Format Profile', 'Sample Rate', 'Bit Depth', 
	'Bitrate', 'Channels', 'Frame rate', 'Width', 'Height', 'CodecID', 
	'Aspect ratio', 'Audio Channels','Full Siegfried Output',
	'Siegfried Error Messages','Full Mediainfo Output'
	]
	# Get rid of unused columns
	if not mediainfo:
		for i in header_order:
			if i in av_detail_dict:
				header_order.remove(i)

	csv_path = os.path.join(out_path,inventory_path_dirname) + '.csv'
	with open(csv_path,'a') as outfile:
		writer = csv.DictWriter(outfile,fieldnames=header_order)
		writer.writeheader()
		for item in inventory_dicts:
			# print(item)
			writer.writerow(item)

	return csv_path

def main():
	args = set_args()
	inventory_path = args.inventory_path
	inventory_path_dirname = os.path.basename(inventory_path)
	out_path = args.out_path
	mediainfo = args.mediainfo

	if not os.path.isdir(inventory_path):
		print(
			"Your selected input path ({}) is not a valid path!".format(
				inventory_path
				)
			)
		sys.exit()
	else:
		# go make the inventory
		inventory_dicts = inventory(inventory_path,mediainfo)

	# write the inventory to csv
	csv_path = write_inventory(
		inventory_dicts,
		inventory_path_dirname,
		out_path,
		mediainfo
		)

	print("you should now have an inventory CSV file at {}".format(csv_path))

if __name__ == '__main__':
	main()
