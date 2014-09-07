from libmproxy import protocol
from libmproxy.protocol.http import HTTPFlow,HTTPRequest,HTTPResponse
from libmproxy.proxy import ServerConnection
from libmproxy.version import NAMEVERSION
from threading import Thread
import Queue
from netlib import http
import urllib
import urlparse
from ntlm import ntlm


class HTTPClient():

	connection=None
	address=None

	def __init__(self,config):
		self.config=config	

	def close(self):
		self.connection.close()
		self.address=None



	def ntlm_replay(self,flow):

		if not self.connection or self.address != flow.server_conn.address():
			if self.connection:
				self.close()

			self.address=flow.server_conn.address()
			self.connection=ServerConnection(self.address, None)
			self.connection.connect()
			if flow.server_conn.ssl_established:
				self.connection.establish_ssl(self.config.libmproxy_config.clientcerts, flow.server_conn.sni)


		flow_1=HTTPFlow(None,flow.server_conn)
		flow_1.request=HTTPRequest.from_string(flow.request.to_string())

		auth_1 = 'NTLM %s' % ntlm.create_NTLM_NEGOTIATE_MESSAGE("%s\\%s" % (self.config.authentication.ntlm_domain,self.config.authentication.ntlm_username))

		flow_1.request.headers["Authorization"]=[auth_1]
		flow_1.request.headers["Connection"]=["keep-alive"]

		self.connection.send(flow_1.request._assemble())
		flow_1.response = HTTPResponse.from_stream(self.connection.rfile, flow.request.method)

		ServerChallenge, NegotiateFlags = ntlm.parse_NTLM_CHALLENGE_MESSAGE(flow_1.response.headers["WWW-Authenticate"][0][5:])


		flow_2=HTTPFlow(None,flow.server_conn)
		flow_2.request=HTTPRequest.from_string(flow.request.to_string())
		auth_2 = 'NTLM %s' % ntlm.create_NTLM_AUTHENTICATE_MESSAGE(ServerChallenge, self.config.authentication.ntlm_username, self.config.authentication.ntlm_domain, self.config.authentication.ntlm_password, NegotiateFlags)

		flow_2.request.headers["Authorization"]=[auth_2]

		self.connection.send(flow_2.request._assemble())
		flow_2.response = HTTPResponse.from_stream(self.connection.rfile, flow.request.method)

		flow.response.httpversion=flow_2.response.httpversion
		flow.response.code=flow_2.response.code
		flow.response.msg=flow_2.response.msg
		flow.response.headers=flow_2.response.headers
		flow.response.content=flow_2.response.content


	def request_from_string(self,url,request,update_content_length=False):

		parsed_url=urlparse.urlparse(url)
		if ":" in parsed_url.netloc:
			address=(parsed_url.netloc.split(":")[0],int(parsed_url.netloc.split(":")[1]))
		else:
			address=(parsed_url.netloc,80)

		if not self.connection or address != self.address:

			if self.connection:
				self.close()

			self.address=address
			self.connection = ServerConnection(self.address, None)
			self.connection.connect()

			if parsed_url.scheme == "https":
				if self.config:
					self.connection.establish_ssl(self.config.libmproxy_config.clientcerts, None)
				else:
					self.connection.establish_ssl(None, None)

		try:
			flow=HTTPFlow(None,self.connection)
			flow.request=HTTPRequest.from_string(request,update_content_length=update_content_length)
			self.connection.send(flow.request._assemble())
			flow.response = HTTPResponse.from_stream(self.connection.rfile, flow.request.method)
		except http.HttpErrorConnClosed:
			self.connection.connect()
			if parsed_url.scheme == "https":
				self.connection.establish_ssl(config.libmproxy_config.clientcerts, None)
			flow=HTTPFlow(None,self.connection)
			flow.request=HTTPRequest.from_string(request)
			self.connection.send(flow.request._assemble())
			flow.response = HTTPResponse.from_stream(self.connection.rfile, flow.request.method)
		

		if self.config.authentication.type=="NTLM" and "WWW-Authenticate" in flow.response.headers:
			if "NTLM" in flow.response.headers["WWW-Authenticate"]:
				self.ntlm_replay(flow)


		if "Connection" in flow.request.headers:
			if "keep-alive" not in flow.request.headers["Connection"]:
				self.close()

		return flow


	def request(self,method,url,headers={},data=None,keepalive=False):

		parsed_url=urlparse.urlparse(url)

		if len(parsed_url.path) == 0:
			path="/"

		elif parsed_url.path[0] != "/":
			path="/"+parsed_url.path
		else:
			path=parsed_url.path

		request=method+" "+urllib.quote(path)+" HTTP/1.1\r\n"
		request+="Host: "+parsed_url.netloc.split(":")[0]+"\r\n"

		headers["User-Agent"]=NAMEVERSION

		if keepalive:
			headers["Connection"]="keep-alive"

		if self.config.authentication.type=="Basic":
			headers["Authorization"]="Basic "+base64.b64encode(self.config.authentication.basic_username+":"+self.config.authentication.basic_password)

		for header in headers.keys():
			request+=header+": "+headers[header]+"\r\n"

		if data:
			request+="Content-Length: "+str(len(data))+"\r\n\r\n"
			request+=data
			request+="\r\n\r\n"
		

		return self.request_from_string(url,request)

class WorkerThread(Thread):

	finished=False

	def __init__(self,config,method,url_list,headers,data,keepalive,response_callback):
		Thread.__init__(self)
		self.config=config
		self.method=method
		self.url_list=url_list
		self.headers=headers
		self.data=data
		self.keepalive=keepalive
		self.response_callback=response_callback
		self.client=HTTPClient(config)

	def run(self):
		
		while not self.finished:
		
			try:
				url=self.url_list.get_nowait()
				flow=self.client.request(self.method,url,headers=self.headers,data=self.data,keepalive=self.keepalive)
				self.response_callback(flow)
			except Queue.Empty:
					self.finished=True


	def stop(self):
		self.finished=True


class HTTPMultiClient(Thread):

	
	def __init__(self,config,response_callback=lambda flow:None, finished_callback=lambda:None,threads=10):
		Thread.__init__(self)
		self.config=config
		self.response_callback=response_callback
		self.finished_callback=finished_callback
		self.threads=threads

	
	def run(self,method,url_list,headers={},data=None,keepalive=True):

		self.thread_pool=[]

		if isinstance(url_list,Queue.Queue):
			self.url_list=url_list
		else:
			self.url_list=Queue.Queue()

			for url in url_list:
				self.url_list.put(url)
		
		for i in range(0,self.threads):
			self.thread_pool.append(WorkerThread(self.config,method,self.url_list,headers,data,keepalive,self.response_callback))

		for thread in self.thread_pool:
			thread.start()

		for thread in self.thread_pool:
			thread.join()

		self.finished_callback()
