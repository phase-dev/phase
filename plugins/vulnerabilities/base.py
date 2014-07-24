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

CRITICAL=5
HIGH=4
MEDIUM=3
LOW=2
INFORMATION=1

class Vulnerability():
	
	title="Generic Vulnerability"
	risk=INFORMATION
	description="Generic Vulnerability Description"
	url=str()
	value=str()

	def __init__(self,url,value):
		self.url=url	
		self.value=value

class PluginBase():
	
	name="BASE PLUGIN"

	def process(self,flow):
		pass
