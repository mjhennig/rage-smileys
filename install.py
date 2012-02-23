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

try:
	os.mkdir(SMILEY_TARGET_DIR)
except OSError, e:
	if e.errno != errno.EEXIST:
		raise

try:
	with open(SMILEY_CONFIG_FILE, 'rb') as f:
		doc = minidom.parseString(f.read())
except IOError, e:
	if e.errno != errno.ENOENT:
		raise
	doc = minidom.Document()

try:
	smileys = doc.getElementsByTagName('smileys')[0]
except IndexError:
	smileys = doc.createElement('smileys')
	smileys.setAttribute('version', '1.0')

	doc.appendChild(smileys)

for profile in smileys.getElementsByTagName('profile'):
	if profile.getAttribute('name') == PROFILE:
		break
else:
	profile = doc.createElement('profile')
	profile.setAttribute('name', PROFILE)

	smileys.appendChild(doc.createTextNode('\n\t'))
	smileys.appendChild(profile)
	smileys.appendChild(doc.createTextNode('\n'))

try:
	smiley_set = profile.getElementsByTagName('smiley_set')[0]
except IndexError:
	smiley_set = doc.createElement('smiley_set')

	profile.appendChild(doc.createTextNode('\n\t\t'))
	profile.appendChild(smiley_set)
	profile.appendChild(doc.createTextNode('\n\t'))

for filename in sorted(os.listdir(SMILEY_SOURCE_DIR)):
	with open(os.path.join(SMILEY_SOURCE_DIR, filename), 'rb') as f:
		contents = f.read()

	name, ext = os.path.splitext(filename)
	checksum = sha1(contents).hexdigest()
	filename = checksum + ext

	with open(os.path.join(SMILEY_TARGET_DIR, filename), 'wb') as f:
		f.write(contents)

	for node in smiley_set.childNodes:
		if not isinstance(node, minidom.Element):
			continue
		if node.tagName != 'smiley':
			continue
		if node.getAttribute('checksum').lower() != checksum:
			continue

		while True:
			prev = node.previousSibling
			smiley_set.removeChild(node)

			if not isinstance(prev, minidom.Text):
				break

			node = prev

	smiley = doc.createElement('smiley')
	smiley.setAttribute('shortcut', '*%s*' % name.replace('-', ' '))
	smiley.setAttribute('checksum', checksum)
	smiley.setAttribute('filename', filename)

	while isinstance(smiley_set.lastChild, minidom.Text):
		smiley_set.removeChild(smiley_set.lastChild)

	smiley_set.appendChild(doc.createTextNode('\n\t\t\t'))
	smiley_set.appendChild(smiley)
	smiley_set.appendChild(doc.createTextNode('\n\t\t'))

with open(SMILEY_CONFIG_FILE, 'wb') as f:
	f.write(doc.toxml('utf-8'))
