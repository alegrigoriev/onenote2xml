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
	sys.exit("onenote2xml: This package requires Python 3.9+")

from ..exception import EndOfBufferException

class onestore_reader:
	# If the length argument is supplied, it means the length after 'slice_offset' in the buffer
	# If slice_offset is not specified, it's same as offset
	def __init__(self, data:bytes, length:int=None, slice_offset:int=0):
		data_len = len(data)
		if length is None:
			length = data_len - slice_offset

		if slice_offset > data_len:
			raise EndOfBufferException(
				"Attempted slice at offset 0x%X with only 0x%X bytes in buffer"
				% (slice_offset, data_len))

		data_len -= slice_offset
		if length > data_len:
			raise EndOfBufferException(
				"Attempted slice of 0x%X bytes with only 0x%X bytes remaining in buffer"
				% (length, data_len))

		self.data = data
		# Start of the record data in 'data'
		self.slice_offset = slice_offset
		# Current offset to read data, relative to 'slice_offset'
		self.offset = 0
		# length of data to read, starting from 'slice_offset'
		self.length = length
		return

	def clone(self, ref=None, offset=None, additional_offset:int=0, length:int=None):
		if ref is not None:
			assert(self.slice_offset == 0)
			assert(not ref.isNil())
			assert(not ref.isZero())
			offset = ref.stp
			assert(length is None)
			length = ref.cb
		elif offset is None:
			offset = self.offset
		offset += additional_offset
		if offset > self.length:
			raise EndOfBufferException(
				"Attempted slice at offset 0x%X with only 0x%X bytes in buffer"
				% (offset, self.length))

		if length is None:
			length = self.length - offset
		elif length + offset > self.length:
			raise EndOfBufferException(
				"Attempted slice of 0x%X bytes with only 0x%X bytes remaining in buffer"
				% (length, self.length - offset))
		return onestore_reader(self.data,
								slice_offset=offset+self.slice_offset,
								length=length)

	def extract(self, length:int=None):
		if length is not None and length < 0:
			# Cut the tail off
			if self.offset > self.length + length:
				raise EndOfBufferException(
					"Attempted tail slice 0x%X long with only 0x%X bytes remaining"
					% (-length, self.length-self.offset))
			reader = self.clone(offset=self.length + length, length=-length)
			self.length += length
			return reader

		reader = self.clone(length=length)
		self.skip(reader.length)
		return reader

	def check_read(self, length:int):
		if self.offset + length > self.length:
			raise EndOfBufferException(
				"Attempted read of %d bytes with only %d bytes remaining in buffer"
				% (length, self.length - self.offset))
		return

	def read_bytes(self, length:int)->bytes:
		self.check_read(length)
		offset = self.offset + self.slice_offset
		bytes_read = self.data[offset:offset+length]
		self.offset += length
		return bytes_read

	# Read without updating the current offset
	def read_bytes_at(self, offset:int, length:int)->bytes:
		self.check_read(length + offset)
		offset += self.offset + self.slice_offset
		bytes_read = self.data[offset:offset+length]
		# Not advancing self.offset
		return bytes_read

	def read_uint8(self)->int:
		return self.read_bytes(1)[0]

	def read_uint16(self)->int:
		return int.from_bytes(self.read_bytes(2), byteorder='little', signed=False)

	def read_uint32(self)->int:
		return int.from_bytes(self.read_bytes(4), byteorder='little', signed=False)

	def read_uint64(self)->int:
		return int.from_bytes(self.read_bytes(8), byteorder='little', signed=False)

	def skip(self, skip_bytes:int):
		self.check_read(skip_bytes)
		self.offset += skip_bytes
		return

	def get_offset(self):
		return self.offset

	def remaining(self):
		return self.length - self.offset
