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
from plugins.vulnerabilities import base
from bs4 import BeautifulSoup
import urlparse

class CrossDomainJavaScript(base.Vulnerability):
	
	title="Cross Domain JavaScript File Inclusion"	
	risk=base.LOW
	description="The affected page includes a JavaScript file from a different domain. If the server hosting this file were to be compromised, an attacker would be able to carry out Cross-Site Scripting attacks by modifying the file to include malicious code." 
	recommendation="The affected file should be copied to the web server for this domain."

class Plugin(base.PluginBase):

	def process(self,flow):
		vulnerabilities=[]
		requested_host=urlparse.urlparse(flow.request.get_url()).netloc.split(":")[0]
		soup=BeautifulSoup(flow.response.content)
	
		included_scripts=set()

		for script_tag in soup.findAll('script'):
			if "src" in script_tag.attrs.keys():
				included_scripts.add(script_tag["src"])

		for script in included_scripts:
			script_host=urlparse.urlparse(script).netloc.split(":")[0]
			if script_host != requested_host:
				vulnerabilities.append(CrossDomainJavaScript(flow.request.get_url(),script))
		return vulnerabilities
