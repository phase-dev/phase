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

from libphase.windows import window
from libphase import gtk

from gi.repository import GtkSource
from gi.repository import Gtk

from libmproxy.protocol.http import HTTPFlow,HTTPRequest,HTTPResponse
from libmproxy.proxy import ServerConnection

import urllib2
import OpenSSL
import time
import os
import glob
import shutil

COUNTRY_CODES=["GB","US","AD","AE","AF","AG","AI","AL","AM","AN","AO","AQ","AR","AS","AT","AU","AW","AX","AZ","BA","BB","BD","BE","BF","BG","BH","BI","BJ","BM","BN","BO","BR","BS","BT","BV","BW","BZ","CA","CC","CF","CH","CI","CK","CL","CM","CN","CO","CR","CS","CV","CX","CY","CZ","DE","DJ","DK","DM","DO","DZ","EC","EE","EG","EH","ER","ES","ET","FI","FJ","FK","FM","FO","FR","FX","GA","GD","GE","GF","GG","GH","GI","GL","GM","GN","GP","GQ","GR","GS","GT","GU","GW","GY","HK","HM","HN","HR","HT","HU","ID","IE","IL","IM","IN","IO","IS","IT","JE","JM","JO","JP","KE","KG","KH","KI","KM","KN","KR","KW","KY","KZ","LA","LC","LI","LK","LS","LT","LU","LV","LY","MA","MC","MD","ME","MG","MH","MK","ML","MM","MN","MO","MP","MQ","MR","MS","MT","MU","MV","MW","MX","MY","MZ","NA","NC","NE","NF","NG","NI","NL","NO","NP","NR","NT","NU","NZ","OM","PA","PE","PF","PG","PH","PK","PL","PM","PN","PR","PS","PT","PW","PY","QA","RE","RO","RS","RU","RW","SA","SB","SC","SE","SG","SH","SI","SJ","SK","SL","SM","SN","SR","ST","SU","SV","SZ","TC","TD","TF","TG","TH","TJ","TK","TM","TN","TO","TP","TR","TT","TV","TW","TZ","UA","UG","UM","UY","UZ","VA","VC","VE","VG","VI","VN","VU","WF","WS","YE","YT","ZA","ZM"]

