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
        FileId = cherrypy.request.headers['FileId']
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
            FileId = cherrypy.request.headers['FileId']
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

        
        lcHDRS = {}
        for key, val in cherrypy.request.headers.iteritems():
            lcHDRS[key.lower()] = val
            
        formFields = myFieldStorage(fp=cherrypy.request.rfile,
                                    headers=lcHDRS,
                                    environ={'REQUEST_METHOD':'POST'},
                                    keep_blank_values=True)
        
        theFile = formFields['theFile']
        FileId = cherrypy.request.headers['FileId'].split(".")[0]
        namelist = theFile.filename.split('.')
        suffix = namelist[len(namelist)-1]
        if suffix == '':
            suffix = 'none'
            
        if FileId == None:
            uid = uuid.uuid4();
            FileId = uid.hex;
                        
        stored_path = '/'.join([imgroot,suffix,FileId[0:3], FileId[4:6], FileId[7:9],FileId[10:]]);
        dirname = "/".join([imgroot,suffix,FileId[0:3], FileId[4:6], FileId[7:9]]);
            
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        realpath = stored_path
        if suffix != 'none':
            realpath = stored_path+'.'+suffix
            
        #realfile = open(realpath,"w+b")
        #realfile.write(theFile.file.read());
        if not uploadFileExist(cherrypy.request.headers['FileId']):
            os.link(theFile.file.name, realpath)
        #else:
            #destination = open(realpath, 'ab')
            #shutil.copyfileobj(open(realpath+".append", 'rb'), destination)
            #destination.close()

        return "%s" % FileId+'.'+suffix
    
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