Most file systems organize files in a directory hierarchy. A file is stored in a particular directory. When it is needed to store a file, a decision has to be made about the most suitable directory for the file. This can be tough.

IMO, when presented with data, a human being generally associates a set of attributes to data rather than looking at various attributes and selecting the best fit. i.e. On seeing a Lion, a human brain would attach attributes like ferocious, wild, huge, carnivorous, etc. It would be tough, if ten different attributes are given and the one most fitting attribute needs to be assigned.

_[View User Guide](http://code.google.com/p/dhtfs/wiki/UserGuide?tm=6)_

Similiarly, on observing some file, attributes like, music, favorite, needs\_backup, work, picture etc could spring up in mind. But while storing the file it can only be stored in a single directory. Some workaround would be done like storing a favourite picture in directory 'pics/favorite'. The problem here is the hierarchy between 'pics' and 'favorite' is unchangable. Browsing through all favorites from 'music', 'pics', 'poems' etc is quite cumbersome.

Tagging is a more intutive way of organizing data. All the attributes of a file can be stored as tags to the file. Browsing through files by the tags associated with them is easy.

The problem is that traditional file systems do not support a tagging structure.

This project aims at making the benefits of tagging available through a traditional filesystem framework like VFS.

The aims of this project are as follows:

  1. Integrate tagging with traditional filesystem (VFS)
  1. The directory hierarchies should be dynamically generated depending on the users browsing pattern

The filesystem would be implemented using FUSE and fuse-python bindings.

The packages are available for download from the download link.

Please send your feedbacks / comments to mayuresh (at) gmail.com.

[Design discussion and User Guide](http://code.google.com/p/dhtfs/wiki/UserGuide?tm=6)