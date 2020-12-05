# fileReporter

Script to output a CSV inventory of a directory and subdirectories, using [Siegfried](https://www.itforarchivists.com/siegfried/) to identify file formats and other details.

Optionally can run [Mediainfo]() on each file to get more AV-specific details (codec ID, aspect ratio, duration, etc.)

You can specify an output path with `-o` or use the default of your `Desktop`. The CSV is named for the directory you run the script on.

## Usage

With `mediainfo` and specified output path: 

`python3 fileReporter.py -m -p /path/to/dir/you/want/2/inventory -o /optional/output/path`

## Dependencies

* `siegfried`
  * `brew install siegfried`
* `pyjq`
  * this is used to parse mediainfo json...
  * `pip3 install pyjq`

*Note:* currently requires Python 3.9+ (uses the cool new dict union syntax `{} | {}`)
