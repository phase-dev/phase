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


class HTTPOnlyNotSet(base.Vulnerability):
	
	title="Secure Cookie Flag Not Set"	
	risk=base.MEDIUM
	description="A cookie has been sent by the application via HTTPS that does not have the 'secure' flag set. This flag instructs web browsers to not send the cookie via an unencrypted HTTP connection. If the affected application serves content via HTTP, browsing to this site using an unencrypted connection may allow an attacker to intercept the cookie and carry out a session hijacking attack."
	recommendation="Ensure that the Secure flag is set on all cookies carrying sensitive information, such as session cookies."

class SecureNotSet(base.Vulnerability):
	
	title="HTTPOnly Cookie Flag Not Set"	
	risk=base.MEDIUM
	description="A cookie has been sent by the application without the 'HttpOnly' flag set. This flag instructs web browsers to prevent access to the cookie via JavaScript. This prevents session hijacking via Cross-Site Scripting."
	recommendation="Ensure that the HTTPOnly flag is set on all cookies."


class Plugin(base.PluginBase):

	def process(self,flow):
		vulnerabilities=[]
		for header in flow.response.headers:
			if "Set-Cookie" in header:
				http_only=False
				secure=False

				for component in header[1].split(";"):
					if component.strip().lower() == "httponly":
						http_only=True
					if component.strip().lower() == "secure":
						secure=True

				if not http_only:
					vulnerabilities.append(HTTPOnlyNotSet(flow.request.get_url(),flow.response.get_headers()))

				if not secure and flow.request.get_scheme() == "https":
					vulnerabilities.append(SecureNotSet(flow.request.get_url(),flow.response.get_headers()))
		return vulnerabilities

