from libphase import http_client
from threading import Thread
import Queue
from urlparse import urlparse,urljoin
from bs4 import BeautifulSoup
from gi.repository import GObject


class UniqueQueue(Queue.Queue):

	history_set=set()

	def put_unique(self,item,no_wait=False):
		if item in self.history_set:
			return
		else:
			self.history_set.add(item)
			if no_wait:
				self.put_nowait(item)
			else:
				self.put(item)


class Spider(Thread):

	def __init__(self,config, url, add_function,progress_function,finished_function):
		Thread.__init__(self)
		self.config=config
		self.url=urlparse(url)
		self.visited_urls=[url]
		self.allowed_domain=self.url.netloc
		self.work_queue=Queue.Queue(0)
		self.work_queue.put(url)
		self.finished=False		

		self.add_function=add_function
		self.progress_function=progress_function
		self.finished_function=finished_function


	def run(self):
		
		while not self.finished:
			if self.work_queue.qsize() > 0:
				self.worker=http_client.HTTPMultiClient(self.config,self.response_callback,self.finished_callback)
				self.worker.run("GET",self.work_queue)
			else:
				self.finished=True
		GObject.idle_add(self.finished_function,self.iter)


	def response_callback(self,flow):
		print "GET:",flow.request.get_url()
		soup=BeautifulSoup(flow.response.content)
		
		for a in soup.find_all('a', href=True):
			if a["href"] != "#" or a["href"][0:6]!="mailto:":		
				parsed_url=urlparse(a["href"])			
				if parsed_url.hostname:
					#absolute URL
					if parsed_url.netloc == self.allowed_domain and not self.config.proxy.ignored_extensions.match(url):
						url=parsed_url.geturl()					
						if url not in self.visited_urls:
							#print "FOUND:",a["href"]
							self.visited_urls.append(url)
							self.work_queue.put(url)
						else:
							pass#print "ALREADY FOUND:",a["href"]
					else:
						print "IGNORING:",a["href"]
				else:
					#relative URL
					url=urljoin(self.url.geturl(),a["href"])
					if not self.config.proxy.ignored_extensions.match(url):						
						if url not in self.visited_urls:
							#print "FOUND REL:",a["href"],url
							self.visited_urls.append(url)
							self.work_queue.put(url)
						else:
							pass#print "ALREADY FOUND REL:",a["href"],url
					else:
						print "IGNORING:",a["href"]
	def finished_callback(self):
		pass
