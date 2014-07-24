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
from libmproxy import protocol
from libmproxy.protocol.http import HTTPFlow,HTTPRequest,HTTPResponse
from libmproxy.proxy import ServerConnection
from libmproxy.version import NAMEVERSION
from netlib import http
import urllib
import urlparse
import re

class RegexList(list):

	def __init__(self,items=[]):
		super(RegexList, self).__init__(items)
		self._compile_regex()

	def __setitem__(self,key,item):
		return super(RegexList, self).__setitem__(key,item)
		self._compile_regex()

	def _compile_regex(self):
		self.pattern=str()		
		for item in self:
			self.pattern+=str(item)+"$|"
		self.pattern=self.pattern[:-1]
		self.regex=re.compile(self.pattern)

	def append(self,x):
		super(RegexList, self).append(x)
		self._compile_regex()

	def match(self,string):
		if self.regex.search(string):
			return True
		else:
			return False



class HTTPClient():

	def __init__(self,url,config):
				
		parsed_url=urlparse.urlparse(url)

		if ":" in parsed_url.netloc:
			self.address=(parsed_url.netloc.split(":")[0],int(parsed_url.netloc.split(":")[1]))
		else:
			self.address=(parsed_url.netloc,80)

		self.scheme=parsed_url.scheme
		self.connection = ServerConnection(self.address, None)
		self.connection.connect()
		if self.scheme == "https":
			self.connection.establish_ssl(config.libmproxy_config.clientcerts, None)


	def close(self):
		self.connection.close()

	def request(self,path,headers={},data=None,head=False):

			parsed_path=urlparse.urlparse(path)
			path=parsed_path.path

			if head:
				method="HEAD"
			elif data:
				method="POST"
			else:
				method="GET"


			request=method+" "+urllib.quote(path)+" HTTP/1.1\r\n"
			request+="Host: "+self.address[0]+"\r\n"

			headers["User-Agent"]=NAMEVERSION
			headers["Connection"]="keep-alive"

			for header in headers.keys():
				request+=header+": "+headers[header]+"\r\n"

			if data:
				request+="Content-Length: "+str(len(data))+"\r\n\r\n"
				request+=data
				request+="\r\n\r\n"
			
			try:
				flow=HTTPFlow(None,self.connection)
				flow.request=HTTPRequest.from_string(request)
				self.connection.send(flow.request._assemble())
				flow.response = HTTPResponse.from_stream(self.connection.rfile, flow.request.method)
			except http.HttpErrorConnClosed:
				self.connection.connect()
				if self.scheme == "https":
					self.connection.establish_ssl(config.libmproxy_config.clientcerts, None)
				flow=HTTPFlow(None,self.connection)
				flow.request=HTTPRequest.from_string(request)
				self.connection.send(flow.request._assemble())
				flow.response = HTTPResponse.from_stream(self.connection.rfile, flow.request.method)
				
			return flow
