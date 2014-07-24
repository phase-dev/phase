"""
Copyright 2014

This file is part of Phase.

Phase is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Phase is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Phase.  If not, see <http://www.gnu.org/licenses/>.
"""

from libphase import gtk
from libphase.windows import window
from gi.repository import Gtk

from base64 import b64encode,b64decode
from urllib import quote_plus, unquote
from binascii import hexlify,unhexlify
from hashlib import md5,sha1
class Encoder(window.Window):

	def __init__(self,shared_objects,name):
		window.Window.__init__(self,shared_objects,name)

		self.textbuffer_input=gtk.TextBuffer()
		self.textbuffer_encode_base64=gtk.TextBuffer()
		self.textbuffer_encode_url=gtk.TextBuffer()
		self.textbuffer_encode_hex=gtk.TextBuffer()
		self.textbuffer_decode_base64=gtk.TextBuffer()
		self.textbuffer_decode_url=gtk.TextBuffer()
		self.textbuffer_decode_hex=gtk.TextBuffer()
		self.textbuffer_hash_md5=gtk.TextBuffer()
		self.textbuffer_hash_sha1=gtk.TextBuffer()

		self.builder.get_object("textviewEncoderInput").set_buffer(self.textbuffer_input)
		self.builder.get_object("textviewEncodeBase64").set_buffer(self.textbuffer_encode_base64)
		self.builder.get_object("textviewEncodeURL").set_buffer(self.textbuffer_encode_url)
		self.builder.get_object("textviewEncodeHex").set_buffer(self.textbuffer_encode_hex)
		self.builder.get_object("textviewDecodeBase64").set_buffer(self.textbuffer_decode_base64)
		self.builder.get_object("textviewDecodeURL").set_buffer(self.textbuffer_decode_url)
		self.builder.get_object("textviewDecodeHex").set_buffer(self.textbuffer_decode_hex)
		self.builder.get_object("textviewHashMD5").set_buffer(self.textbuffer_hash_md5)
		self.builder.get_object("textviewHashSHA1").set_buffer(self.textbuffer_hash_sha1)

		self.textbuffer_input.connect("changed",self.handle_input_changed)


	def handle_input_changed(self,textbuffer):
		text=self.textbuffer_input.get_all_text()
		

		self.textbuffer_encode_base64.set_text(b64encode(text))
	
		try:
			self.textbuffer_decode_base64.set_text(b64decode(text))
		except:
			self.textbuffer_decode_base64.clear()

		self.textbuffer_encode_url.set_text(quote_plus(text))
		self.textbuffer_decode_url.set_text(unquote(text))

		self.textbuffer_encode_hex.set_text(hexlify(text))

		try:
			self.textbuffer_decode_hex.set_text(unhexlify(text))
		except:
			self.textbuffer_decode_hex.clear()

		self.textbuffer_hash_md5.set_text(md5(text).hexdigest())
		self.textbuffer_hash_sha1.set_text(sha1(text).hexdigest())

		

