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

class Window():
	def __init__(self,shared_objects,name):
		self.config=shared_objects.config		
		self.builder=shared_objects.builder
		self.window=self.builder.get_object(name)
		self.window.connect("delete-event",self.handler_window_delete)


	def handler_window_delete(self,widget,event):
		self.window.hide()
		return True

	def show(self):
		self.window.show_all()
