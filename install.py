#!/usr/bin/env python

import sys
import os
import errno
from hashlib import sha1
from xml.dom import minidom

PROFILE = len(sys.argv) > 1 and sys.argv[1] or 'Default'

SMILEY_SOURCE_DIR  = os.path.join(os.path.dirname(__file__), 'smileys')
SMILEY_TARGET_DIR  = os.path.expanduser(os.path.join('~', '.purple', 'custom_smiley'))
SMILEY_CONFIG_FILE = os.path.expanduser(os.path.join('~', '.purple', 'smileys.xml'))

KILL_LIST = ('c25eb29f9ff3b26a0e3d0789b55028ba139c1ef1',)

class Installer(object):
	def __init__(self):
		try:
			with open(SMILEY_CONFIG_FILE, 'rb') as f:
				self.doc = minidom.parseString(f.read())
		except IOError, e:
			if e.errno != errno.ENOENT:
				raise
			self.doc = minidom.Document()

		try:
			smileys = self.doc.getElementsByTagName('smileys')[0]
		except IndexError:
			smileys = self.doc.createElement('smileys')
			smileys.setAttribute('version', '1.0')

			self.doc.appendChild(smileys)

		for profile in smileys.getElementsByTagName('profile'):
			if profile.getAttribute('name') == PROFILE:
				break
		else:
			profile = self.doc.createElement('profile')
			profile.setAttribute('name', PROFILE)

			smileys.appendChild(self.doc.createTextNode('\n\t'))
			smileys.appendChild(profile)
			smileys.appendChild(self.doc.createTextNode('\n'))

		try:
			self.smiley_set = profile.getElementsByTagName('smiley_set')[0]
		except IndexError:
			self.smiley_set = self.doc.createElement('smiley_set')

			profile.appendChild(self.doc.createTextNode('\n\t\t'))
			profile.appendChild(self.smiley_set)
			profile.appendChild(self.doc.createTextNode('\n\t'))

	def remove_smiley(self, checksum):
		for node in self.smiley_set.childNodes:
			if not isinstance(node, minidom.Element):
				continue
			if node.tagName != 'smiley':
				continue
			if node.getAttribute('checksum').lower() != checksum:
				continue

			try:
				os.unlink(os.path.join(SMILEY_TARGET_DIR, node.getAttribute('filename')))
			except OSError, e:
				if e.errno != errno.ENOENT:
					raise

			while True:
				prev = node.previousSibling
				self.smiley_set.removeChild(node)

				if not isinstance(prev, minidom.Text):
					break

				node = prev

	def add_smiley(self, checksum, filename, data, shortcut):
		while True:
			try:
				with open(os.path.join(SMILEY_TARGET_DIR, filename), 'wb') as f:
					f.write(data)
				break
			except IOError, e:
				if e.errno != errno.ENOENT:
					raise
				os.mkdir(SMILEY_TARGET_DIR)

		smiley = self.doc.createElement('smiley')
		smiley.setAttribute('shortcut', shortcut)
		smiley.setAttribute('checksum', checksum)
		smiley.setAttribute('filename', filename)

		while isinstance(self.smiley_set.lastChild, minidom.Text):
			self.smiley_set.removeChild(self.smiley_set.lastChild)

		self.smiley_set.appendChild(self.doc.createTextNode('\n\t\t\t'))
		self.smiley_set.appendChild(smiley)
		self.smiley_set.appendChild(self.doc.createTextNode('\n\t\t'))

	def install(self):
		for checksum in KILL_LIST:
			self.remove_smiley(checksum)

		for filename in sorted(os.listdir(SMILEY_SOURCE_DIR)):
			with open(os.path.join(SMILEY_SOURCE_DIR, filename), 'rb') as f:
				data = f.read()

			name, ext = os.path.splitext(filename)
			checksum = sha1(data).hexdigest()
			filename = checksum + ext

			self.remove_smiley(checksum)
			self.add_smiley(checksum, filename, data, '*%s*' % name.replace('-', ' '))

		with open(SMILEY_CONFIG_FILE, 'wb') as f:
			f.write(self.doc.toxml('utf-8'))

if __name__ == '__main__':
	Installer().install()
