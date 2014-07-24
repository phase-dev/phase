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


class XFrameOptionsNotSet(base.Vulnerability):
	
	title="X-Frame-Options Not Set"	
	risk=base.LOW
	description="The remote server has not set the X-Frame-Options header. This headers instructs browsers whether to permit embedding of the page within an <iframe> tag. Without this header it may be possible to carry out a 'Clickjacking' attack."
	recommendation="Reconfigure the server to send an X-Frame-Options header with value 'deny' or 'sameorigin'."

class XContentTypeOptionsNotSet(base.Vulnerability):
	
	title="X-Content-Type-Options Not Set"	
	risk=base.LOW
	description="The remote server has not set the X-Content-Type-Options header. This header controls the use of MIME type sniffing on certain web browsers. An attacker able to upload malicious content may be able to exploit potential vulnerabilities in the browser functions used to carry out MIME sniffing."
	recommendation="Reconfigure the server to send an X-Content-Type-Options header with value 'nosniff'."


class Plugin(base.PluginBase):

	def process(self,flow):
		vulnerabilities=[]
		if "X-Frame-Options" not in flow.response.headers:
			vulnerabilities.append(XFrameOptionsNotSet(flow.request.get_url(),flow.response.get_headers()))

		if "X-Content-Type-Options" not in flow.response.headers:
			vulnerabilities.append(XContentTypeOptionsNotSet(flow.request.get_url(),flow.response.get_headers()))

		return vulnerabilities

