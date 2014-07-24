#! /usr/bin/python
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

Phase incorporates the netlib and libmproxy libraries from the mitmproxy project, version 0.8 (c) 2010 Aldo Cortesi.

The licence for mitmproxy includes the following addition, which is extended to the modifications to these libraries included
with Phase:

In addition, as a special exception, the copyright holders give
permission to link the code of this program or portions of this
program with the OpenSSL project's "OpenSSL" library (or with modified
versions of it that use the same license as the "OpenSSL" library),
and distribute linked combinations including the two. 

You must obey the GNU General Public License in all respects for all
of the code used other than "OpenSSL".  If you modify file(s) provided
under this license, you may extend this exception to your version of
the file, but you are not obligated to do so. If you do not wish to do
so, delete this exception statement from your version.

"""
import gi
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GtkSource

import libmproxy
from libmproxy import controller,proxy

from libphase import config, gtk, utilities, dialogs, http_client
from libphase.tabs import intercept, history, scripting, sitemap, vulnerabilities, processes, request
from libphase.windows import encoder, settings

import threading
import xml.etree.cElementTree as ET
from bs4 import BeautifulSoup
import argparse
import os
import sys
from os.path import expanduser,exists
import base64

class Proxy(controller.Master,threading.Thread):

	def __init__(self,server,request_handler,response_handler,error_handler):
		controller.Master.__init__(self,server)
		threading.Thread.__init__(self)
		self.request_handler=request_handler
		self.response_handler=response_handler
		self.error_handler=error_handler
        
	def stop(self):
		self.shutdown()

	def handle_request(self,request):
		self.request_handler(request.flow)

	def handle_response(self,response):
		self.response_handler(response.flow)

	def handle_error(self,error):
		self.error_handler(error)

class PhaseGUI():

	filename=None
	save_required=False

	class SharedObjects():
		pass

	script_request_function=None
	script_response_function=None

	def restart_proxy(self):
		if self.shared_objects.proxy:
			self.shared_objects.proxy.stop()
		try:
			server = proxy.ProxyServer(self.shared_objects.config.generate_libmproxy_config(), self.shared_objects.config.proxy.port)
			self.shared_objects.proxy=Proxy(server,self.handle_request,self.handle_response,self.handle_error)
			self.shared_objects.proxy.start()
		except libmproxy.proxy.ProxyServerError:
			dialogs.warning("Port in use", "Phase is unable to start the proxy service on port "+str(self.shared_objects.config.proxy.port)+". Another service is listening on this port.")


	def __init__(self,config):
	
		self.shared_objects=self.SharedObjects()
		self.shared_objects.proxy=None
		self.shared_objects.config=config
		self.shared_objects.restart_proxy=self.restart_proxy

		#Setup GTK
		self.shared_objects.builder = Gtk.Builder()
		self.shared_objects.builder.add_from_file(os.path.abspath(os.path.dirname(sys.argv[0]))+os.sep+"phase.glade")
		self.shared_objects.builder.get_object("toolbarMain").get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

		#Window Management and Start GTK Loop
		#self.shared_objects.builder.get_object("windowMain").connect("destroy",self.handler_window_main_destroy)
		self.shared_objects.builder.get_object("windowMain").connect("delete-event",self.handler_window_main_destroy)
		self.shared_objects.builder.get_object("windowMain").show_all()

		if not exists(self.shared_objects.config.directory):
			if dialogs.disclaimer() != Gtk.ResponseType.OK:
				sys.exit()
			os.mkdir(self.shared_objects.config.directory)
			os.mkdir(self.shared_objects.config.directory+os.sep+"ca")
			os.mkdir(self.shared_objects.config.directory+os.sep+"client")
		config.load()
		parser = argparse.ArgumentParser()
		parser.add_argument("filename", nargs="?", help=".phase File To Open")
		#parser.add_argument("--debug-plugins", help="Allow Plugins to Raise Exceptions",  action="store_true")
		self.args=parser.parse_args()






		#Setup Tabs
		self.shared_objects.request=request.Request(self.shared_objects)	
		self.shared_objects.history=history.History(self.shared_objects)
		self.shared_objects.scripting=scripting.Scripting(self.shared_objects,self.set_script_request_function,self.set_script_response_function)		
		self.shared_objects.sitemap=sitemap.SiteMap(self.shared_objects)
		self.shared_objects.vulnerabilities=vulnerabilities.Vulnerabilities(self.shared_objects)
		self.shared_objects.processes=processes.Processes(self.shared_objects)		

		
			
		

		#Setup Windows
		self.encoder=encoder.Encoder(self.shared_objects,"windowEncoder")
		self.settings=settings.Settings(self.shared_objects,"windowSettings")
	

		self.shared_objects.builder.get_object("toolbuttonNew").connect("clicked",self.handler_button_new_clicked)
		self.shared_objects.builder.get_object("toolbuttonSave").connect("clicked",self.handler_button_save_clicked)
		self.shared_objects.builder.get_object("toolbuttonOpen").connect("clicked",self.handler_button_open_clicked)

		self.shared_objects.builder.get_object("toolbuttonEncoder").connect("clicked",self.handler_button_encoder_clicked)


		

		

		#Setup Proxy Server
		GObject.threads_init()

		try:
			self.shared_objects.server = proxy.ProxyServer(self.shared_objects.config.generate_libmproxy_config(), self.shared_objects.config.proxy.port)
			self.shared_objects.proxy=Proxy(self.shared_objects.server,self.handle_request,self.handle_response,self.handle_error)
			self.shared_objects.proxy.start()
		except libmproxy.proxy.ProxyServerError:
			dialogs.warning("Port in use", "Phase is unable to start the proxy service on port "+str(self.shared_objects.config.proxy.port)+". Another service is listening on this port.")

		self.shared_objects.intercept=intercept.Intercept(self.shared_objects)

		if self.args.filename:
			self.open(self.args.filename)
		
		
		self.shared_objects.builder.get_object("windowMain").show_all()
		Gtk.main()


	def set_script_request_function(self,function):
		self.script_request_function=function

	def set_script_response_function(self,function):
		self.script_response_function=function


	def exit(self):
		if self.shared_objects.proxy:
			self.shared_objects.proxy.stop()
		self.shared_objects.vulnerabilities.stop()
		Gtk.main_quit()		


	#End proxy thread and gracefully exit GTK when "x" clicked
	def handler_window_main_destroy(self,widget,event):
		if self.save_required:
			response=dialogs.exit_warning()

			if response == 0:
				self.exit()
			elif response == 1:
				return True
			elif response == 2:
				if self.filename:
					self.save(self.filename)
					self.exit()
				else:
					dialog = Gtk.FileChooserDialog(title="Save As",action=Gtk.FileChooserAction.SAVE,buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
					phase_filter = Gtk.FileFilter()
					phase_filter.add_pattern("*.phase")
					phase_filter.set_name("Phase File")
					dialog.add_filter(phase_filter)
					dialog.set_current_name(".phase")
					response=dialog.run()

					if response == Gtk.ResponseType.OK:
						self.open(dialog.get_filename())
						dialog.destroy()
						self.exit()
					else:
						dialog.destroy()
						return True
		else:
			self.exit()

	def handle_request(self,flow):
		self.save_required=True

		if self.shared_objects.config.authentication.type=="Basic":
			flow.request.headers["Authorization"]=["Basic "+base64.b64encode(self.shared_objects.config.authentication.basic_username+":"+self.shared_objects.config.authentication.basic_password)]

		if self.script_request_function != None:
			flow.request=self.script_request_function(flow.request)
		self.shared_objects.intercept.request_intercept(flow)

	def handle_response(self,flow):
		self.save_required=True
		if self.script_response_function != None:
			flow.response=self.script_response_function(flow.response)
		self.shared_objects.intercept.response_intercept(flow)

	def handle_error(self,error):
		self.shared_objects.intercept.handle_error(error)
	
	def handler_button_new_clicked(self,button):
		self.clear()


	def clear(self):
		self.shared_objects.builder.get_object("windowMain").set_title("Phase - Python HTTP Attack and Scripting Environment")
		self.shared_objects.intercept.clear()
		self.shared_objects.history.clear()
		self.shared_objects.scripting.clear()
		self.shared_objects.sitemap.clear()
		self.shared_objects.vulnerabilities.clear()

	def handler_button_save_clicked(self,button):

		if self.filename:
			self.save(self.filename)
		else:
			dialog = Gtk.FileChooserDialog(title="Save As",action=Gtk.FileChooserAction.SAVE,buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
			phase_filter = Gtk.FileFilter()
			phase_filter.add_pattern("*.phase")
			phase_filter.set_name("Phase File")
			dialog.add_filter(phase_filter)
			dialog.set_current_name(".phase")
			response=dialog.run()
	 
			if response == Gtk.ResponseType.OK:
				self.save(dialog.get_filename())
			dialog.destroy()

	def handler_button_open_clicked(self,button):
		dialog = Gtk.FileChooserDialog(title="Open",action=Gtk.FileChooserAction.OPEN,buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		phase_filter = Gtk.FileFilter()
		phase_filter.add_pattern("*.phase")
		phase_filter.set_name("Phase File")
		dialog.add_filter(phase_filter)
		response=dialog.run()
 
		if response == Gtk.ResponseType.OK:
			self.open(dialog.get_filename())
		dialog.destroy()

	def handler_button_encoder_clicked(self,button):
		self.encoder.show()

	def save(self,filename):
		root = ET.Element("phase")
		self.shared_objects.history.save(root)
		self.shared_objects.scripting.save(root)
		self.shared_objects.sitemap.save(root)
		self.shared_objects.vulnerabilities.save(root)
		tree = ET.ElementTree(root)

		if filename[-6:] != ".phase":
			filename+=".phase"
		tree.write(filename)
		self.filename=os.path.abspath(filename)
		self.shared_objects.builder.get_object("windowMain").set_title("Phase - Python HTTP Attack and Scripting Environment ("+self.filename+")")
		self.save_required=False

	def open(self,filename):
		save_file=open(filename)
		xml=BeautifulSoup(save_file.read(),"xml")
		save_file.close()
		self.filename=os.path.abspath(filename)
		self.clear()
		self.shared_objects.history.load(xml)
		self.shared_objects.scripting.load(xml)
		self.shared_objects.sitemap.load(xml)
		self.shared_objects.vulnerabilities.load(xml)

		self.shared_objects.builder.get_object("windowMain").set_title("Phase - Python HTTP Attack and Scripting Environment ("+self.filename+")")
		self.save_required=False

phase=PhaseGUI(config.Config(expanduser("~")+os.sep+".phase"))
