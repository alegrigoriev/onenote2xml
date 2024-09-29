#   Copyright 2024 Alexandre Grigoriev
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from __future__ import annotations
import sys

if sys.version_info < (3, 9):
	sys.exit("1note2json: This package requires Python 3.9+")

def main():

	import argparse

	parser = argparse.ArgumentParser(description='Convert Microsoft OneNote files to JSON.', allow_abbrev=False)
	parser.add_argument("onefile", metavar='<onefile>', help="Source '.one' or '.onetoc2' Microsoft OneNote file")
	parser.add_argument("--output", '-O', metavar='<json-filename>',
						help="Filename of output JSON file")
	parser.add_argument("--log", '-L', metavar='<log file>', help="Log file")

	options = parser.parse_args()

	if options.log:
		log_file = open(options.log, 'wt', encoding='utf-8')

		from types import SimpleNamespace
		verbose = SimpleNamespace()
		verbose.dump_nodelists = False
		verbose.dump_object_spaces = False

		options.verbose = verbose
	else:
		log_file = None

	from ONE.NOTE.onenote import OneNote
	print("Loading file %s..." % (options.onefile,), file=sys.stderr, end='', flush=True)
	onenote = OneNote.open(options.onefile, options, log_file)
	print("done", file=sys.stderr)

	if options.output:
		print("Making JSON file %s..." % (options.output,), file=sys.stderr, end='', flush=True)
		onenote.MakeJsonFile(options.output, options)
		print("done", file=sys.stderr)

	if log_file is not None:
		onenote.dump(log_file, options.verbose)
		log_file.close()

	return 0

if __name__ == "__main__":
	from ONE.exception import OneException
	try:
		sys.exit(main())
	except OneException as ex:
		print("\nERROR:", str(ex), file=sys.stderr)
		sys.exit(1)
	except FileNotFoundError as fnf:
		print("\nERROR: %s: %s" % (fnf.strerror, fnf.filename), file=sys.stderr)
		sys.exit(1)
	except KeyboardInterrupt:
		# silent abort
		sys.exit(130)