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
from libphase.tabs import tab
from gi.repository import Gtk
from gi.repository import GtkSource

from libmproxy.protocol.http import HTTPFlow
from libphase import http_client,dialogs
import netlib.http

class Request(tab.Tab):
	
	def __init__(self,shared_objects):
		tab.Tab.__init__(self,shared_objects)

		self.view_request=gtk.HTTPView()
		self.view_response=gtk.HTTPView(webkit=True)

		self.builder.get_object("scrolledwindowRequestRequest").add(self.view_request)	
		self.builder.get_object("scrolledwindowRequestResponse").add(self.view_response)
		self.view_response.set_editable(False)

		lang_manager = GtkSource.LanguageManager()
		self.view_response.text_buffer.set_language(lang_manager.get_language('html'))

		self.builder.get_object("buttonRequestSend").connect("clicked",self.handler_send_clicked)



	def handler_send_clicked(self,button):
		url=self.builder.get_object("entryRequestURL").get_text()
		client=http_client.HTTPClient(self.config)

		try:
			request=self.view_request.text_buffer.get_all_text()
			if len(request) == 0:
				dialogs.warning("Invalid HTTP Request","Empty HTTP Request")
				return
			flow=client.request_from_string(url,request,self.builder.get_object("checkbuttonRequestContentLength").get_active())
			
			self.view_response.set_text(flow.response.to_string(remove_transfer_encoding=True))
			
			if self.builder.get_object("checkbuttonRequestHistory").get_active():
				self.shared_objects.history.add_item(flow)

		except netlib.http.HttpError as e:
			dialogs.warning("Invalid HTTP Request",e.msg)
		except netlib.tcp.NetLibError as e:
			dialogs.warning("Network Error",e.message)

	def send(url,request,update_content_length):
		flow=client.request_from_string(url,request,self.builder.get_object("checkbuttonRequestContentLength").get_active())
