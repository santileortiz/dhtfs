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

import os, sys
from errno import *
from stat import *
import fuse
from fuse import Fuse
import TagHelper
from TagHelper import TagDir, TagFile
from Tagging import Tagging
from GPStor import GPStor

fuse.feature_assert('stateful_files')

def flag2mode(flags):
	md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
	m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]

	if flags | os.O_APPEND:
		m = m.replace('w', 'a', 1)

	return m

class Dhtfs(Fuse):

	MAX_DIR_ENTRIES = 210
	MISSING_FILE = '__MISSING_FILE_qwertyuiopasdfghjklzxcvbnm0987654321'		

	DB_FILE = '.dhtfs.db'
	SEQ_FILE = '.dhtfs.seq'

	def checkSetup(cls, path):
		"""
		D.checkSetup() -> Check whether dhtfs filesystem is setup at path

		@param path: Path to be checked
		@type path: str

		@return: True is dhtfs is setup at path, False otherwise
		@rtype: bool
		"""

		if not Tagging.checkSetup(db_path=path, db_file=cls.DB_FILE):	
			return False
		if not GPStor.checkSetup(db_path=path, db_file=cls.SEQ_FILE):
			return False

		return True
		
	checkSetup = classmethod(checkSetup)

	def setup(cls, path, forceInit=False):
		"""
		D.setup(path, forceInitFlag) -> Do the necessary setup to mount the specified path as a dhtfs file system

		@param path: Path for which to setup
		@type path: str

		@param forceInit: If forceInit is True, do a new setup regardless of whether an older setup is present.
		@type forceInit: bool
		"""

		# If forceInit flag is true, clean up the directory
		if forceInit:
			for root, dirs, files in os.walk(path, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))

		# Initialize tagging

		t = Tagging(db_path=path, db_file=cls.DB_FILE)
		t.initDB(forceInit = forceInit)

		# Initialize sequence generator
		seqStore = GPStor(db_path=path, db_file=cls.SEQ_FILE)

		ret, currentSeqNumber = seqStore.getDataRO()

		if (ret != 0) or (not isinstance(currentSeqNumber, long) ) or forceInit:
			seqStore.getDataRW()
			currentSeqNumber = long(0)
			seqStore.writeData(currentSeqNumber)

	setup = classmethod(setup)

	def __init__(self, *args, **kw):

		Fuse.__init__(self, *args, **kw)
		self.fileCache = {}

	def __initialize(self):
		try:
			X = self.getCover
		except:
			self.getCover = "Dont Care"

		self.tagdir = TagDir(db_path=self.root, db_file=self.DB_FILE)
		self.logger = TagHelper.getLogger('DHTFS')
		self.__initSequenceNumberGenerator()

		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.logger.info("Tagging and TagDir instances created for path %s" % self.root)
		self.logger.info("self.getCover = %s" % self.getCover)

	def __initSequenceNumberGenerator(self):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.seqStore = GPStor(db_path=self.root, db_file='.dhtfs.seq')
		ret, self.currentSeqNumber = self.seqStore.getDataRO()
		if ret != 0:
			self.seqStore.getDataRW()
			self.currentSeqNumber = long(0)
			self.seqStore.writeData(self.currentSeqNumber)
			self.logger.info("Initialized seq store with %s" % long(0))
			
	def __getNextSeqNumber(self):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		ret, num = self.seqStore.getDataRW()
		self.logger.info("ret = %s, num = %s" % (ret, num))
		self.currentSeqNumber = num + 1
		self.seqStore.writeData(self.currentSeqNumber)
		return self.currentSeqNumber

	def getActualPath(self, path):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)

		if path in self.fileCache:
			self.logger.info("Path found in cache")
			actualPath = self.fileCache[path]

		elif path == '/':
			self.logger.info("Path is root directory")
			actualPath = self.root

		elif self.tagdir.isDir(os.path.basename(path)):
			self.logger.info("Path is directory")
			actualPath = os.path.join(self.root, 't_' + os.path.basename(path))
		else:
			self.logger.info("get actual path from TagHelper")
			dirs = [x for x in os.path.dirname(path).split(os.path.sep) if x != '']
			filename = os.path.basename(path)
			actualLocation = self.tagdir.getActualLocation(dirs, filename)
			if actualLocation:
				actualPath = os.path.join(self.root, actualLocation)
			else:
				actualPath = os.path.join(self.root, Dhtfs.MISSING_FILE)

		self.logger.info("Path =  %s, ActualPath =  %s" % (path, actualPath))

		return actualPath

	def opendir(self, path):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.logger.info("path = %s" % path)

	def releasedir(self, path):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.logger.info("path = %s" % path)

	def getattr(self, path):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.logger.info("path = %s" % path)
		return os.lstat(self.getActualPath(path))

	def readdir(self, path, offset):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.logger.info("self.getCover = %s" % self.getCover)

		# Get the directories in the specified path
		# The directories in the path will be treated as tags
		dirsInPath = [x for x in path.split(os.path.sep) if x != '']

		# get files and directories associated with the given tags
		if self.getCover != 'Always':
			dirs, files = self.tagdir.getDirsAndFilesForDirs(dirsInPath, beRestrictive=True)
			self.logger.info("After getDirsAndFilesForDirs beRestrictive=True, \
					dirs = %s, files = %s" %(dirs, files))

		# Too many directory entries cause problems
		#	It takes too long to display all entries
		#	Too cumbersome to go through all the entries
		#
		# If we get too many directory entries just get tags which cover
		# all the files + the remaining files
		if (self.getCover == 'Always') or len(files) < 2 or \
				(	len(dirs) > 0 and 
					len(dirs) + len(files) > Dhtfs.MAX_DIR_ENTRIES and
					self.getCover != 'Never'
				):
			self.logger.info("Dir entries exceeded %d. getting cover" % Dhtfs.MAX_DIR_ENTRIES)	
			dirs, files = self.tagdir.getDirsAndFilesForDirs(dirsInPath, getCover=True)
			self.logger.info("After getDirsAndFilesForDirs getCover=True, \
					dirs = %s, files = %s" %(dirs, files))
				
		# Cache the mapping between 'location in our file system' -> 'location in the underlying file system'
		self.fileCache.clear()
		self.fileCache.update([(os.path.join(path, f.name), os.path.join(self.root, f.location)) for f in files])
		self.fileCache.update([(os.path.join(path, dir), os.path.join(self.root, 't_' + dir)) for dir in dirs])
		self.logger.info("Added info for dir %s to cache" % path)

		# Get file names from the file object
		filenames = [f.name for f in files]
		self.logger.info("Dir entries = %s" % (filenames + dirs))

		# Create a generator for the directory entries
		for e in filenames + dirs:
			yield fuse.Direntry(e)

	def rmdir(self, path):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		self.tagdir.delDirs([os.path.basename(path)])

