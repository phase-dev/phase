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


class InvalidSSLCertificate(base.Vulnerability):
	
	title="Invalid SSL Certificate"	
	risk=base.MEDIUM
	description="The Subject or SubjectAlt fields in the Secure Sockets Layer (SSL) X.509 certificate presented to Phase by the remote server do not contain the hostname used to access the server.\n\nPhase has automatically created a valid certificate for this hostname to prevent browser certificate warnings."
	recommendation="Purchase a valid Secure Sockets Layer certificate for this hostname. Alternatively, the server should be accessed using a hostname contained within the Subject or SubjectAlt fields of the certificate."

class Plugin(base.PluginBase):

	def process(self,flow):
		vulnerabilities=[]
		if flow.server_conn.cert:
			if flow.server_conn.cert.cn != flow.server_conn.address.host:
				return_text="Valid Hostnames:\n\n"
				return_text+=flow.server_conn.cert.cn+"\n"
				for san in flow.server_conn.cert.altnames:
					return_text+=san+"\n"
				return_text+="\nAccessed Hostname:\n\n"+flow.server_conn.address.host

				vulnerabilities.append(InvalidSSLCertificate(flow.request.get_url(),return_text))
		return vulnerabilities
