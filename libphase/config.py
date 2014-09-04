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

from libphase import utilities
from libphase import dialogs
from libmproxy import proxy

from netlib import certutils

from gi.repository import Gtk

import os
import sys
import OpenSSL

import ConfigParser

class ConfigSection():
		pass


class Config():


	def generate_libmproxy_config(self):

		def unlock_client_certs(cert_file):
			clientcerts=None
			finished=False
			password=None
			while not finished:
				try:
					if password:
						clientcerts = certutils.KeyPair.from_file(cert_file,password)
						finished=True
					else:
						clientcerts = certutils.KeyPair.from_file(cert_file)
						finished=True
				except OpenSSL.crypto.Error:
					response,password=dialogs.password_question("PKCS #12 Password","Please enter the password to unlock the PKCS #12 file:\n\n<b>"+cert_file+"</b>")
					if response == Gtk.ResponseType.OK:
						continue
					else:
						dialogs.warning("Unable to open PKCS #12","Phase was unable to open the PKCS #12 file. Continuing without client certificates.")
						finished=True
			return clientcerts

		if self.proxy.ssl.ca_cert:
			try:
				certstore = certutils.CertStore.from_file(self.directory+os.sep+"ca"+os.sep+self.proxy.ssl.ca_cert+".p12")
			except IOError:
				dialogs.warning("Unable to load CA certificate", "Phase was unable to open the certificate authority file:\n\n<b>"+self.directory+os.sep+"ca"+os.sep+self.proxy.ssl.ca_cert+".p12"+"</b>\n\nSSL support has been disabled. Select a valid CA certificate from <i>Settings</i> to re-enable.")
				certstore=None
		else:
			dialogs.warning("SSL Support Disabled", "A Certificate Authority (CA) certificate has not been generated or selected. SSL support is currently disabled.\n\nUse <i>Settings</i> to generate a new CA certificate.")			
			certstore=None

		if self.proxy.mode == "REVERSE":
			rp=(self.proxy.reverse_protocol,self.proxy.reverse_host,self.proxy.reverse_port)
		else:
			rp=None
		
		if self.proxy.ssl.client_cert_enabled:
			try:
				clientcerts=unlock_client_certs(self.directory+os.sep+"client"+os.sep+self.proxy.ssl.client_cert+".p12")
			except IOError:
				dialogs.warning("Unable to load client certificate", "Phase was unable to open the client certificate file:\n\n<b>"+self.directory+os.sep+"ca"+os.sep+self.proxy.ssl.client_cert+".p12"+"</b>\n\nThe SSL client certificate function has been disabled. Select a valid client certificate from <i>Settings</i> to re-enable.")
				clientcerts=None
		else:
			clientcerts=None

		self.libmproxy_config = proxy.ProxyConfig(clientcerts=clientcerts,certstore=certstore,disable_client_ssl=(not self.proxy.reverse_ssl),reverse_proxy=rp)
		return self.libmproxy_config
	
	def load_defaults(self):
		self.proxy.port=8080
		self.proxy.mode="FORWARD"
		self.proxy.reverse_protocol="http"
		self.proxy.reverse_host=""
		self.proxy.reverse_port=80
		self.proxy.reverse_ssl=False

		self.proxy.ssl.ca_cert=""
		self.proxy.ssl.client_cert=""
		self.proxy.ssl.client_cert_enabled=False

		self.authentication.type="None"
		self.authentication.basic_username=""
		self.authentication.basic_password=""
		self.authentication.digest=False
		self.authentication.ntlm_domain=""
		self.authentication.ntlm_username=""
		self.authentication.ntlm_password=""

		self.external_tools.sqlmap=""
		self.save()


	def __init__(self,directory):
		self.directory=directory
		self.filename=directory+os.sep+"phase.conf"

		self.proxy=ConfigSection()
		self.proxy.ssl=ConfigSection()
		self.authentication=ConfigSection()
		self.external_tools=ConfigSection()


	def load(self):

		if not os.path.exists(self.filename):
			self.load_defaults()


		self.proxy.ignored_extensions=utilities.RegexList(["png","PNG","jpg","JPG","jpeg","JPEG","gif","GIF",".js",".css",".ico"])

		try:
			config = ConfigParser.SafeConfigParser()
			config.read(self.filename)
			self.proxy.port=config.getint('proxy','port')

			if self.proxy.port > 65535 or self.proxy.port < 0:
				 self.proxy.port=8080

			self.proxy.mode=config.get('proxy','mode')
	
			if self.proxy.mode != "FORWARD" or self.proxy.mode != "REVERSE":
				self.proxy.mode = "FORWARD"

			self.proxy.reverse_protocol=config.get('proxy','reverse_protocol')

			if self.proxy.reverse_protocol != "http" or self.proxy.reverse_protocol != "https":
				self.proxy.reverse_protocol="http"

			self.proxy.reverse_host=config.get('proxy','reverse_host')
			self.proxy.reverse_port=config.getint('proxy','reverse_port')

			if self.proxy.reverse_port > 65535 or self.proxy.reverse_port < 0:
				self.proxy.reverse_port=80

			self.proxy.reverse_ssl=config.getboolean('proxy','reverse_ssl')

			self.proxy.ssl.ca_cert=config.get('proxy.ssl','ca_cert')
			self.proxy.ssl.client_cert=config.get('proxy.ssl','client_cert')
			self.proxy.ssl.client_cert_enabled=config.getboolean('proxy.ssl','client_cert_enabled')

			self.external_tools.sqlmap=config.get('external_tools','sqlmap')

			self.authentication.type=config.get("authentication","type")

			if self.authentication.type not in ["None","Basic","NTLM"]:
				self.authentication.type=="None"

			self.authentication.basic_username=config.get("authentication","basic_username")
			self.authentication.basic_password=config.get("authentication","basic_password")
			self.authentication.digest=config.get("authentication","digest")
			self.authentication.ntlm_domain=config.get("authentication","ntlm_domain")
			self.authentication.ntlm_username=config.get("authentication","ntlm_username")
			self.authentication.ntlm_password=config.get("authentication","ntlm_password")

		except (ValueError,ConfigParser.ParsingError) as e:
			dialogs.warning("Invalid Configuration", "An error has been detected in the Phase configuration file:\n\n<b>"+str(e)+"</b>\n\nPhase will now exit.")
			sys.exit()

	def save(self):
		config = ConfigParser.SafeConfigParser()
		
		#Proxy Settings
		config.add_section('proxy')
		config.set('proxy', 'port', str(self.proxy.port))
		config.set('proxy', 'mode', self.proxy.mode)
		config.set('proxy', 'reverse_protocol', self.proxy.reverse_protocol)
		config.set('proxy', 'reverse_host', self.proxy.reverse_host)
		config.set('proxy', 'reverse_port', str(self.proxy.reverse_port))
		config.set('proxy', 'reverse_ssl', str(self.proxy.reverse_ssl))
		
		#SSL Settings
		config.add_section('proxy.ssl')
		config.set('proxy.ssl', 'ca_cert', self.proxy.ssl.ca_cert)
		config.set('proxy.ssl', 'client_cert', self.proxy.ssl.client_cert)
		config.set('proxy.ssl', 'client_cert_enabled', str(self.proxy.ssl.client_cert_enabled))

		config.add_section("authentication")
		config.set("authentication","type",self.authentication.type)
		config.set("authentication","basic_username",self.authentication.basic_username)
		config.set("authentication","basic_password",self.authentication.basic_password)
		config.set("authentication","digest",str(self.authentication.digest))
		config.set("authentication","ntlm_domain",self.authentication.ntlm_domain)
		config.set("authentication","ntlm_username",self.authentication.ntlm_username)
		config.set("authentication","ntlm_password",self.authentication.ntlm_password)
	

		#External Tool Settings
		config.add_section('external_tools')
		config.set('external_tools', 'sqlmap', self.external_tools.sqlmap)
	
		with open(self.filename, 'wb') as configfile:
			config.write(configfile)
		

