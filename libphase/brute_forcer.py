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


from libphase import utilities,http_client
from threading import Thread
import Queue
from gi.repository import Gtk
from gi.repository import GObject
import os
import glob
import sys



class DialogBruteForce(Gtk.Dialog):
	def __init__(self, parent,url):
		Gtk.Dialog.__init__(self, "Brute Force", parent, 0, ())
		self.add_button("Cancel",Gtk.ResponseType.CANCEL)
		self.generate_button=self.add_button("Start",Gtk.ResponseType.OK)

		box = self.get_content_area()

	
		self.word_list=Gtk.ComboBox()
		self.wordlist_store=Gtk.ListStore(str)

		wordlist_dir=os.path.abspath(os.path.dirname(sys.argv[0]))+os.sep+"resources"+os.sep+"dirbuster-lists"+os.sep

		self.wordlist_files=[]
		for filename in glob.glob(wordlist_dir+"*.txt"):
			self.wordlist_store.append([filename.replace(wordlist_dir,"")])
			self.wordlist_files.append(filename)

		self.word_list.set_model(self.wordlist_store)		
		wordlist_cell=Gtk.CellRendererText()
		self.word_list.pack_start(wordlist_cell,True)
		self.word_list.add_attribute(wordlist_cell,'text',0)
		self.word_list.set_active(0)

	
		word_list_box=Gtk.Box()
		word_list_box.add(Gtk.Label("Word List:"))
		word_list_box.add(self.word_list)
	
		box.add(word_list_box)
		
		self.recursive=Gtk.CheckButton("Recursive")
		box.add(self.recursive)
		self.show_all()	
		
class DialogBruteForceView(Gtk.Dialog):
	def __init__(self):
		Gtk.Dialog.__init__(self, "Brute Force Status", None, 0, ())
		self.ok_button=self.add_button("OK",Gtk.ResponseType.OK)
		self.ok_button.connect("clicked",self.handler_delete,None)

		box = self.get_content_area()

		self.set_size_request(600,500)
		vbox=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		progress_label=Gtk.Label("Progress:")
		progress_label.set_alignment(0,0)
		vbox.add(progress_label)
		self.progress_bar=Gtk.ProgressBar()
		self.progress_bar.set_size_request(-1,30)
		self.progress_bar.set_show_text(True)
		vbox.add(self.progress_bar)
		output_label=Gtk.Label("Output:")
		output_label.set_alignment(0,0)
		vbox.add(output_label)
		scrolled_window=Gtk.ScrolledWindow(expand=True)
		self.textview=Gtk.TextView()
		self.textview.set_editable(False)
		scrolled_window.add(self.textview)
		vbox.add(scrolled_window)
		box.add(vbox)
		self.connect("delete-event",self.handler_delete)

	def handler_delete(self,widget,event):
		self.hide()
		return True

	def progress_function(self,current_total,total,log):
		self.progress_bar.set_fraction(float(current_total)/float(total))
		self.progress_bar.set_text(str(current_total)+"/"+str(total))


		log_view=str()		
		for key in sorted(log.keys()):
			log_view+=key+"\n=====================\n"
			for url in log[key]:
				log_view+=url.strip()+"\n"
			log_view+="\n\n"

		self.textview.get_buffer().set_text(log_view)


class BruteForce(Thread):

	iter=None

	def __init__(self,config,base_url,wordlist,recursive,add_function,progress_function,finished_function):
	        Thread.__init__(self)
		self.config=config
		self.recursive=recursive
		self.wordlist_length=0
		self.wordlist=[]
		self.total=0
		self.current_total=0
		self.finished=False


		self.base_queue=Queue.Queue(0)
		self.base_queue.put(base_url)

		self.add_function=add_function
		self.progress_function=progress_function
		self.finished_function=finished_function

		self.log={}
		self.view=DialogBruteForceView()

		f=open(wordlist,"r")
		for word in f:
			word=word.strip()
			if len(word) > 0:
				if word[0] != "#":
					if word[-1:] != "/":
						word+="/"		
					self.wordlist_length+=1
					self.wordlist.append(word)
		f.close()


	def run(self):
		self.total+=self.wordlist_length
		work_queue=Queue.Queue(0)
		while not self.finished:
			try:
				base_url=self.base_queue.get_nowait()
				for word in self.wordlist:
					work_queue.put(base_url+word)
				
				self.worker=http_client.HTTPMultiClient(self.config,self.response_callback,self.finished_callback)
				self.worker.run("HEAD",work_queue)


			except Queue.Empty:
				self.finished=True
		GObject.idle_add(self.finished_function,self.iter)
		GObject.idle_add(self.view.progress_function,self.current_total,self.total,self.log)


	def response_callback(self,flow):
		url=flow.request.get_url()

		if flow.response.code != 404:
			if str(flow.response.code) in self.log.keys():
				self.log[str(flow.response.code)].append(url)
			else:
				self.log[str(flow.response.code)]=[url]

		if flow.response.code == 200:
			if self.recursive:
				self.total+=self.wordlist_length
				self.base_queue.put(url)
			GObject.idle_add(self.add_function,url)
		self.current_total+=1
		if divmod(self.current_total,100)[1] == 0:
			GObject.idle_add(self.progress_function,self.iter,self.current_total,self.total)
			GObject.idle_add(self.view.progress_function,self.current_total,self.total,self.log)

	def finished_callback(self):
		print self.log
	

	def stop(self):
		self.worker.stop()
		self.finished=True


