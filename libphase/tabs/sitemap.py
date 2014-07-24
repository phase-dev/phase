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
from gi.repository import Gdk



import xml.etree.cElementTree as ET
import urlparse
import webbrowser


class SiteMap(tab.Tab):
	
	def __init__(self,shared_objects):
		tab.Tab.__init__(self,shared_objects)
		#Setup Main TreeView
		
		self.view=self.builder.get_object("treeviewSiteMap")
	
		treeview_sitemap_cell_1 = Gtk.CellRendererText()
		treeview_sitemap_column_1 = Gtk.TreeViewColumn("Site Map", treeview_sitemap_cell_1, text=0)
		self.view.append_column(treeview_sitemap_column_1)
		self.store=gtk.TreeStore(str)
		self.view.set_model(self.store)

		self.view.connect("button-press-event",self.handler_view_clicked)

		self.builder.get_object("menuitemSitemapOpen").connect("activate",self.handler_menu_clicked,"OPEN")
		self.builder.get_object("menuitemSitemapCopy").connect("activate",self.handler_menu_clicked,"COPY")
		self.builder.get_object("menuitemSitemapDelete").connect("activate",self.handler_menu_delete_clicked)


	def clear(self):
		self.store.clear()

	def save(self,root):
		
		def traverse_tree(parent,parent_node):
			child_node=ET.SubElement(parent_node, "path")
			child_node.set("value",self.store.get_value(parent,0))
			for child in self.store.get_children(parent):
				traverse_tree(child,child_node)

		sitemap_node = ET.SubElement(root, "sitemap")
		
		for parent in self.store.get_children(None):
			traverse_tree(parent,sitemap_node)


	def handler_view_clicked(self,treeview,event):
		path=treeview.get_path_at_pos(int(event.x), int(event.y))
		if path:
			if event.button == 3:
				self.builder.get_object("menuSitemap").popup(None, None,None, None, event.button, event.time)
			

	def load(self,xml):

		def traverse_tree(parent,parent_node):
			for child_node in parent_node.children:
				child=self.store.append(parent,[child_node["value"]])
				traverse_tree(child,child_node)

		for parent_node in xml.phase.sitemap.children:
			parent=self.store.append(None,[parent_node["value"]])
			traverse_tree(parent,parent_node)


	def add_item(self,flow):
		if flow.response.code == 200:
			self.add_url(flow.request.get_url())


	def add_url(self,url):
		parsed_url=urlparse.urlparse(url)
		base_url=parsed_url.scheme+"://"+parsed_url.netloc

		parent=None
		for path_element in [base_url]+parsed_url.path.split("/")[1:]:
			if len(path_element) > 0:
				if self.store.contains(parent,[(path_element,0)]):
					parent=self.store.contains(parent,[(path_element,0)])
				else:
					parent=self.store.append(parent,[path_element])


	def handler_menu_clicked(self,button,mode):
		model,iter=self.view.get_selection().get_selected()
		url=self.reconstruct_url(iter)
		if mode == "OPEN":
			webbrowser.open(url)
		if mode == "COPY":
			Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(url,len(url))

	def handler_menu_delete_clicked(self,button):
		model,iter=self.view.get_selection().get_selected()
		self.store.remove(iter)

	def reconstruct_url(self,iter):
		url=self.store.get_value(iter,0)

		parent=self.store.iter_parent(iter)
		while parent != None:
			url=self.store.get_value(parent,0)+"/"+url
			parent=self.store.iter_parent(parent)
		return url
