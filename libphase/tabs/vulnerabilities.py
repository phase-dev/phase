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


from libphase.tabs import tab
import plugins.vulnerabilities
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GdkPixbuf
from libphase import gtk
import pkgutil
import importlib
import traceback
import sys
import xml.etree.cElementTree as ET
import os
import threading
import Queue
import time

class Vulnerabilities(tab.Tab):

	plugins=[]

	def __init__(self,shared_objects):
		tab.Tab.__init__(self,shared_objects)
	
		icon_dir=os.path.abspath(os.path.dirname(sys.argv[0]))+os.sep+"resources"+os.sep+"icons"+os.sep

		self.info_icon=GdkPixbuf.Pixbuf.new_from_file_at_size(icon_dir+"info.png", 15, 15)
		self.low_icon=GdkPixbuf.Pixbuf.new_from_file_at_size(icon_dir+"low.png", 15, 15)
		self.medium_icon=GdkPixbuf.Pixbuf.new_from_file_at_size(icon_dir+"medium.png", 15, 15)
		self.high_icon=GdkPixbuf.Pixbuf.new_from_file_at_size(icon_dir+"high.png", 15, 15)
		self.critical_icon=GdkPixbuf.Pixbuf.new_from_file_at_size(icon_dir+"critical.png", 15, 15)

		self.view=self.builder.get_object("treeviewVulnerabilities")
		treeview_vulnerabilities_cell_1 = Gtk.CellRendererPixbuf()
		treeview_vulnerabilities_column_1 = Gtk.TreeViewColumn("Risk", treeview_vulnerabilities_cell_1)
		treeview_vulnerabilities_column_1.set_cell_data_func(treeview_vulnerabilities_cell_1,self.data_function)
		self.view.append_column(treeview_vulnerabilities_column_1)
		treeview_vulnerabilities_cell_2 = Gtk.CellRendererText()
		treeview_vulnerabilities_column_2 = Gtk.TreeViewColumn("Title", treeview_vulnerabilities_cell_2, text=0)
		self.view.append_column(treeview_vulnerabilities_column_2)

		self.store=gtk.TreeStore(str,int,str,str,str)
		self.view.set_model(self.store)

		self.view.connect("cursor-changed",self.handler_treeview_vulnerabilities_cursor_changed)

		for importer, modname, ispkg in pkgutil.iter_modules(plugins.vulnerabilities.__path__):
			if modname != "base":
				try:	
					module = importlib.import_module("plugins.vulnerabilities."+modname)
					plugin=module.Plugin()
					self.plugins.append(plugin)
				except:
					print "Failed to import ",modname
					print traceback.format_exc()


		self.processing_queue=Queue.Queue()
		self.finish_processing=False
		self.processing_thread=threading.Thread(target=self.process_thread)
		self.processing_thread.start()

	def data_function(self,column,cell,model,iter,user_data):		
		cell_contents=model.get_value(iter,1)

		
		if cell_contents==5:
			cell.set_property('pixbuf',self.critical_icon)
		if cell_contents==4:
			cell.set_property('pixbuf',self.high_icon)	
		if cell_contents==3:
			cell.set_property('pixbuf',self.medium_icon)	
		if cell_contents==2:
			cell.set_property('pixbuf',self.low_icon)	
		if cell_contents==1:
			cell.set_property('pixbuf',self.info_icon)	

	
	def stop(self):
		self.finish_processing=True


	def process(self,flow):
		if self.builder.get_object("checkbuttonVulnerabilitesDetect").get_active():
			self.processing_queue.put(flow)

	
	def process_thread(self):
		while not self.finish_processing:
			try:
				flow=self.processing_queue.get_nowait()
				for plugin in self.plugins:
					vulnerabilities=plugin.process(flow.copy())
					self.add(vulnerabilities)

			except Queue.Empty:
				time.sleep(0.1)

	def load(self,xml):
		for parent_node in xml.phase.vulnerabilities.children:
			parent=self.store.append(None,[parent_node["title"],int(parent_node["risk"]),parent_node["description"],parent_node["recommendation"],""])
			for child_node in parent_node.children:
				self.store.append(parent,[child_node["url"],int(parent_node["risk"]),parent_node["description"],parent_node["recommendation"],child_node["value"]])


	def save(self,root):
		
		vulnerabilities_node = ET.SubElement(root, "vulnerabilities")
		
		for parent in self.store.get_children(None):
			vuln_node=ET.SubElement(vulnerabilities_node, "vulnerability")
			vuln_node.set("title",self.store.get_value(parent,0))
			vuln_node.set("risk",str(self.store.get_value(parent,1)))
			vuln_node.set("description",self.store.get_value(parent,2))
			vuln_node.set("recommendation",self.store.get_value(parent,3))
					
			for child in self.store.get_children(parent):
				child_node=ET.SubElement(vuln_node, "affected_url")
				child_node.set("url",self.store.get_value(child,0))
				child_node.set("value",self.store.get_value(child,4))
				

	def clear(self):
		self.store.clear()

	def handler_treeview_vulnerabilities_cursor_changed(self,treeview):
		model,iter=self.view.get_selection().get_selected()
		path=model.get_path(iter)
		if len(path) == 1:
			self.builder.get_object("textviewVulnerabilitiesDescription").get_buffer().set_text(treeview.get_model().get_value(iter,2))
			self.builder.get_object("textviewVulnerabilitiesRecommendation").get_buffer().set_text(treeview.get_model().get_value(iter,3))
			self.builder.get_object("textviewVulnerabilitiesValue").get_buffer().set_text("")
		else:
			self.builder.get_object("textviewVulnerabilitiesDescription").get_buffer().set_text(treeview.get_model().get_value(iter,2))
			self.builder.get_object("textviewVulnerabilitiesRecommendation").get_buffer().set_text(treeview.get_model().get_value(iter,3))
			self.builder.get_object("textviewVulnerabilitiesValue").get_buffer().set_text(treeview.get_model().get_value(iter,4))
		

	def add(self,vulnerabilities):
		for vulnerability in vulnerabilities:
			parent=self.store.contains(None,[(vulnerability.title,0)])

			if parent == None:
				parent=self.store.append(None,[vulnerability.title,vulnerability.risk,vulnerability.description,vulnerability.recommendation,""])
				self.store.append(parent,[vulnerability.url,vulnerability.risk,vulnerability.description,vulnerability.recommendation,vulnerability.value])
			else:
				if self.store.contains(parent,[(vulnerability.url,0)]) == None:
					self.store.append(parent,[vulnerability.url,vulnerability.risk,vulnerability.description,vulnerability.recommendation,vulnerability.value])