class DialogSSL(Gtk.Dialog):

	def __init__(self, parent):
		Gtk.Dialog.__init__(self, "Generate A New SSL Certificate", parent, 0, ())

		self.add_button("Cancel",Gtk.ResponseType.CANCEL)
		self.generate_button=self.add_button("Generate",Gtk.ResponseType.OK)

		self.generate_button.set_sensitive(False)

		sn_label = Gtk.Label("<b>Subject Name</b>")
		sn_label.set_use_markup(True)
		key_label = Gtk.Label("<b>Key Size</b>")
		key_label.set_use_markup(True)
		self.key_dropdown = Gtk.ComboBox()
		key_store=Gtk.ListStore(str,int)
		key_store.append(["1024",1024])
		key_store.append(["2048",2048])
		key_store.append(["3072",3072])
		key_store.append(["4096",4096])
		self.key_dropdown.set_model(key_store)
		key_cell=Gtk.CellRendererText()
		self.key_dropdown.pack_start(key_cell,True)
		self.key_dropdown.add_attribute(key_cell,'text',0)
		self.key_dropdown.set_active(0)

		cn_label = Gtk.Label("Common Name (CN):")
		self.cn_entry = Gtk.Entry()
		ou_label = Gtk.Label("Organisational Unit (OU)")
		self.ou_entry = Gtk.Entry()
		o_label = Gtk.Label("Organisation (O):")
		self.o_entry = Gtk.Entry()
		st_label = Gtk.Label("State or Province (ST):")
		self.st_entry = Gtk.Entry()
		l_label = Gtk.Label("Locality (L):")
		self.l_entry = Gtk.Entry()
		c_label = Gtk.Label("Country (C):")
		self.c_dropdown = Gtk.ComboBox()
		c_store=Gtk.ListStore(str)

		for country in COUNTRY_CODES:
			c_store.append([country])
		
		self.c_dropdown.set_model(c_store)		
		c_cell=Gtk.CellRendererText()
		self.c_dropdown.pack_start(c_cell,True)
		self.c_dropdown.add_attribute(c_cell,'text',0)
		self.c_dropdown.set_active(0)

		box = self.get_content_area()

		grid=Gtk.Grid()

		grid.attach(cn_label,0,0,1,1)
		grid.attach(self.cn_entry,1,0,1,1)
		grid.attach(ou_label,0,1,1,1)
		grid.attach(self.ou_entry,1,1,1,1)
		grid.attach(o_label,0,2,1,1)
		grid.attach(self.o_entry,1,2,1,1)
		grid.attach(st_label,0,3,1,1)
		grid.attach(self.st_entry,1,3,1,1)
		grid.attach(l_label,0,4,1,1)
		grid.attach(self.l_entry,1,4,1,1)
		grid.attach(c_label,0,5,1,1)
		grid.attach(self.c_dropdown,1,5,1,1)
		grid.set_column_homogeneous(True)

		alignment=Gtk.Alignment()
		alignment.set_padding(15,15,0,0)
		alignment.add(grid)

		cal_grid=Gtk.Grid()

		label_from=Gtk.Label("Valid From")
		label_to=Gtk.Label("Valid To")
		self.from_cal=Gtk.Calendar()
		self.to_cal=Gtk.Calendar()
		
		cal_grid.attach(label_from,0,0,1,1)
		cal_grid.attach(label_to,1,0,1,1)
		cal_grid.attach(self.from_cal,0,1,1,1)
		cal_grid.attach(self.to_cal,1,1,1,1)

		box.add(sn_label)
		box.add(alignment)
		#box.add(cal_grid)
		box.add(key_label)
		box.add(self.key_dropdown)

		self.cn_entry.connect("changed",self.handler_entry_changed)
		self.ou_entry.connect("changed",self.handler_entry_changed)		
		self.o_entry.connect("changed",self.handler_entry_changed)
		self.st_entry.connect("changed",self.handler_entry_changed)
		self.l_entry.connect("changed",self.handler_entry_changed)

		self.show_all()

	def handler_entry_changed(self,entry):
		if len(self.cn_entry.get_text()) > 0 and len(self.ou_entry.get_text()) > 0 and len(self.o_entry.get_text()) > 0 and len(self.st_entry.get_text()) > 0 and len(self.l_entry.get_text()) > 0:
			self.generate_button.set_sensitive(True)
	

