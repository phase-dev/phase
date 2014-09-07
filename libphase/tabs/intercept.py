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


from libphase import gtk,error
from libphase.tabs import tab
from gi.repository import Gtk
from gi.repository import GtkSource
from gi.repository import GObject

import Queue
import StringIO

from libmproxy.protocol import http

from libphase import http_client

import threading

from netlib.odict import ODict,ODictCaseless

class Intercept(tab.Tab):

	current_request=None
	current_response=None
	binary_response=False

	def __init__(self,shared_objects):
		tab.Tab.__init__(self,shared_objects)
		self.proxy=shared_objects.proxy
		self.history=shared_objects.history
		self.sitemap=shared_objects.sitemap
		self.vulnerabilities=shared_objects.vulnerabilities

		self.view_intercept_headers=gtk.HTTPView()
		self.builder.get_object("boxInterceptHeaders").add(self.view_intercept_headers)	
		self.view_intercept_headers.set_sensitive(False)

		self.view_intercept_body=gtk.HTTPView(webkit=True)
		self.builder.get_object("boxInterceptBody").add(self.view_intercept_body)
		self.view_intercept_body.set_sensitive(False)


		lang_manager = GtkSource.LanguageManager()
		self.view_intercept_body.text_buffer.set_language(lang_manager.get_language('html'))

		self.request_intercept_queue=Queue.Queue()	
		self.response_intercept_queue=Queue.Queue()

		self.builder.get_object("toolbuttonProxySend").connect("clicked",self.handler_button_send)
		self.builder.get_object("toolbuttonProxyCancel").connect("clicked",self.handler_button_cancel)
		self.builder.get_object("toolbuttonProxySend").set_sensitive(False)
		self.builder.get_object("toolbuttonProxyCancel").set_sensitive(False)


	def clear(self):
		self.builder.get_object("toolbuttonProxyRequest").set_active(False)
		self.builder.get_object("toolbuttonProxyResponse").set_active(False)
		self.handler_button_cancel(None)

	def request_intercept(self,flow):
		flow.request.anticomp()
		flow.request.anticache()

		if len(self.config.proxy.ignored_extensions) > 0 and self.config.proxy.ignored_extensions.match(flow.request.get_url()):
			flow.ignore=True
			flow.request.reply()
			return

		elif self.current_request == None and self.current_response==None:
			if self.builder.get_object("toolbuttonProxyRequest").get_active():
				self.current_request=flow
				GObject.idle_add(self.load_request,flow)
			else:
				flow.request.reply()
		else:
			self.request_intercept_queue.put(flow)

	def response_intercept(self,flow):

		if self.config.authentication.type=="NTLM" and "WWW-Authenticate" in flow.response.headers:
			if "NTLM" in flow.response.headers["WWW-Authenticate"]:
				client=http_client.HTTPClient(self.config)
				client.ntlm_replay(flow)


		if flow.ignore:
			flow.response.reply()
			return

		if self.current_response == None:
			if self.builder.get_object("toolbuttonProxyResponse").get_active():
				self.current_response=flow
				GObject.idle_add(self.load_response,flow)
			else:
				GObject.idle_add(self.process_response,flow)
				flow.response.reply()
				self.send_next()
		else:
			self.response_intercept_queue.put(flow)


	def process_response(self,flow):
		self.history.add_item(flow)
		self.sitemap.add_item(flow)
		self.vulnerabilities.process(flow)	

	def handle_error(self,error):
		error.reply()		
		self.send_next()

	def send_next(self):

		try:
			self.current_response=self.response_intercept_queue.get_nowait()
			if self.builder.get_object("toolbuttonProxyResponse").get_active():
				GObject.idle_add(self.load_response,self.current_response)
				return
			else:
				self.current_response.response.reply()
				self.send_next()
				return

		except Queue.Empty:
			self.current_response=None


		try:
			self.current_request=self.request_intercept_queue.get_nowait()
			if self.builder.get_object("toolbuttonProxyRequest").get_active():
				GObject.idle_add(self.load_request,self.current_request)
			else:
				self.current_request.request.reply()
		except Queue.Empty:
			self.current_request=None

	def load_request(self,flow):		
		if flow == None:
			self.view_intercept_headers.text_buffer.clear()
			self.view_intercept_body.text_buffer.clear()
			self.builder.get_object("toolbuttonProxySend").set_sensitive(False)
			self.builder.get_object("toolbuttonProxyCancel").set_sensitive(False)
			self.view_intercept_headers.set_sensitive(False)
			self.view_intercept_body.set_sensitive(False)

		else:
			self.builder.get_object("notebookMain").set_current_page(0)
			self.view_intercept_headers.text_buffer.clear()
			self.view_intercept_body.text_buffer.clear()
			self.view_intercept_headers.text_buffer.set_text(flow.request.get_headers())
			self.view_intercept_body.text_buffer.set_text(flow.request.content)
			self.view_intercept_body.text_view.set_content_type(flow.request.headers["Content-Type"])
			self.builder.get_object("toolbuttonProxySend").set_sensitive(True)
			self.builder.get_object("toolbuttonProxyCancel").set_sensitive(True)
			self.view_intercept_headers.set_sensitive(True)
			self.view_intercept_body.set_sensitive(True)

	def load_response(self,flow):
		if flow == None:
			self.view_intercept_headers.text_buffer.clear()
			self.view_intercept_body.text_buffer.clear()
			self.builder.get_object("toolbuttonProxySend").set_sensitive(False)
			self.builder.get_object("toolbuttonProxyCancel").set_sensitive(False)
			self.view_intercept_headers.set_sensitive(False)
			self.view_intercept_body.set_sensitive(False)
		else:
			self.builder.get_object("notebookMain").set_current_page(0)
			self.builder.get_object("toolbuttonProxySend").set_sensitive(True)
			self.builder.get_object("toolbuttonProxyCancel").set_sensitive(True)
			self.view_intercept_headers.set_sensitive(True)
			self.view_intercept_body.set_sensitive(True)

			self.view_intercept_headers.text_buffer.clear()
			self.view_intercept_body.text_buffer.clear()
			self.view_intercept_headers.text_buffer.set_text(flow.response.get_headers(remove_transfer_encoding=True))
			self.binary_response=False			
			try:	
				self.current_response.response.content.decode("utf-8")
				self.view_intercept_body.text_buffer.set_text(flow.response.content)
				self.view_intercept_body.text_view.set_content_type(flow.response.headers["Content-Type"])
			except UnicodeDecodeError:
				self.builder.get_object("scrolledwindowInterceptBody").set_sensitive(False)
				self.view_intercept_body.text_buffer.set_text("Binary Response")
				self.binary_response=True
			



	def send_response(self,flow,process=True):
		flow.response.reply()
		if process:
			self.process_response(flow)
		self.send_next()

	def send_null_response(self,flow):
		flow.client_conn.send(flow.response._assemble())
		flow.client_conn.finish()
		self.send_next()

	def handler_button_send(self,button):
		if self.current_response != None:
			if self.binary_response:
				altered_http_response=self.current_response.response.from_string(self.view_intercept_headers.text_buffer.get_all_text()+"\r\n",self.current_response.request.method)
				self.current_response.response.code=altered_http_response.code
				self.current_response.response.headers=altered_http_response.headers		
			else:			
				altered_http_response=self.current_response.response.from_string(self.view_intercept_headers.text_buffer.get_all_text()+"\r\n"+self.view_intercept_body.text_buffer.get_all_text(),self.current_response.request.method)
				self.current_response.response.code=altered_http_response.code
				self.current_response.response.headers=altered_http_response.headers
				self.current_response.response.content=altered_http_response.content
			self.load_response(None)
			send_response_thread=threading.Thread(target=self.send_response,args=(self.current_response,))
			send_response_thread.start()
			
		else:
			altered_http_request=self.current_request.request.from_string(self.view_intercept_headers.text_buffer.get_all_text()+"\r\n"+self.view_intercept_body.text_buffer.get_all_text(),update_content_length=self.shared_objects.builder.get_object("checkbuttonInterceptContentLength").get_active())
			self.current_request.request.method=altered_http_request.method
			self.current_request.request.scheme=altered_http_request.scheme
			self.current_request.request.host=altered_http_request.host
			self.current_request.request.path=altered_http_request.path
			self.current_request.request.httpversion=altered_http_request.httpversion
			self.current_request.request.headers=altered_http_request.headers
			self.current_request.request.content=altered_http_request.content
			self.load_request(None)			
			send_request_thread=threading.Thread(target=self.current_request.request.reply)
			send_request_thread.start()


	def handler_button_cancel(self,button):
		if self.current_response != None:
			self.current_response.response.code=200
			self.current_response.response.headers=ODict()
			self.current_response.response.headers["Cache-Control"]=["no-store,no-cache"]
			self.current_response.response.headers["Pragma"]=["no-cache"]
			error_page=error.error_page % (200, "OK", 200, "User Cancelled Response")
			self.current_response.response.headers["Content-Length"]=[str(len(error_page))]
			self.current_response.response.content=error_page
			self.load_response(None)
			send_response_thread=threading.Thread(target=self.send_response,args=(self.current_response,False))
			send_response_thread.start()
			
		elif self.current_request != None:
			headers=ODictCaseless()
			headers["Cache-Control"]=["no-store,no-cache"]
			headers["Pragma"]=["no-cache"]
			error_page=error.error_page % (200, "OK", 200, "User Cancelled Request")
			headers["Content-Length"]=[str(len(error_page))]
			self.current_request.response=http.HTTPResponse((1,1),200,"OK",headers,error_page)
			self.load_request(None)
			send_response_thread=threading.Thread(target=self.send_null_response,args=(self.current_request,))
			send_response_thread.start()

