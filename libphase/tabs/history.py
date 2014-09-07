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

import os
import sys
import uuid
import threading
import subprocess

import xml.etree.cElementTree as ET
import webbrowser
import urlparse


class History(tab.Tab):
	
	request_id=0

	def __init__(self,shared_objects):
		tab.Tab.__init__(self,shared_objects)

		self.request=shared_objects.request

		treeview_history_cell_1 = Gtk.CellRendererText()
		treeview_history_column_1 = Gtk.TreeViewColumn("ID", treeview_history_cell_1)
		treeview_history_column_1.set_cell_data_func(treeview_history_cell_1,self.data_function,0)
		treeview_history_cell_2 = Gtk.CellRendererText()		
		treeview_history_column_2 = Gtk.TreeViewColumn("Method", treeview_history_cell_2)
		treeview_history_column_2.set_cell_data_func(treeview_history_cell_2,self.data_function,1)
		treeview_history_cell_3 = Gtk.CellRendererText()
		treeview_history_column_3 = Gtk.TreeViewColumn("URL", treeview_history_cell_3)
		treeview_history_column_3.set_cell_data_func(treeview_history_cell_3,self.data_function,2)
		treeview_history_cell_4 = Gtk.CellRendererText()
		treeview_history_column_4 = Gtk.TreeViewColumn("Response Code", treeview_history_cell_4)
		treeview_history_column_4.set_cell_data_func(treeview_history_cell_4,self.data_function,3)

		self.view=self.builder.get_object("treeviewHistory")
		self.view.append_column(treeview_history_column_1)
		self.view.append_column(treeview_history_column_2)
		self.view.append_column(treeview_history_column_3)
		self.view.append_column(treeview_history_column_4)
		self.store=Gtk.ListStore(object)
		self.view.set_model(self.store)
		self.view.connect("button-press-event",self.handler_treeview_history_clicked)
		self.view.connect("cursor-changed",self.handler_treeview_history_cursor_changed)


		self.view_history_request=gtk.HTTPView()
		self.view_history_response=gtk.HTTPView(webkit=True)
		self.view_history_request.text_view.set_editable(False)
		self.view_history_response.text_view.set_editable(False)
		self.builder.get_object("boxHistoryRequest").add(self.view_history_request)	
		self.builder.get_object("boxHistoryResponse").add(self.view_history_response)


		self.builder.get_object("menuitemHistoryOpen").connect("activate",self.handler_menuitem_open_clicked)
		self.builder.get_object("menuitemHistoryCopy").connect("activate",self.handler_menuitem_copy_clicked)
		self.builder.get_object("menuitemHistorySaveRequest").connect("activate",self.handler_menuitem_save_clicked,"Request")
		self.builder.get_object("menuitemHistorySaveResponse").connect("activate",self.handler_menuitem_save_clicked,"Response")
		self.builder.get_object("menuitemHistorySQLMap").connect("activate",self.handler_menuitem_send_to_sqlmap_clicked)
		self.builder.get_object("menuitemHistoryResend").connect("activate",self.handler_menuitem_history_resend)


	def save(self,root):
		history_node = ET.SubElement(root, "history")
		for flow, in self.store:
			flow_node = ET.SubElement(history_node, "flow")
			flow_node.set("id",str(flow.id))
			flow_node.text=flow.save()

	def load(self,xml):
		for element in xml.phase.history:
			if element.name==u"flow":
				flow=HTTPFlow.load(element.text)
				flow.id=int(element["id"])
				self.request_id=int(element["id"])
				self.store.append([flow])

	def clear(self):
		self.request_id=0
		self.store.clear()
		self.view_history_request.text_buffer.clear()
		self.view_history_response.text_buffer.clear()

	def add_item(self,flow):
		if self.builder.get_object("checkbuttonRecordHistory").get_active():
			self.request_id+=1
			flow.id=self.request_id
			self.store.append([flow])

	def handler_treeview_history_clicked(self,treeview,event):
		path=treeview.get_path_at_pos(int(event.x), int(event.y))
		if path:
			if event.button == 3:
				self.builder.get_object("menuHistory").popup(None, None,None, None, event.button, event.time)


	def handler_treeview_history_cursor_changed(self,treeview):
		model,iter=self.view.get_selection().get_selected()
		flow=self.view.get_model().get_value(iter,0)
		self.view_history_request.text_buffer.set_text(flow.request.to_string().strip())
		self.view_history_response.text_buffer.set_text(flow.response.to_string().strip())
		self.view_history_request.text_view.set_content_type(flow.request.headers["Content-Type"])	
		self.view_history_response.text_view.set_content_type(flow.response.headers["Content-Type"])	


	def handler_menuitem_open_clicked(self,button):
		model,iter=self.view.get_selection().get_selected()
		url=self.view.get_model().get_value(iter,0).request.get_url()
		webbrowser.open(url)

	def handler_menuitem_copy_clicked(self,button):
		model,iter=self.view.get_selection().get_selected()
		url=self.view.get_model().get_value(iter,0).request.get_url()
		Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(url,len(url))

	def handler_menuitem_save_clicked(self,button,save_type):
		
		dialog = Gtk.FileChooserDialog(title="Save "+save_type,action=Gtk.FileChooserAction.SAVE,buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
		response=dialog.run()

 
		if response == Gtk.ResponseType.OK:
			model,iter=self.view.get_selection().get_selected()
			flow=model.get_value(iter,0)
			save_file=open(dialog.get_filename(),"w")
			if save_type == "Request":
				new_flow=flow.copy()
				new_flow.request.path=new_flow.request.get_url()
				save_file.write(new_flow.request.to_string())		
			else:
				save_file.write(flow.response.to_string())
			save_file.close()

		dialog.destroy()

	def handler_menuitem_send_to_sqlmap_clicked(self,button):
		model,iter=self.view.get_selection().get_selected()
		flow=model.get_value(iter,0)
		temp_filepath="/tmp/"+str(uuid.uuid4())
		temp_file=open(temp_filepath,"w")
		temp_file.write(flow.request.to_string())	
		temp_file.close()		
		threading.Thread(target=self.sqlmap_thread,args=(self.config.external_tools.sqlmap, temp_filepath,)).start()
		
	def sqlmap_thread(self,sqlmap_path,temp_filepath):
		
		terminal_process=subprocess.Popen("/usr/bin/gnome-terminal -e \""+os.path.dirname(sys.argv[0])+"/bash/sqlmap "+sqlmap_path+" "+temp_filepath+"\"",shell=True)

	def data_function(self,column,cell,model,iter,user_data):
		cell_contents=model.get_value(iter,0)

		if user_data==0:
			cell.set_property('text',str(cell_contents.id))
		elif user_data==1:
			cell.set_property('text',cell_contents.request.method)
		elif user_data==2:
			cell.set_property('text',cell_contents.request.get_url())
		elif user_data==3:
			cell.set_property('text',str(cell_contents.response.code))

	def handler_menuitem_history_resend(self,button):
		model,iter=self.view.get_selection().get_selected()
		flow=self.view.get_model().get_value(iter,0)
		parsed_url=urlparse.urlparse(flow.request.get_url())
		self.builder.get_object("entryRequestURL").set_text(parsed_url.scheme+"://"+parsed_url.netloc)
		self.request.textview_request.get_buffer().set_text(flow.request.to_string())
		self.request.textview_response.get_buffer().clear()
		self.builder.get_object("notebookMain").set_current_page(4)
