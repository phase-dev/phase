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
from libphase import brute_forcer,spider,http_client

from gi.repository import Gtk

class Processes(tab.Tab):

	def __init__(self,shared_objects):
		tab.Tab.__init__(self,shared_objects)

		self.sitemap=shared_objects.sitemap

		self.store=Gtk.ListStore(str,int,object)
		self.view=self.builder.get_object("treeviewProcesses")
	
		process_cell1 = Gtk.CellRendererText()
		process_cell2 = Gtk.CellRendererProgress()
		process_column1 = Gtk.TreeViewColumn("Process", process_cell1, text=0)
		process_column2 = Gtk.TreeViewColumn("Progress", process_cell2, value=1)
		self.view.append_column(process_column1)
		self.view.append_column(process_column2)
		self.view.set_model(self.store)
		self.builder.get_object("menuitemSitemapBruteForce").connect("activate",self.handler_brute_force_clicked)
		self.builder.get_object("menuitemSitemapSpider").connect("activate",self.handler_spider_clicked)
		self.builder.get_object("menuitemProcessesStop").connect("activate",self.handler_stop_clicked)
		self.builder.get_object("menuitemProcessesView").connect("activate",self.handler_process_view_clicked)
		self.view.connect("button-press-event",self.handler_view_clicked)


	def handler_view_clicked(self,treeview,event):
		path=treeview.get_path_at_pos(int(event.x), int(event.y))
		if path:
			if event.button == 3:
				self.builder.get_object("menuProcesses").popup(None, None,None, None, event.button, event.time)


	def handler_stop_clicked(self,button):
		model,iter=self.view.get_selection().get_selected()		
		process=model.get_value(iter,2)
		process.stop()

	def handler_process_view_clicked(self,button):
		model,iter=self.view.get_selection().get_selected()		
		process=model.get_value(iter,2)
		process.view.show_all()

	def handler_brute_force_clicked(self,button):
		
		model,iter=self.sitemap.view.get_selection().get_selected()
		url=self.sitemap.reconstruct_url(iter)
		self.new_brute_force(url)

	
	def handler_spider_clicked(self,button):
		model,iter=self.sitemap.view.get_selection().get_selected()
		url=self.sitemap.reconstruct_url(iter)
		self.new_spider(url)


	def new_spider(self,url):
		sp=spider.Spider(self.config, url, self.add_function,self.progress_function,self.finished_function)
		iter=self.store.append(["Spider: "+url,0,sp])
		sp.iter=iter
		sp.start()

	def new_brute_force(self,url):
		dialog=brute_forcer.DialogBruteForce(self.builder.get_object("windowMain"),url)
		response = dialog.run()

		if response == Gtk.ResponseType.OK:

			if url[-1:] != "/":
				url=url+"/"
		
			bf=brute_forcer.BruteForce(self.config,url,dialog.wordlist_files[dialog.word_list.get_active()],dialog.recursive.get_active(),self.add_function,self.progress_function,self.finished_function)
			iter=self.store.append(["Brute Force: "+url,0,bf])
			bf.iter=iter
			bf.start()

		dialog.destroy()
		

	def add_function(self,url):
		self.sitemap.add_url(url)

	def progress_function(self,iter,current_total,total):
		self.store.set_value(iter,1,int(float(current_total)/float(total)*float(100)))

	def finished_function(self,iter):
		self.store.set_value(iter,1,100)
