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

from gi.repository import Gtk
from gi.repository import GtkSource
from gi.repository import WebKit

from libphase import utilities,dialogs

from base64 import b64encode,b64decode
from urllib import quote_plus, unquote
from binascii import hexlify,unhexlify


class TextBuffer(GtkSource.Buffer):

	def __init__(self):
		super(TextBuffer,self).__init__()

	def clear(self):
		self.delete(self.get_start_iter(),self.get_end_iter())

	def get_all_text(self,hidden=False):
		return self.get_text(self.get_start_iter(),self.get_end_iter(),hidden)

	def replace(self,start,end,text):
		self.delete(start,end)
		self.insert(start,text)


class HTTPView(Gtk.Notebook):

	def __init__(self,webkit=False):
		super(HTTPView,self).__init__()
		self.text_buffer=TextBuffer()
		self.text_view=HTTPTextView(self.text_buffer)
		text_view_scrolled_window=Gtk.ScrolledWindow(expand=True)
		text_view_scrolled_window.add(self.text_view)
		self.text_tab=self.insert_page(text_view_scrolled_window,Gtk.Label("Text"),-1)

		self.set_tab_pos(Gtk.PositionType.BOTTOM)

		if webkit:
			self.webkit_view=WebKit.WebView(expand=True)
			self.set_show_tabs(True)
			webkit_scrolled_window=Gtk.ScrolledWindow(expand=True)
			webkit_scrolled_window.add(self.webkit_view)
			self.webkit_tab=self.insert_page(webkit_scrolled_window,Gtk.Label("Rendered"),-1)
			self.connect("switch-page",self.handler_switch_page)
		else:
			self.webkit_tab=-1
			self.set_show_tabs(False)


	def handler_switch_page(self,notebook, page, page_num):
		if page_num == self.webkit_tab:
			self.webkit_view.load_html_string(self.text_buffer.get_all_text(),"NULL")

class HTTPTextView(GtkSource.View):
	
	def __init__(self,text_buffer):
		super(HTTPTextView,self).__init__(expand=True)
		self.set_buffer(text_buffer)
		self.connect("populate-popup",self.handle_populate_popup)
		self.lang_manager = GtkSource.LanguageManager()
		self.get_buffer().set_language(self.lang_manager.get_language('none'))

	def set_content_type(self,content_type):
		if len(content_type) == 1:
			content_type=content_type[0]
			if "text/html" in content_type:
				self.get_buffer().set_language(self.lang_manager.get_language('html'))
			elif "application/javascript" in content_type or "application/x-javascript" in content_type or "text/javascript" in content_type:
				self.get_buffer().set_language(self.lang_manager.get_language('js'))
			elif "text/css" in content_type:
				self.get_buffer().set_language(self.lang_manager.get_language('css'))
			elif "application/json" in content_type :
				self.get_buffer().set_language(self.lang_manager.get_language('json'))
			elif "application/soap+xml" in content_type:
				self.get_buffer().set_language(self.lang_manager.get_language('xml'))
			else:
				self.get_buffer().set_language(self.lang_manager.get_language('none'))
		else:
			self.get_buffer().set_language(self.lang_manager.get_language('none'))

	def handle_populate_popup(self,textview,menu):
		encode=Gtk.MenuItem(label="Encode")
		encode_submenu=Gtk.Menu()
		encode_b64=Gtk.MenuItem(label="Base 64")
		encode_b64.connect("activate",self.encoder,"ENCODE","B64")
		encode_url=Gtk.MenuItem(label="URL")
		encode_url.connect("activate",self.encoder,"ENCODE","URL")
		encode_hex=Gtk.MenuItem(label="ASCII Hex")
		encode_hex.connect("activate",self.encoder,"ENCODE","HEX")
		encode_submenu.add(encode_b64)
		encode_submenu.add(encode_url)
		encode_submenu.add(encode_hex)		
		encode.set_submenu(encode_submenu)
		
		decode=Gtk.MenuItem(label="Decode")
		decode_submenu=Gtk.Menu()
		decode_b64=Gtk.MenuItem(label="Base 64")
		decode_b64.connect("activate",self.encoder,"DECODE","B64")
		decode_url=Gtk.MenuItem(label="URL")
		decode_url.connect("activate",self.encoder,"DECODE","URL")
		decode_hex=Gtk.MenuItem(label="ASCII Hex")
		decode_hex.connect("activate",self.encoder,"DECODE","HEX")
		decode_submenu.add(decode_b64)
		decode_submenu.add(decode_url)
		decode_submenu.add(decode_hex)		
		decode.set_submenu(decode_submenu)

		menu.add(Gtk.SeparatorMenuItem())
		menu.add(encode)
		menu.add(decode)

		if len(self.get_buffer().get_selection_bounds()) != 2 or self.get_sensitive() == False:
			encode.set_sensitive(False)
			decode.set_sensitive(False)

		menu.show_all()

	def encoder(self,menuitem,operation,mode):
		iter1,iter2=self.get_buffer().get_selection_bounds()
		text=self.get_buffer().get_text(iter1,iter2,False)		

		if operation == "ENCODE":
			try:			
				if mode == "B64":
					self.get_buffer().replace(iter1,iter2,b64encode(text))
				if mode == "HEX":
					self.get_buffer().replace(iter1,iter2,hexlify(text))
				if mode == "URL":
					self.get_buffer().replace(iter1,iter2,quote_plus(text))
			except:
				dialogs.warning("Encode Failed", "Unable to encode text")
	
		elif operation == "DECODE":
			try:
				if mode == "B64":
					self.get_buffer().replace(iter1,iter2,b64decode(text))
				if mode == "HEX":
					self.get_buffer().replace(iter1,iter2,unhexlify(text))
				if mode == "URL":
					self.get_buffer().replace(iter1,iter2,unquote(text))
			except:
				dialogs.warning("Decode Failed", "Unable to decode text")

class ButtonToggleGroup():
	pass


class TreeStore(Gtk.TreeStore):
	
	def contains(self,parent,pairs):
		for child in self.get_children(parent):
			matches_constraints=True
			for pair in pairs:
				#Pair[0] = string
				#Pair[1] = position
				if not self.get_value(child,pair[1]) == pair[0]:
					matches_constraints=False			
			if matches_constraints:			
				return child	
		return None

	def get_children(self,parent):
		return [self.iter_nth_child(parent,child_no) for child_no in range(0,self.iter_n_children(parent))]



	def get_b64_value(iter,column):
		return b64encode(self.get_value(iter,column))

