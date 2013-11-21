#!/usr/bin/python2.4

import cherrypy
import cgi
import tempfile
import memcache
import uuid
import os
from cherrypy import wsgiserver
import shutil

mc = memcache.Client(['127.0.0.1:11211'])
imgroot = "img"
fileUploading = {}


def uploadFileExist(FileId):
    if FileId == None:
        return False
    return os.path.exists(FilePath(FileId))


def FilePath(FileId):
    if FileId == None:
        return ""
    filenamelists = FileId.split('.')
    if len(filenamelists) < 1 or len(filenamelists) > 2:
        return ""
    if len(filenamelists) == 1:
        filenamelists.append('none') 
    filename = filenamelists[0]
    suffix = filenamelists[1]
    realpath = '/'.join([imgroot,suffix,filename[0:3], filename[4:6], filename[7:9],filename[10:]])
    if suffix != 'none':
        realpath = realpath+'.'+suffix
    return realpath

class myFieldStorage(cgi.FieldStorage):
    
    def make_file(self, binary=None):
        tmpfile = None
        try:
            FileId = cherrypy.request.headers['FileId']
        except:
            FileId = ""
        if uploadFileExist(FileId):
            filePath = FilePath(FileId)
            tmpfile = open(filePath,'ab')
            fileUploading[FileId] = (filePath, int(cherrypy.request.headers['Content-length']))
        else:
            tmpfile = tempfile.NamedTemporaryFile()
            fileUploading[FileId] = (tmpfile.name, int(cherrypy.request.headers['Content-length'])) 
        return tmpfile
        
    def read_single(self):
        """Modified: Internal: read an atomic part."""
        if(self.name == "theFile"):
            try:
                FileId = cherrypy.request.headers['FileId']
            except:
                FileId = ""
            if uploadFileExist(FileId):
                filePath = FilePath(FileId)
                #self.fp.read(len(self.outerboundary))
                print os.stat(filePath).st_size
                print self.fp.read(os.stat(filePath).st_size)
        if self.length >= 0:
            self.read_binary()
            self.skip_lines()
        else:
            self.read_lines()
        self.file.seek(0)
        
def noBodyProcess():
    cherrypy.request.process_request_body = False

cherrypy.tools.noBodyProcess = cherrypy.Tool('before_request_body', noBodyProcess)

class fileUpload:    
    
    @cherrypy.expose
    def uploadingStatus(self, fid=None): 
        if fid == None:
            return "no file id"
        try: 
            tempfilepath, length = fileUploading[fid] 
        except: # is None or unpack error 
            return 'no such file uploading' 
        else: 
            if os.path.exists(tempfilepath):
                currsize = os.stat(tempfilepath).st_size 
            else:
                FileId = cherrypy.request.headers['FileId']
                fpath = FilePath(FileId)
                if os.path.exists(fpath):
                    currsize = os.stat(fpath).st_size
                    return "aborted: " + str(float(currsize) / length * 100) + '%' 
                else:
                    return "upload failed"
            return str(float(currsize) / length * 100) + '%' 

class files(object):
    exposed = True
    def GET(self,fileId=None):
        if fileId == None:
            return "no file id"
        #mc.set("hello","world")
        #print mc.get("hello")
        filenamelists = fileId.split('.')
        if len(filenamelists) != 2:
            return "invalid file id"
        filename = filenamelists[0]
        suffix = filenamelists[1]
        realpath = '/'.join([imgroot,suffix,filename[0:3], filename[4:6], filename[7:9],filename[10:]])
        if suffix != 'none':
            realpath = realpath+'.'+suffix
        
        content = mc.get(fileId.encode("utf-8"))
        if  content == None:
            try:
                imgFile = open(realpath,"rb")
            except:
                return "file no exist"
            content = imgFile.read()
            mc.set(fileId.encode("utf-8"),content)
        cherrypy.response.headers['Content-Type'] = "image"
        return content
   
    @cherrypy.tools.noBodyProcess()
    def POST(self):
        cherrypy.response.timeout = 3600
        try:
            del cherrypy.file_transfers[cherrypy.request.remote_addr][myfile1.filename]
        except KeyError:
            pass

        tmpdir = os.path.join(os.getcwd(), "img")
        if len(myfile1.filename) > 0:
            self.save_file(os.path.join(tmpdir, os.path.basename(myfile1.filename)), myfile1.file)

        return self.upload(msg="uploaded %s and %s" % (myfile1.filename, myfile2.filename))
    
    def upload(self, msg=""):
        return dict(message=msg)
    
    def save_file(self, filepath, file):
        chunk_size = 8192
        # return if file is empty
        if not file:
            return
        # create new file on file system
        savedfile = open(filepath, "wb")
        # save data to this new file in chunks
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            savedfile.write(data)
def application(environ, start_response):
    cherrypy.server.max_request_body_size = 0
    cherrypy.server.socket_timeout = 60
    restful_conf = {
                    '/': {
                          'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                          #'tools.sessions.on':True,
                          #'tools.sessions.storage_type':"file",
                          #'tools.sessions.storage_path':"sessions",
                          #'tools.sessions.timeout': 60
                         },
    }
    cherrypy.tree.mount(files(), '/files', config=restful_conf)
    cherrypy.tree.mount(fileUpload(), '/', config = {"/": {#'tools.sessions.on':True,
                                                           #'tools.sessions.storage_type':"file",
                                                           #'tools.sessions.storage_path':"sessions",
                                                           #'tools.sessions.timeout': 60
                                                           }})
    return cherrypy.tree(environ, start_response)

server = wsgiserver.CherryPyWSGIServer(('localhost', 8000), application)
server.start()