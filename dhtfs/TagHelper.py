# Copyright (c) 2006, Mayuresh Phadke
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#         * Redistributions of source code must retain the above copyright
#           notice, this list of conditions and the following disclaimer.
#         * Redistributions in binary form must reproduce the above copyright
#           notice, this list of conditions and the following disclaimer in the
# 	    documentation and/or other materials provided with the distribution.
#         * Neither the name of 'QualEx Systems' nor the names of its
# 	    contributors may be used to endorse or promote products derived from
# 	    this software without specific prior written permission.
# 
#         THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import md5	
import os
import logging
import stat
from dhtfs.Tagging import Tagging

class TagFile:
	"""
	This class represents a file in dhtfs.

	Objects of this class will be used as Elements and tags will be associated with them.
	The Instances of this class have two propeties 'location' and 'name' which are used
	to identify the instances.
	"""
	def __init__(self, location, name):

		self.location = os.path.abspath(os.path.normpath(location))
		self.name = name
		self.__hash = 0
		if os.path.isfile(location):
			self.__hash = (self.location + self.name).__hash__() # Avoid recomputing
		else:
			self.location = None

	def __hash__(self):
		return self.__hash

	def __repr__(self):
		if self.location:
			return '<location=%s>' % (self.location)

	def __str__(self):
		if self.location:
			return self.name + " at " + self.location

	def __eq__(self, f):
		if f.location == self.location and  f.name == self.name:
			return True
		else:
			return False

	def __nonzero__(self):
		if self.location == None:
			return False
		else:
			return True