class Settings(window.Window):
	
	def __init__(self,shared_objects,name):
		window.Window.__init__(self,shared_objects,name)
		self.restart_proxy=shared_objects.restart_proxy
		self.builder.get_object("toolbuttonSettings").connect("clicked",self.handler_toolbutton_settings_clicked)
		self.builder.get_object("toolbuttonSettingsSSLAdd").connect("clicked",self.handler_toolbutton_settings_ssl_add_clicked)
		self.builder.get_object("toolbuttonSettingsSSLRemove").connect("clicked",self.handler_toolbutton_settings_ssl_remove_clicked)


		self.treeview_ca_store=Gtk.ListStore(str,bool)
		treeview_ca_cell_1 = Gtk.CellRendererText()
		treeview_ca_column_1 = Gtk.TreeViewColumn("Common Name", treeview_ca_cell_1, text=0)
		treeview_ca_cell_2 = Gtk.CellRendererToggle()
		treeview_ca_cell_2.set_radio(True)
		treeview_ca_column_2 = Gtk.TreeViewColumn("Active", treeview_ca_cell_2, active=1)
		treeview_ca_cell_2.connect("toggled",self.handler_toggle,self.treeview_ca_store)

		self.builder.get_object("treeviewSettingsSSLCAs").append_column(treeview_ca_column_1)
		self.builder.get_object("treeviewSettingsSSLCAs").append_column(treeview_ca_column_2)

		

		self.builder.get_object("treeviewSettingsSSLCAs").set_model(self.treeview_ca_store)

		self.builder.get_object("buttonSettingsOK").connect("clicked",self.handler_button_ok_clicked)
		self.builder.get_object("buttonSettingsCancel").connect("clicked",self.handler_button_cancel_clicked)
		
		self.builder.get_object("radiobuttonSettingsProxyReverse").connect("toggled",self.handler_proxy_radio_toggled)

		self.builder.get_object("radiobuttonSettingsAuthenticationNone").connect("toggled",self.handler_radio_authentication_toggled)
		self.builder.get_object("radiobuttonSettingsAuthenticationBasic").connect("toggled",self.handler_radio_authentication_toggled)
		self.builder.get_object("radiobuttonSettingsAuthenticationNTLM").connect("toggled",self.handler_radio_authentication_toggled)


		protocol_dropdown=self.builder.get_object("comboboxSettingsProxyReverseProtocol")
		self.protocol_store=Gtk.ListStore(str)
		self.protocol_store.append(["http"])
		self.protocol_store.append(["https"])
		protocol_dropdown.set_model(self.protocol_store)
		protocol_cell=Gtk.CellRendererText()
		protocol_dropdown.pack_start(protocol_cell,True)
		protocol_dropdown.add_attribute(protocol_cell,'text',0)
		protocol_dropdown.set_active(0)

		self.treeview_clientcert_store=Gtk.ListStore(str,bool)
		treeview_clientcert_cell_1 = Gtk.CellRendererText()
		treeview_clientcert_column_1 = Gtk.TreeViewColumn("Name", treeview_clientcert_cell_1, text=0)
		treeview_clientcert_cell_2 = Gtk.CellRendererToggle()
		treeview_clientcert_cell_2.set_radio(True)
		treeview_clientcert_column_2 = Gtk.TreeViewColumn("Active", treeview_clientcert_cell_2, active=1)
		treeview_clientcert_cell_2.connect("toggled",self.handler_toggle,self.treeview_clientcert_store)

		self.builder.get_object("treeviewSettingsSSLClientCerts").append_column(treeview_clientcert_column_1)
		self.builder.get_object("treeviewSettingsSSLClientCerts").append_column(treeview_clientcert_column_2)

		
		self.builder.get_object("treeviewSettingsSSLClientCerts").set_model(self.treeview_clientcert_store)

		self.builder.get_object("checkbuttonSettingsSSLClientCerts").connect("toggled",self.handler_checkbutton_clientcerts_toggled)
		self.builder.get_object("toolbuttonSettingsSSLClientCertsAdd").connect("clicked",self.handler_toolbutton_settings_ssl_clientcerts_add_clicked)
		self.builder.get_object("toolbuttonSettingsSSLClientCertsRemove").connect("clicked",self.handler_toolbutton_settings_ssl_clientcerts_remove_clicked)
	
	def handler_button_cancel_clicked(self,button):
		self.window.hide()

	def handler_button_ok_clicked(self,button):
		
		for row in self.treeview_ca_store:
			if row[1]:
				self.config.proxy.ssl.ca_cert=row[0]
		
		# Proxy Settings
		if self.builder.get_object("radiobuttonSettingsProxyForward").get_active():
			self.config.proxy.mode="FORWARD"
		else:
			self.config.proxy.mode="REVERSE"

		self.config.proxy.port=int(self.builder.get_object("spinbuttonSettingsProxyPort").get_value())
		if self.builder.get_object("comboboxSettingsProxyReverseProtocol").get_active() == 1:
			self.config.proxy.reverse_protocol = "https"
		else:
			self.config.proxy.reverse_protocol = "http"
		
		self.config.proxy.reverse_host=self.builder.get_object("entrySettingsProxyReverseHost").get_text()
		self.config.proxy.reverse_port=int(self.builder.get_object("spinbuttonSettingsProxyReversePort").get_value())
		self.config.proxy.reverse_ssl=self.builder.get_object("comboboxSettingsProxyReverseSSLListen").get_active()	


		self.config.proxy.ssl.client_cert_enabled=self.builder.get_object("checkbuttonSettingsSSLClientCerts").get_active()

		for row in self.treeview_clientcert_store:
			if row[1]:
				self.config.proxy.ssl.client_cert=row[0]


		if self.builder.get_object("radiobuttonSettingsAuthenticationNone").get_active():
			self.config.authentication.type="None"
		elif self.builder.get_object("radiobuttonSettingsAuthenticationBasic").get_active():
			self.config.authentication.type="Basic"
		elif self.builder.get_object("radiobuttonSettingsAuthenticationNTLM").get_active():
			self.config.authentication.type="NTLM"


		self.config.authentication.basic_username=self.builder.get_object("entrySettingsAuthenticationBasicUsername").get_text()
		self.config.authentication.basic_password=self.builder.get_object("entrySettingsAuthenticationBasicPassword").get_text()
		self.config.authentication.digest=self.builder.get_object("checkbuttonSettingsAuthenticationDigest").get_active()
		self.config.authentication.ntlm_domain=self.builder.get_object("entrySettingsAuthenticationNTLMDomain").get_text()
		self.config.authentication.ntlm_username=self.builder.get_object("entrySettingsAuthenticationNTLMUsername").get_text()
		self.config.authentication.ntlm_password=self.builder.get_object("entrySettingsAuthenticationNTLMPassword").get_text()

		self.restart_proxy()
		self.config.save()
		self.window.hide()

	def handler_toolbutton_settings_clicked(self,button):
		self.populate_certificate_authorities()
		self.populate_client_certificates()


		#Proxy Settings
		self.builder.get_object("spinbuttonSettingsProxyPort").set_value(self.config.proxy.port)

		if self.config.proxy.mode=="REVERSE":
			self.builder.get_object("radiobuttonSettingsProxyReverse").set_active(True)
		else:
			self.builder.get_object("radiobuttonSettingsProxyForward").set_active(True)

		
		if self.config.proxy.reverse_protocol == "https":
			self.builder.get_object("comboboxSettingsProxyReverseProtocol").set_active(1)
		else:
			self.builder.get_object("comboboxSettingsProxyReverseProtocol").set_active(0)
	
		self.builder.get_object("entrySettingsProxyReverseHost").set_text(self.config.proxy.reverse_host)
		self.builder.get_object("spinbuttonSettingsProxyReversePort").set_value(self.config.proxy.reverse_port)
		self.builder.get_object("comboboxSettingsProxyReverseSSLListen").set_active(self.config.proxy.reverse_ssl)
		
		self.builder.get_object("checkbuttonSettingsSSLClientCerts").set_active(self.config.proxy.ssl.client_cert_enabled)
		self.handler_checkbutton_clientcerts_toggled(self.builder.get_object("checkbuttonSettingsSSLClientCerts"))

		if self.config.authentication.type == "None":
			self.builder.get_object("radiobuttonSettingsAuthenticationNone").set_active(True)
		elif self.config.authentication.type == "Basic":
			self.builder.get_object("radiobuttonSettingsAuthenticationBasic").set_active(True)
		elif self.config.authentication.type == "NTLM":
			self.builder.get_object("radiobuttonSettingsAuthenticationNTLM").set_active(True)

		self.builder.get_object("entrySettingsAuthenticationBasicUsername").set_text(self.config.authentication.basic_username)
		self.builder.get_object("entrySettingsAuthenticationBasicPassword").set_text(self.config.authentication.basic_password)
		self.builder.get_object("checkbuttonSettingsAuthenticationDigest").set_active(self.config.authentication.digest)
		self.builder.get_object("entrySettingsAuthenticationNTLMDomain").set_text(self.config.authentication.ntlm_domain)
		self.builder.get_object("entrySettingsAuthenticationNTLMUsername").set_text(self.config.authentication.ntlm_username)
		self.builder.get_object("entrySettingsAuthenticationNTLMPassword").set_text(self.config.authentication.ntlm_password)

		self.window.show_all()


	def handler_radio_authentication_toggled(self,radio):
		if self.builder.get_object("radiobuttonSettingsAuthenticationNone").get_active():
			self.builder.get_object("entrySettingsAuthenticationBasicUsername").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationBasicPassword").set_sensitive(False)
			self.builder.get_object("checkbuttonSettingsAuthenticationDigest").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationNTLMDomain").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationNTLMUsername").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationNTLMPassword").set_sensitive(False)


		if self.builder.get_object("radiobuttonSettingsAuthenticationBasic").get_active():
			self.builder.get_object("entrySettingsAuthenticationBasicUsername").set_sensitive(True)
			self.builder.get_object("entrySettingsAuthenticationBasicPassword").set_sensitive(True)
			self.builder.get_object("checkbuttonSettingsAuthenticationDigest").set_sensitive(True)
			self.builder.get_object("entrySettingsAuthenticationNTLMDomain").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationNTLMUsername").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationNTLMPassword").set_sensitive(False)


		if self.builder.get_object("radiobuttonSettingsAuthenticationNTLM").get_active():
			self.builder.get_object("entrySettingsAuthenticationBasicUsername").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationBasicPassword").set_sensitive(False)
			self.builder.get_object("checkbuttonSettingsAuthenticationDigest").set_sensitive(False)
			self.builder.get_object("entrySettingsAuthenticationNTLMDomain").set_sensitive(True)
			self.builder.get_object("entrySettingsAuthenticationNTLMUsername").set_sensitive(True)
			self.builder.get_object("entrySettingsAuthenticationNTLMPassword").set_sensitive(True)



	def handler_checkbutton_clientcerts_toggled(self,checkbutton):
		if checkbutton.get_active():
			self.builder.get_object("treeviewSettingsSSLClientCerts").set_sensitive(True)
			self.builder.get_object("toolbuttonSettingsSSLClientCertsAdd").set_sensitive(True)
			self.builder.get_object("toolbuttonSettingsSSLClientCertsRemove").set_sensitive(True)
		else:
			self.builder.get_object("treeviewSettingsSSLClientCerts").set_sensitive(False)
			self.builder.get_object("toolbuttonSettingsSSLClientCertsAdd").set_sensitive(False)
			self.builder.get_object("toolbuttonSettingsSSLClientCertsRemove").set_sensitive(False)


	def handler_proxy_radio_toggled(self,radio):
		if self.builder.get_object("radiobuttonSettingsProxyForward").get_active():
			self.builder.get_object("comboboxSettingsProxyReverseProtocol").set_sensitive(False)
			self.builder.get_object("entrySettingsProxyReverseHost").set_sensitive(False)
			self.builder.get_object("spinbuttonSettingsProxyReversePort").set_sensitive(False)
			self.builder.get_object("comboboxSettingsProxyReverseSSLListen").set_sensitive(False)
		else:
			self.builder.get_object("comboboxSettingsProxyReverseProtocol").set_sensitive(True)
			self.builder.get_object("entrySettingsProxyReverseHost").set_sensitive(True)
			self.builder.get_object("spinbuttonSettingsProxyReversePort").set_sensitive(True)
			self.builder.get_object("comboboxSettingsProxyReverseSSLListen").set_sensitive(True)


	def populate_certificate_authorities(self):
		self.treeview_ca_store.clear()
		cas=glob.glob(self.config.directory+os.sep+"ca"+os.sep+"*.p12")		
		for ca in cas:
			cn=ca.replace(self.config.directory+os.sep+"ca"+os.sep,"").replace(".p12","")

			if cn == self.config.proxy.ssl.ca_cert:
				self.treeview_ca_store.append([cn,True])
			else:
				self.treeview_ca_store.append([cn,False])

	def populate_client_certificates(self):
		self.treeview_clientcert_store.clear()
		cas=glob.glob(self.config.directory+os.sep+"client"+os.sep+"*.p12")		
		for ca in cas:
			cn=ca.replace(self.config.directory+os.sep+"client"+os.sep,"").replace(".p12","")

			if cn == self.config.proxy.ssl.client_cert:
				self.treeview_clientcert_store.append([cn,True])
			else:
				self.treeview_clientcert_store.append([cn,False])


        def handler_toggle(self,cellrenderer,path,store):
                store.set_value(store.get_iter(path), 1, not cellrenderer.get_active())
                for row in store:
                        if int(row.path[0]) == int(path):
                                row[1]=True
                        else:
                                row[1]=False   


	def handler_toolbutton_settings_ssl_remove_clicked(self,button):
		model,iter=self.builder.get_object("treeviewSettingsSSLCAs").get_selection().get_selected()
		if iter:
			ca=self.builder.get_object("treeviewSettingsSSLCAs").get_model().get_value(iter,0)
			self.builder.get_object("treeviewSettingsSSLCAs").get_model().remove(iter)
			os.remove(self.config.directory+os.sep+"ca"+os.sep+ca+".p12")
			os.remove(self.config.directory+os.sep+"ca"+os.sep+ca+".pem")


	def handler_toolbutton_settings_ssl_clientcerts_remove_clicked(self,button):
		model,iter=self.builder.get_object("treeviewSettingsSSLClientCerts").get_selection().get_selected()
		if iter:
			ca=self.builder.get_object("treeviewSettingsSSLClientCerts").get_model().get_value(iter,0)
			self.builder.get_object("treeviewSettingsSSLClientCerts").get_model().remove(iter)
			os.remove(self.config.directory+os.sep+"client"+os.sep+ca+".p12")

	def handler_toolbutton_settings_ssl_clientcerts_add_clicked(self,button):
		dialog = Gtk.FileChooserDialog(title="Import Client Certificate and Key",action=Gtk.FileChooserAction.OPEN,buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		phase_filter = Gtk.FileFilter()
		phase_filter.add_pattern("*.p12")
		phase_filter.add_pattern("*.pfx")
		phase_filter.set_name("PKCS #12 File")
		dialog.add_filter(phase_filter)
		response=dialog.run()
 
		if response == Gtk.ResponseType.OK:
			source_filename=dialog.get_filename()
			dest_filename=os.path.basename(dialog.get_filename().replace(".pfx",".p12"))
			shutil.copyfile(source_filename, self.config.directory+os.sep+"client"+os.sep+dest_filename)
		dialog.destroy()
		self.populate_client_certificates()


	def handler_toolbutton_settings_ssl_add_clicked(self,button):
		dialog=DialogSSL(self.window)
		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:

			key = OpenSSL.crypto.PKey()
			key_length=(dialog.key_dropdown.get_active()*1024)+1024
			key.generate_key(OpenSSL.crypto.TYPE_RSA, key_length)
			cert = OpenSSL.crypto.X509()
			cert.set_serial_number(int(time.time()*10000))
			cert.set_version(2)
			cert.get_subject().CN = dialog.cn_entry.get_text()
			cert.get_subject().OU = dialog.ou_entry.get_text()
			cert.get_subject().O = dialog.o_entry.get_text()
			cert.get_subject().ST = dialog.st_entry.get_text()
			cert.get_subject().L = dialog.l_entry.get_text()		
			cert.get_subject().C = COUNTRY_CODES[dialog.c_dropdown.get_active()]
			cert.gmtime_adj_notBefore(0)
			cert.gmtime_adj_notAfter(62208000)
			cert.set_issuer(cert.get_subject())
			cert.set_pubkey(key)

			cert.add_extensions([
				OpenSSL.crypto.X509Extension("basicConstraints", True, "CA:TRUE"),
				OpenSSL.crypto.X509Extension("nsCertType", True, "sslCA"),
				OpenSSL.crypto.X509Extension("extendedKeyUsage", True, "serverAuth,clientAuth,emailProtection,timeStamping,msCodeInd,msCodeCom,msCTLSign,msSGC,msEFS,nsSGC"),
				OpenSSL.crypto.X509Extension("keyUsage", False, "keyCertSign, cRLSign"),
				OpenSSL.crypto.X509Extension("subjectKeyIdentifier", False, "hash", subject=cert),
			])
			cert.sign(key, "sha1")

			f = open(self.config.directory+os.sep+"ca"+os.sep+dialog.cn_entry.get_text()+".p12", "wb")
			p12 = OpenSSL.crypto.PKCS12()
			p12.set_certificate(cert)
			p12.set_privatekey(key)
			f.write(p12.export())
			f.close()

			f = open(os.path.join(self.config.directory+os.sep+"ca"+os.sep+dialog.cn_entry.get_text()+".pem"), "wb")
			f.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
			f.close()

		dialog.destroy()
		self.populate_certificate_authorities()
