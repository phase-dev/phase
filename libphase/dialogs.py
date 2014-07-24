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

from gi.repository import Gtk

def warning(title,message):
	dialog= Gtk.MessageDialog(
		None,
		Gtk.DialogFlags.MODAL| Gtk.DialogFlags.DESTROY_WITH_PARENT,
		Gtk.MessageType.WARNING,
		Gtk.ButtonsType.NONE,
		None)

	dialog.set_default_response(Gtk.ResponseType.OK)
	dialog.add_button("OK",Gtk.ResponseType.OK)
	dialog.set_position(Gtk.WindowPosition.CENTER)
	dialog.set_title(title)
	dialog.set_markup(message)
	response=dialog.run()
	dialog.destroy()
	return response



def password_question(title,question):

	dialog= Gtk.MessageDialog(
		None,
		Gtk.DialogFlags.MODAL| Gtk.DialogFlags.DESTROY_WITH_PARENT,
		Gtk.MessageType.QUESTION,
		Gtk.ButtonsType.NONE,
		None)

	dialog.set_default_response(Gtk.ResponseType.OK)
	dialog.add_button("Cancel",Gtk.ResponseType.CANCEL)
	dialog.add_button("OK",Gtk.ResponseType.OK)
	dialog.set_position(Gtk.WindowPosition.CENTER)
	dialog.set_markup(question)
	dialog.set_title(title)
	
	entry=Gtk.Entry()
	entry.set_visibility(False)
	label=Gtk.Label("Password:")
	alignment=Gtk.Alignment()
	alignment.set_padding(0,0,75,0)
	box=Gtk.Box()
	box.add(label)
	box.add(entry)
	alignment.add(box)

	dialog.vbox.add(alignment)
	dialog.vbox.show_all()

	response=dialog.run()
	password=entry.get_text()
	dialog.destroy()
	return response,password

def disclaimer():
	dialog= Gtk.MessageDialog(
		None,
		Gtk.DialogFlags.MODAL| Gtk.DialogFlags.DESTROY_WITH_PARENT,
		Gtk.MessageType.WARNING,
		Gtk.ButtonsType.NONE,
		None)

	dialog.add_button("I Do Not Accept",Gtk.ResponseType.CANCEL)
	dialog.add_button("I Accept",Gtk.ResponseType.OK)
	dialog.set_position(Gtk.WindowPosition.CENTER)
	dialog.set_title("Disclaimer")
	dialog.set_markup("Phase is a penetration testing tool and therefore is to be used only against systems where the user has authorisation. Usage of Phase for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable laws. The developers assume no liability and are not responsible for any misuse or damage caused by this software")
	response=dialog.run()
	dialog.destroy()
	return response


def exit_warning():
	dialog= Gtk.MessageDialog(
		None,
		Gtk.DialogFlags.MODAL| Gtk.DialogFlags.DESTROY_WITH_PARENT,
		Gtk.MessageType.WARNING,
		Gtk.ButtonsType.NONE,
		None)

	dialog.set_default_response(Gtk.ResponseType.OK)
	dialog.add_button("Close Without Saving",0)
	dialog.add_button("Cancel",1)
	dialog.add_button("Save",2)

	dialog.set_position(Gtk.WindowPosition.CENTER)
	dialog.set_title("Save and Exit?")
	dialog.set_markup("<b>Save and Exit?</b>\n\nIf you don't save, all changes will be permanently lost.")
	response=dialog.run()
	dialog.destroy()
	return response