#	def rename(self, path, path1):
#		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
#		os.rename(self.root + path, self.root + path1)

	def chmod(self, path, mode):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		os.chmod(self.getActualPath(path), mode)

	def chown(self, path, user, group):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		os.chown(self.getActualPath(path), user, group)

	def truncate(self, path, len):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		f = open(self.getActualPath(path), "a")
		f.truncate(len)
		f.close()

	def mkdir(self, path, mode):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		dirs = [x for x in path.split(os.path.sep) if x != '']
		self.tagdir.createDirs(dirs, mode=mode)

	def utime(self, path, times):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		os.utime(self.getActualPath(path), times)

	def access(self, path, mode):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		if not os.access(self.getActualPath(path), mode):
			return -EACCES

	def statfs(self):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
		"""
		Should return an object with statvfs attributes (f_bsize, f_frsize...).
		Eg., the return value of os.statvfs() is such a thing (since py 2.2).
		If you are not reusing an existing statvfs object, start with
		fuse.StatVFS(), and define the attributes.

		To provide usable information (ie., you want sensible df(1)
		output, you are suggested to specify the following attributes:

			- f_bsize - preferred size of file blocks, in bytes
			- f_frsize - fundamental size of file blcoks, in bytes
				[if you have no idea, use the same as blocksize]
			- f_blocks - total number of blocks in the filesystem
			- f_bfree - number of free blocks
			- f_files - total number of file inodes
			- f_ffree - nunber of free file inodes
		"""

		return os.statvfs(self.root)

	def unlink(self, path):
		self.logger.info("In function : %s" % sys._getframe().f_code.co_name)

		# Get dirs in path
		dirs = [x for x in os.path.dirname(path).split(os.path.sep) if x != '']

		# create an instance of class TagFile
		fi = TagFile(self.getActualPath(path), os.path.basename(path))

		# Remove the directories asociated with the file
		self.tagdir.delFilesFromDirs([fi], dirs)
		self.logger.info("Deleted %s" % path)

		# If all directories asociated with the file are removed remove the file
		if len( self.tagdir.getDirsForFiles([fi]) ) == 0:
			self.logger.info("Deleting actual file since last reference is being deleted")	
			self.tagdir.delFiles([fi])
			os.unlink(fi.location)

	def generateNewFileName(self):
		number = self.__getNextSeqNumber()
		newfilename = 'f_' + ('%x' % number).rjust(32, '0')
		self.logger.info("newfilename = %s" % newfilename)
		actualPath = newfilename

		return actualPath

	def main(self, *a, **kw):

		# Define the file class locally as that seems to be the easiest way to
		# inject instance specific data into it...

		server = self

		if server.fuse_args.mount_expected():
			server.__initialize()

		class DhtfsFile(object):

			def __init__(self, path, flags, *mode):
				# set logger
				self.logger = server.logger
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)

				if path == '/.mount.db':
					self.file = SpoofFile()
					return

				# set the dirs which are associated with this file
				self.dirs = [x for x in os.path.dirname(path).split(os.path.sep) if x != '']

				# Get actual path for the specified path
				actualPath = server.getActualPath(path)

				newCreated = False
				if os.path.basename(actualPath) == Dhtfs.MISSING_FILE:
					# File is not yet created. Create file

					self.logger.info("Actual path missing")
					actualPath = server.generateNewFileName()
					newCreated = True

				self.file = os.fdopen(os.open(os.path.join(server.root, actualPath), flags, *mode),
										flag2mode(flags))
				self.fd = self.file.fileno()

				filename = os.path.basename(path)
				self.fi = TagFile(actualPath, filename)

				if newCreated:
					self.logger.info("Adding tags %s, to file %s" %(self.dirs, self.fi))
					# Add tag information for the newly created file
					server.tagdir.addDirsToFiles([self.fi], self.dirs)

			def read(self, length, offset):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				self.file.seek(offset)
				return self.file.read(length)

			def write(self, buf, offset):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				self.file.seek(offset)
				self.file.write(buf)
				return len(buf)

			def release(self, flags):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				self.file.close()

			def fsync(self, isfsyncfile):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				if isfsyncfile and hasattr(os, 'fdatasync'):
					os.fdatasync(self.fd)
				else:
					os.fsync(self.fd)

			def flush(self):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				self.file.flush()
				# cf. xmp_flush() in fusexmp_fh.c
				os.close(os.dup(self.fd))

			def fgetattr(self):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				return os.fstat(self.fd)

			def ftruncate(self, len):
				self.logger.info("In function : %s" % sys._getframe().f_code.co_name)
				self.file.truncate(len)

		self.file_class = DhtfsFile

		return Fuse.main(self, *a, **kw)


def main():

	usage = """
Generates Dynamic Hierarchy for Files from tags associated with files. Generated for files in directory specified as root

""" + Fuse.fusage

	server = Dhtfs(version="%prog " + fuse.__version__,
					usage=usage,
					dash_s_do='setsingle')

	server.parser.add_option(mountopt="root", metavar="PATH", default='/', dest="root",
								help="use filesystem from under PATH [default: %default]")
	server.parse(values=server, errex=1)

	# server.root is not getting set by default, workaround it for now
	# TODO: Look into this
	try:
		X = server.root
	except AttributeError:
		server.root = '/'

	if server.fuse_args.mount_expected():
		try:
			os.stat(server.root)
		except OSError:
			print >> sys.stderr, "can't stat root of underlying filesystem"
			sys.exit(1)

	server.main()

if __name__ == '__main__':
	main()
