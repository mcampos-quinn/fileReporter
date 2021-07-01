#!/usr/bin/env python3

import argparse
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
	'File Format (Mediainfo)':'Format',
	'Format Term':'Format_String',
	'Duration':'Duration_String',
	'Format Profile':'Format_Profile',
	'Sample Rate':'SamplingRate_String',
	'Bit Depth':'BitDepth_String',
	'Bitrate':'BitRate_String',
	'Channels':'Channels',
	'Frame Rate':'FrameRate_String',
	'Width':'Width_String',
	'Height':'Height_String',
	'CodecID':'CodecID',
	'Aspect Ratio':'DisplayAspectRatio_String',
	'Audio Channels':'AudioCount',
	'Full Mediainfo Output':None
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

	temp['Full Mediainfo Output'] = mediainfo_output
	filtered = {k: v for k, v in temp.items() if v is not None}
	details = filtered

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


def run_siegfried(inventory_path,out_path,accession_name):
	sf_file_path = os.path.join(out_path,accession_name+".csv")
	# print(sf_file_path)
	# print(inventory_path)
	command = [
	'sf',
	'-csv',
	inventory_path,
	'>',
	sf_file_path
	]
	command = ' '.join(command)
	try:
		output = subprocess.run(command, shell=True)
		status = True
	except:
		status = False

	return sf_file_path,status

def run_mediainfo(csv_path,out_path):
	temp = []
	# temp_path = os.path.join(out_path,'temp.csv')
	with open(csv_path,'r') as sf_file:
		reader = csv.DictReader(sf_file)
		for row in reader:
			file_path = row['filename']
			print("Running mediainfo on {}".format(file_path))
			output,av_format = av_sniffer(file_path)
			av_file_details = av_details(output,av_format)
			for k in av_detail_dict.keys():
				# compare with the complete list 
				# of fields we want from Mediainfo
				# and add filler for empty values
				if not k in av_file_details:
					# print(k)
					av_file_details[k] = ""
			# join the row dict with the mediainfo dict (python 3.9+)
			intermediate = row | av_file_details

			# add the row dict to the temp list
			temp.append(intermediate)

	csv_path = write_inventory(temp,out_path,csv_path)

	return csv_path

def write_inventory(row_list,out_path,csv_path):
	'''
	This spruces up the csv to make it more user friendly.
	Takes in a list of each row as a dict from csv.DictReader
	then parses out a couple of more useful fields.
	It then rearranges columns to be more useful.
	'''
	temp_path = os.path.join(out_path,'temp.csv')
	header_order = [
		'File Name', 'File Size', 'Duration','File Format (Mediainfo)',
		'Format Profile', 'Format Term', 'Created On', 'Last Modified On',
		'MIME Type (Siegfried)', 'File Format (Siegfried)',
		'File Format Version (Siegfried)', 'Aspect Ratio', 'Frame Rate', 
		'Width', 'Height', 'CodecID', 'Sample Rate', 'Bit Depth', 'Bitrate',
		'Channels', 'Audio Channels', 'Size (bytes)', 'Format ID Namespace',
		'Format ID', 'Basis of ID (Siegfried)', 'Siegfried Error Messages',
		'warning', 'File Path', 'Full Mediainfo Output'
	]
	for item_row in row_list:
		# Add created date
		file_path = item_row['filename']
		iso8601Created = ""
		try:
			created = os.stat(file_path).st_birthtime
			localCreated = time.localtime(created)
			iso8601Created = time.strftime("%Y-%m-%dT%H:%M:%S",localCreated)
		except:
			pass
		item_row['Created On'] = iso8601Created

		# Add basename
		item_row['File Name'] = os.path.basename(file_path)

		# Add human readable size
		item_row['File Size'] = humansize(int(item_row['filesize']))

		# Rename Siegfried column names
		item_row['File Format (Siegfried)'] = item_row.pop('format')
		item_row['File Format Version (Siegfried)'] = item_row.pop('version')
		item_row['Size (bytes)'] = item_row.pop('filesize')
		item_row['Last Modified On'] = item_row.pop('modified')
		item_row['File Path'] = item_row.pop('filename')
		item_row['Siegfried Error Messages'] = item_row.pop('errors')
		item_row['Format ID Namespace'] = item_row.pop('namespace')
		item_row['Format ID'] = item_row.pop('id')
		item_row['MIME Type (Siegfried)'] = item_row.pop('mime')
		item_row['Basis of ID (Siegfried)'] = item_row.pop('basis')

	# grab the headers from the first row dict
	headers = list(row_list[0].keys())
	# reorder based on list above
	headers = [x for x in header_order if x in headers]
	with open(temp_path,'w') as outfile:
		writer = csv.DictWriter(outfile,fieldnames=headers)
		writer.writeheader()
		for item in row_list:
			writer.writerow(item)

	# now write the csv
	os.replace(temp_path,csv_path)

	return csv_path

def main():
	args = set_args()
	inventory_path = args.inventory_path
	if inventory_path.endswith('/'):
		inventory_path = inventory_path.rstrip('/')
	accession_name = os.path.basename(inventory_path)
	out_path = args.out_path
	mediainfo = args.mediainfo

	if not os.path.isdir(inventory_path):
		print(
			"Your selected input path ({}) is not a directory!".format(
				inventory_path
				)
			)
		sys.exit(1)
	print("Running Siegfried")	
	sf_file_path,sf_status = run_siegfried(inventory_path,out_path,accession_name)

	if mediainfo and sf_status:
		csv_path = run_mediainfo(sf_file_path,out_path)
	elif sf_status:
		row_list = []
		with open(sf_file_path,'r') as sf_file:
			reader = csv.DictReader(sf_file)
			for row in reader:
				row_list.append(row)
		csv_path = write_inventory(row_list,out_path,sf_file_path)
	else:
		csv_path = "Oops there was an error!"

	print("You should now have an inventory CSV file at {}".format(csv_path))

if __name__ == '__main__':
	import sys 
	print(sys.version)
	main()
