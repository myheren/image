#!/usr/bin/python
import sys
import urllib
import urllib2
import mimetools, mimetypes
import os, stat
from cStringIO import StringIO

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1

class MultipartPostHandler(urllib2.BaseHandler):
    handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first
    def __init__(self,seekP = -1,msize = -1):
        self.seekPoint = seekP
        self.maxsize = msize
        self.realsize = 0
        self.filesize = 0
    def http_request(self, request):
        data = request.get_data()
        if data is not None and type(data) != str:
            v_files = []
            v_vars = []
            try:
                for(key, value) in data.items():
                    if type(value) == file:
                        v_files.append((key, value))
                    else:
                        v_vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise TypeError, "not a valid non-string sequence or mapping object", traceback

            if len(v_files) == 0:
                data = urllib.urlencode(v_vars, doseq)
            else:
                boundary, data = self.multipart_encode(self, v_vars, v_files)
                if self.seekPoint != -1 or self.maxsize != -1:
                    filerange = "bytes "
                    if self.seekPoint != -1:
                        startpoint = self.seekPoint
                    else:
                        startpoint= 0
                    filerange += str(startpoint)
                    filerange += '-'
                    if self.maxsize != -1:
                        endpoint = startpoint + self.realsize - 1
                    else:
                        endpoint = self.filesize - 1
                    filerange += str(endpoint) + '/' + str(self.filesize)
                    request.add_unredirected_header('Content-Range', filerange)
                    
                contenttype = 'multipart/form-data; boundary=%s' % boundary
                if(request.has_header('Content-Type')
                   and request.get_header('Content-Type').find('multipart/form-data') != 0):
                    print "Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)
        
        return request

    def multipart_encode(self, myvars, files, boundary = None, buf = None):
        if boundary is None:
            boundary = mimetools.choose_boundary()
        if buf is None:
            buf = StringIO()
        for(key, value) in myvars:
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"' % key)
            buf.write('\r\n\r\n' + value + '\r\n')
        for(key, fd) in files:
            self.filesize = os.fstat(fd.fileno())[stat.ST_SIZE]
            filename = fd.name.split('/')[-1]
            contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
            buf.write('Content-Type: %s\r\n' % contenttype)
            # buffer += 'Content-Length: %s\r\n' % file_size
            if self.seekPoint != -1:
                fd.seek(self.seekPoint)
            if self.maxsize != -1:
                filecontent = fd.read(self.maxsize)   
            else:
                filecontent = fd.read()
            self.realsize = len(filecontent)
            buf.write('\r\n' + filecontent + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf
    multipart_encode = Callable(multipart_encode)

    https_request = http_request

def main():
    import tempfile

    validatorURL = "http://validator.w3.org/check"
    opener = urllib2.build_opener(MultipartPostHandler)

    def validateFile(url):
        temp = tempfile.mkstemp(suffix=".html")
        os.write(temp[0], opener.open(url).read())
        params = { "ss" : "0",            # show source
                   "doctype" : "Inline",
                   "uploaded_file" : open(temp[1], "rb") }
        print opener.open(validatorURL, params).read()
        os.remove(temp[1])

    if len(sys.argv[1:]) > 0:
        for arg in sys.argv[1:]:
            validateFile(arg)
    else:
        validateFile("http://www.google.com")

if __name__=="__main__":
    main()