class TagDir(Tagging):
	"""
	This class extends Tagging and implements functions which help in mapping tags to directories
	"""

	DEFAULT_DIR_MODE = (stat.S_IRWXO | stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IWRITE)

	def __str__(self):
		return 'Directory helper for ' + Tagging.__str__(self)

	def __createActualDirs(self, dirs, mode):
		print "in __createActualDirs dirs = ", dirs
		allDirs = self.getAllDirs()
		dirs = [x for x in dirs if x not in allDirs]
		print "After filter dirs = ", dirs
		for dir in dirs:
			dirname = os.path.join(self.db_path, 't_' + dir)
			if not os.path.isdir(dirname):
				print "creating dir ", dirname
				os.mkdir(dirname, mode)

	def __delActualDirs(self, dirs):
		print "in __delActualDirs dirs = ", dirs
		allDirs = self.getAllDirs()
		dirs = [x for x in dirs if x in allDirs]
		print "After filter dirs = ", dirs
		for dir in dirs:
			dirname = os.path.join(self.db_path, 't_' + dir)
			if os.path.isdir(dirname):
				print "Removing dir ", dirname
				os.rmdir(dirname)

	def addDirsToFiles(self, fileList, dirList, mode=DEFAULT_DIR_MODE):
		"""
		Associates the specified directories to the specified files

		@param fileList: List of files to be used
		@type fileList: List of instances of L{TagFile}

		@param dirList: List of directories
		@type dirList: List of str

		@param mode: Mode with which the directories are to be created, if required
		@type mode: int
		"""
		self.__createActualDirs(dirList, mode)
		print 'Adding tags %s to files %s' % (dirList, fileList)
		Tagging.addTags(self, fileList, dirList)

	def createDirs(self, dirs, mode=DEFAULT_DIR_MODE):
		"""
		Create Directories

		@param dirs: directories to be created
		@type dirs: List of str

		@param mode: Mode with which the directories are to be created, if required
		@type mode: int
		"""
		self.__createActualDirs(dirs, mode)
		print 'Adding tags %s to files %s' % (dirs, None)
		Tagging.addTags(self, newTagList=dirs)

	def delDirs(self, dirs):
		"""
		Delete Directories

		@param dirs: directories to be created
		@type dirs: List of str
		"""
		print 'Deleting tags ', dirs
		self.__delActualDirs(dirs)
		Tagging.delTagsFromElements(self, dirs)

	def delFilesFromDirs(self, files, dirs):
		"""
		Delete files from directories

		@param fileList: List of files to be used
		@type fileList: List of instances of L{TagFile}

		@param dirList: List of directories
		@type dirList: List of str
		"""

		print 'Deleting dirs %s from files %s' %(dirs, files)
		self.__delActualDirs(dirs)
		Tagging.delTagsFromElements(self, dirs, files)

	def delFiles(self, files):
		"""
		Delete files

		@param files: List of files to be used
		@type files: List of instances of L{TagFile}
		"""

		Tagging.delElementsFromTags(self, files)
		
	def getAllDirs(self):
		"""
		Get a list of all directories

		@return: List of all directories
		@rtype: List of str
		"""

		return Tagging.getTagsForTags(self, tagList = [])

	def getDirsForFiles(self, files):
		"""
		Get directories which contain the given files

		@param files: List of files to be used
		@type files: List of instances of L{TagFile}

		@return: List of all directories
		@rtype: List of str
		"""

		return Tagging.getTagsForElements(self, files)

	def getDirsForDirs(self, dirList):
		"""
		Get directories which contain the files contained in the given directories

		@param dirList: List of directories to be used
		@type files: List of str

		@return: List of all directories
		@rtype: List of str
		"""

		return Tagging.getTagsForTags(self, dirList)

	def getDirsAndFilesForDirs(self, dirList, beRestrictive=False, getCover=False):
		"""
		Get files contained in all the directories specified in dirList. Also get list of other directories which contain ANY of these files

		@param dirList: List of directories to be used
		@type files: List of str

		@param beRestrictive: Only return those directories which are NOT associated with ALL the files
			with which the given list of directories is associated.

			The philosophy behind this is, having already got a set of files associated
			with the given set of directories, it would be useful to find directories that would restrict
			the set set of directories further. This helps in creating an hierarchy of directories.

			Defaults to False

		@type beRestrictive: bool

		@param getCover: Get a set of directories which between them contain all the files that are contianed
			within the given set of directories.

			This helps particularly when there are large number of tags in the system. Instead of
			looking at 100s of directories it would be helpful to look at only those directories which cover all
			currently selected files.

			Defaults to False

		@type getCover: bool

		@return: A tuple of list of directories and list of files
		@rtype: (List of str, List of instances of L{TagFile})
		"""

		return Tagging.getTagsAndElementsForTags(self, dirList, beRestrictive, getCover)

	def getAllFiles(self):
		"""
		Get a list of all files

		@return: List of all files
		@rtype: List of instances of L{TagFile}
		"""

		return self.getFilesForDirs([])

	def getFilesForDirs(self, dirList):
		"""
		Get a list of files which are contained in all of the given directories

		@param dirList: Directories for which to get files
		@type dirList: List of str

		@return: List of files
		@rtype: List of instances of L{TagFile}
		"""
		return Tagging.getElements(self, dirList)

	def isDir(self, fname):
		"""
		Check whether the specified name is the name of a directory

		@param fname: Name to be checked
		@type fname: str

		@return: True is fname is a directory, False otherwise
		@rtype: bool
		"""
		if fname in self.getAllDirs():
			return True
		else:
			return False

	def getActualLocation(self, dirs, filename):
		filesInDir = Tagging.getElements(self, dirs)
		matchingFiles = [x for x in filesInDir if x.name == filename]
		if len(matchingFiles) == 0:
			return None
		else:
			return matchingFiles[0].location
		
def getMimeTypes(location):
	(mt, zz) = mimetypes.guess_type(location)
	if mt:
		mimeTags = mt.split('/')
	else:
		mimeTags = []

# Any file or folder starting with . will be treated as hidden
# this is very UNIX specific
# TODO: Windows port
def hiddenDir(d):
	if d[0] == ".":
		return True
	else:
		return False

