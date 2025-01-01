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
	parser.add_argument("--output-directory", '-R', dest='output_dir', metavar='<json-directory>',
						help="Directory name for writing revision JSON files")
	parser.add_argument("--log", '-L', metavar='<log file>', help="Log file")
	parser.add_argument("--all-revisions", '-A', action="store_true",
						help="Include all revisions in the output, not just the current snapshot")
	parser.add_argument("--include-oids", '-o', action="store_true",
						help="Add Object IDs (OID) attribute to all generated structures")
	parser.add_argument("--verbose", '-v', dest='verbosity', type=int, default=0, const=1, nargs='?',
						help="Generated file verbosity: default 0 - basic properties, 1+ - more stuff")
	parser.add_argument("--list-revisions", '-l', action="store_true",
						help="List all revisions to the standard output")
	parser.add_argument("--combine-revisions", '-c', metavar='<minutes>', default=0, type=int, const=600, nargs='?',
						help="Maximum time span in minutes, to combine revisions to a single one")
	parser.add_argument("--timestamp", '-T', metavar='<revision-timestamp>', type=int, default=None,
						help="Generate a snapshot of a revision with this timestamp")
	parser.add_argument("--incremental", '-i', action="store_true",
						help="Generate revisions in incremental form")
	parser.add_argument("--recurse", '-r', action="store_true", help="Include child notebooks for .onetoc2 file")

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

	if options.recurse and not onenote.IsNotebookToc2():
		raise OneException("--recurse option only applicable to .onetoc2 file")

	if options.output:
		print("Making JSON file %s..." % (options.output,), file=sys.stderr, end='', flush=True)
		onenote.MakeJsonFile(options.output, options)
		print("done", file=sys.stderr)

	if options.output_dir:
		if onenote.IsNotebookToc2() and not options.recurse:
			raise OneException("'--output-directory' option only applicable to .onetoc2 file with --recurse")
		print("Making JSON revisions in %s..." % (options.output_dir,), file=sys.stderr)
		onenote.MakeJsonRevisions(options.output_dir, options)
		print("done", file=sys.stderr)

	if options.list_revisions:
		onenote.PrintVersions(sys.stdout, human_friendly=False)

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
