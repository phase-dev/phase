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


def handler_toggle_script_enable(self,button,script_type,script_function):

	if button.get_active():
		if script_type=="REQUEST":
			test_request_object=http.HTTPRequest.from_stream(StringIO.StringIO("GET / HTTP/1.1\r\nHost:doesnotexist\r\n\r\na=1&b=2\r\n\r\n"))
			script=self.textbuffer_scripting_request.get_all_text()
			try:
				exec(script)
			except:
				gtk.dialog_warning("Invalid Script",traceback.format_exc().replace(">","&gt;").replace("<","&lt;"))
				button.set_active(False)
				return

			try:
				modified_test_request_object=request(test_request_object)
			except NameError:
				gtk.dialog_warning("Invalid Script","This script does not define the function <b>request</b>")
				button.set_active(False)
				return
			except TypeError:
				gtk.dialog_warning("Invalid Script","This script does not accept a single argument <b>request</b>")
				button.set_active(False)
				return

			if not isinstance(modified_test_request_object,http.HTTPRequest):
				gtk.dialog_warning("Invalid Script","This script does not return a HTTPRequest object")
				button.set_active(False)
				return
			
			self.textview_scripting_request.set_sensitive(False)
			self.script_request_function=request
		
		elif script_type=="RESPONSE":
			test_response_object=http.HTTPResponse.from_stream(StringIO.StringIO("HTTP/1.1 200 OK\r\Content-Length: 58\r\n\r\n<html><head><title>Test</title></head><body></body></html>"),"GET")
			script=self.textbuffer_scripting_response.get_all_text()
			try:
				exec(script)
			except:
				gtk.dialog_warning("Invalid Script",traceback.format_exc().replace(">","&gt;").replace("<","&lt;"))
				button.set_active(False)
				return

			try:
				modified_test_response_object=response(test_response_object)
			except NameError:
				gtk.dialog_warning("Invalid Script","This script does not define the function <b>response</b>")
				button.set_active(False)
				return
			except TypeError:
				gtk.dialog_warning("Invalid Script","This script does not accept a single argument <b>response</b>")
				button.set_active(False)
				return

			if not isinstance(modified_test_response_object,http.HTTPResponse):
				gtk.dialog_warning("Invalid Script","This script does not return a HTTPResponse object")
				button.set_active(False)
				return
			
			self.textview_scripting_response.set_sensitive(False)
			self.script_response_function=response

	else:
		if script_type=="REQUEST":	
			self.textview_scripting_request.set_sensitive(True)
			script_function=None
		if script_type=="RESPONSE":	
			self.textview_scripting_response.set_sensitive(True)
			script_function=None

