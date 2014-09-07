from libphase import http_client
from threading import Thread
import Queue
from urlparse import urlparse,urljoin
from bs4 import BeautifulSoup
from gi.repository import GObject
from gi.repository import Gtk


class DialogSpiderView(Gtk.Dialog):
	def __init__(self):
		Gtk.Dialog.__init__(self, "Spider Status", None, 0, ())
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
	
		self.textview.get_buffer().set_text(log)



class Spider(Thread):

	def __init__(self,config, url, add_function,progress_function,finished_function,threads=10):
		Thread.__init__(self)
		self.config=config
		self.url=urlparse(url)
		self.visited_urls=[url]
		self.visited_count=0
		self.allowed_domain=self.url.netloc
		self.work_queue=Queue.Queue(0)
		self.work_queue.put(url)
		self.finished=False		

		self.add_function=add_function
		self.progress_function=progress_function
		self.finished_function=finished_function
	
		self.view=DialogSpiderView()
		self.log=str()

		self.threads=threads


	def run(self):
		
		while not self.finished:
			if self.work_queue.qsize() > 0:
				self.worker=http_client.HTTPMultiClient(self.config,self.response_callback,self.finished_callback,threads=self.threads)
				self.worker.run("GET",self.work_queue)
			else:
				self.finished=True
		GObject.idle_add(self.finished_function,self.iter)


	def response_callback(self,flow):
		self.visited_count+=1
		GObject.idle_add(self.progress_function,self.iter,self.visited_count,self.visited_count+self.work_queue.qsize())
		GObject.idle_add(self.view.progress_function,self.visited_count,self.visited_count+self.work_queue.qsize(),self.log)
		self.log+="GET: "+flow.request.get_url()+" ("+str(flow.response.code)+")\n"
		soup=BeautifulSoup(flow.response.content)
		
		for a in soup.find_all('a', href=True):
			if a["href"] != "#" and a["href"].startswith("mailto:") == False:		
				parsed_url=urlparse(a["href"])			
				if parsed_url.hostname:
					#absolute URL
					if parsed_url.netloc == self.allowed_domain and not self.config.proxy.ignored_extensions.match(a["href"]):
						url=parsed_url.geturl()					
						if url not in self.visited_urls:
							self.log+="FOUND: "+a["href"]+"\n"
							self.visited_urls.append(url)
							self.work_queue.put(url)
							GObject.idle_add(self.add_function,url)
						else:
							self.log+="ALREADY FOUND: "+a["href"]+"\n"
					else:
						self.log+="IGNORING: "+a["href"]+"\n"
				else:
					#relative URL
					url=urljoin(flow.request.get_url(),a["href"])
					if not self.config.proxy.ignored_extensions.match(url):						
						if url not in self.visited_urls:
							self.log+="FOUND: "+url+"\n"
							self.visited_urls.append(url)
							self.work_queue.put(url)
							GObject.idle_add(self.add_function,url)
						else:
							self.log+="ALREADY FOUND: "+url+"\n"
					else:
						self.log+="IGNORING: "+a["href"]+"\n"
	def finished_callback(self):
		pass

	def stop(self):
		self.worker.stop()