def notHiddenFile(f):
	if f[0] == ".":
		return False
	else:
		return True

def addTagsToDir(tagging, dirname, tagList, targetDir, includeDirsInPath=False, recursive=True, excludeDirList=[],
		includeHiddenDirs=False, includeHiddenFiles=False, addDirsAsTags=False,
		addMimeTags=False, mimeTagFunc=getMimeTypes, logging=None):
	td = TagDir(tagging)
	dirname = os.path.normpath(dirname)
	dirname = os.path.abspath(dirname)
	origDirsInPath = dirname.split(os.path.sep)[1:-1]

	if logging:
		logging.info('Adding tags to files in directory %s' % dirname)

	# Walk the directory structure and add the directories in the path as tags to the files
	# Look up the documentation of os.walk() for the syntax
	for root, dirnames, files in os.walk(dirname):
		if logging:
			logging.info("Processing directory: %s" % root)

		if not includeHiddenDirs:
			# Trim dirnames to include only non-hidden directories
			# The dirnames argument needs to be modified in place so that
			# it affects the behavior of os.walk()
			hiddenDirNames = filter(hiddenDir, dirnames)
			for d in hiddenDirNames:
				dirnames.remove(d)

		# Trim dirnames to remove directories from the exclude list
		for d in excludeDirList:
			if d in dirnames: dirnames.remove(d)

		if not includeHiddenFiles:
			# Trim files to include only non-hidden files
			files = filter(notHiddenFile, files)

		fiList = [TagFile(os.path.join(root, f), f) for f in files]
		td.createDirs(tagList, root=targetDir)
		td.addDirsToFiles(fiList, tagList)
		if logging:
			logging.info('Tags %s added to files %s' %(tagList, fiList))

		if addDirsAsTags:
			# Tag the files in a directory with directory names as tags
			# e.g. The files foo1 and foo2 in directory dir1/dir2 will be tagged with dir1 and dir2 
			# get list of directories that make up this path
			dirsInPath = root.rsplit('/')
			if not includeDirsInPath:
				dirsInPath = [x for x in dirsInPath if x not in origDirsInPath]

			td.createDirs(dirsInPath, root=targetDir)
			td.addDirsToFiles(fiList, dirsInPath)
			if logging:
				logging.info('Dirs %s added to files %s' %(dirsInPath, fiList))

		if addMimeTags:
			for fi in fiList:
				mimeTags = getMimeTypes(location)
				td.createDirs(mimeTags, root=targetDir)
				td.addDirsToFiles([fi], mimeTags)
				if logging:
					logging.info('Mime tags %s added to file %s' %(mimeTags, fi))

		if not recursive:
			del dirnames[:]
def getLogger(name):
	logging.basicConfig(level=logging.DEBUG,
		format='%(asctime)s: %(levelname)s: %(name)s: %(message)s',
		filename='/tmp/dhtfs.log',
		filemode='a')

	return logging.getLogger(name)

def main():
	from Tagging import Tagging
	import os

	# Set up test environment
	testDirectory = '/tmp/testTagHelper'
	if not os.path.exists(testDirectory):
		os.makedirs(testDirectory)

	files = ['file1', 'file2', 'file3']
	locations = [os.path.join(testDirectory, f) for f in files]

	for l in locations:
		x = file(l, 'w')
		x.write("This is file %s" % l)
		x.close()

	# Create an instance of tagging
	td = TagDir(testDirectory)
	td.initDB(forceInit=True)

	# Save all the files in Tagging DB
	tagFileInstances = []
	for l in locations:
		tf = TagFile(l, os.path.basename(l))
		tagFileInstances.append(tf)

	td.addDirsToFiles(tagFileInstances, ['root'])
	x = td.getFilesForDirs(['root'])
	if len(x) != len(tagFileInstances):
		print 'Test 1 failed'
	else:
		print 'Test 1 passed'

	print x

if __name__ == '__main__':
	main()
