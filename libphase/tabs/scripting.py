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


from libphase import gtk,dialogs
from libphase.tabs import tab

from libmproxy.protocol import http

import traceback
import base64
import xml.etree.cElementTree as ET

class Scripting(tab.Tab):
	
	def __init__(self,shared_objects,set_script_request_function,set_script_response_function):
		tab.Tab.__init__(self,shared_objects)
		self.set_script_request_function=set_script_request_function
		self.set_script_response_function=set_script_response_function

		self.textbuffer_scripting_request=gtk.TextBuffer()
		self.textbuffer_scripting_response=gtk.TextBuffer()

		self.textbuffer_scripting_request.set_text("def request(request):\n\t#Your code here\n\treturn request")
		self.textbuffer_scripting_response.set_text("def response(response):\n\t#Your code here\n\treturn response")

		self.textview_scripting_request=GtkSource.View.new_with_buffer(self.textbuffer_scripting_request)
		self.textview_scripting_response=GtkSource.View.new_with_buffer(self.textbuffer_scripting_response)
		lang_manager = GtkSource.LanguageManager()
		self.textbuffer_scripting_request.set_language(lang_manager.get_language('python'))
		self.textbuffer_scripting_response.set_language(lang_manager.get_language('python'))
		self.builder.get_object("scrolledwindowMainScriptingRequest").add(self.textview_scripting_request)
		self.builder.get_object("scrolledwindowMainScriptingResponse").add(self.textview_scripting_response)

		self.builder.get_object("togglebuttonScriptRequest").connect("toggled",self.handler_toggle_script_enable,"REQUEST")
		self.builder.get_object("togglebuttonScriptResponse").connect("toggled",self.handler_toggle_script_enable,"RESPONSE")



	def save(self,root):
		scripting_node = ET.SubElement(root, "scripting")
		request_node = ET.SubElement(scripting_node, "request")
		response_node = ET.SubElement(scripting_node, "response")
		request_node.text=base64.b64encode(self.textbuffer_scripting_request.get_all_text())
		response_node.text=base64.b64encode(self.textbuffer_scripting_response.get_all_text())
		

	def load(self,xml):
		self.textbuffer_scripting_request.set_text(base64.b64decode(xml.phase.scripting.request.text))
		self.textbuffer_scripting_response.set_text(base64.b64decode(xml.phase.scripting.response.text))


	def clear(self):
		self.builder.get_object("togglebuttonScriptRequest").set_active(False)
		self.builder.get_object("togglebuttonScriptRequest").set_active(False)
		self.textbuffer_scripting_request.set_text("def request(request):\n\t#Your code here\n\treturn request")
		self.textbuffer_scripting_response.set_text("def response(response):\n\t#Your code here\n\treturn response")

	def handler_toggle_script_enable(self,button,script_type):

		if button.get_active():
			if script_type=="REQUEST":
				test_request_object=http.HTTPRequest.from_string("GET / HTTP/1.1\r\nHost:doesnotexist\r\n\r\na=1&b=2\r\n\r\n")
				script=self.textbuffer_scripting_request.get_all_text()
				try:
					exec(script)
				except:
					dialogs.warning("Invalid Script",traceback.format_exc().replace(">","&gt;").replace("<","&lt;"))
					button.set_active(False)
					return
	
				try:
					modified_test_request_object=request(test_request_object)
				except NameError:
					dialogs.warning("Invalid Script","This script does not define the function <b>request</b>")
					button.set_active(False)
					return
				except TypeError:
					dialogs.warning("Invalid Script","This script does not accept a single argument <b>request</b>")
					button.set_active(False)
					return

				if not isinstance(modified_test_request_object,http.HTTPRequest):
					dialogs.warning("Invalid Script","This script does not return a HTTPRequest object")
					button.set_active(False)
					return
				
				self.textview_scripting_request.set_sensitive(False)
				self.set_script_request_function(request)
			
			elif script_type=="RESPONSE":
				test_response_object=http.HTTPResponse.from_string("HTTP/1.1 200 OK\r\Content-Length: 58\r\n\r\n<html><head><title>Test</title></head><body></body></html>","GET")
				script=self.textbuffer_scripting_response.get_all_text()
				try:
					exec(script)
				except:
					dialogs.warning("Invalid Script",traceback.format_exc().replace(">","&gt;").replace("<","&lt;"))
					button.set_active(False)
					return
	
				try:
					modified_test_response_object=response(test_response_object)
				except NameError:
					dialogs.warning("Invalid Script","This script does not define the function <b>response</b>")
					button.set_active(False)
					return
				except TypeError:
					dialogs.warning("Invalid Script","This script does not accept a single argument <b>response</b>")
					button.set_active(False)
					return

				if not isinstance(modified_test_response_object,http.HTTPResponse):
					dialogs.warning("Invalid Script","This script does not return a HTTPResponse object")
					button.set_active(False)
					return
				
				self.textview_scripting_response.set_sensitive(False)
				self.set_script_response_function(response)

		else:
			if script_type=="REQUEST":	
				self.textview_scripting_request.set_sensitive(True)
				self.set_script_request_function(None)
			if script_type=="RESPONSE":	
				self.textview_scripting_response.set_sensitive(True)
				self.set_script_response_function(None)

