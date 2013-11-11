#!/usr/bin/python2.4

import cherrypy
import cgi
import tempfile
import memcache
import uuid
import os
from cherrypy import wsgiserver

mc = memcache.Client(['127.0.0.1:11211'])
imgroot = "img"
class myFieldStorage(cgi.FieldStorage):
    
    def make_file(self, binary=None):
        return tempfile.NamedTemporaryFile()

def noBodyProcess():
    cherrypy.request.process_request_body = False

cherrypy.tools.noBodyProcess = cherrypy.Tool('before_request_body', noBodyProcess)

class fileUpload:    
    
    @cherrypy.expose
    def index(self):

        return """
            <html>
            <body>
                <form action="upload" method="post" enctype="multipart/form-data">
                    FileId: <input type="text" name="FileId"/> <br/>
                    File: <input type="file" name="theFile"/> <br/>
                    <input type="submit"/>
                </form>
            </body>
            </html>
            """

    @cherrypy.expose
    @cherrypy.tools.noBodyProcess()
    def upload(self):
        cherrypy.response.timeout = 3600

        
        lcHDRS = {}
        for key, val in cherrypy.request.headers.iteritems():
            lcHDRS[key.lower()] = val
            
        formFields = myFieldStorage(fp=cherrypy.request.rfile,
                                    headers=lcHDRS,
                                    environ={'REQUEST_METHOD':'POST'},
                                    keep_blank_values=True)

        theFile = formFields['theFile']
        FileId = formFields['FileId'].value
        cherrypy.session[FileId] = (theFile.file.name, cherrypy.request.headers['Content-length']) 
        cherrypy.session.save() 
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
        os.link(theFile.file.name, realpath)

        return "%s" % FileId+'.'+suffix
    @cherrypy.expose
    def _status(self, fid=None): 
        if fid == None:
            return "no file id"
        try: 
            print cherrypy.session[fid]
            tempfilepath, length = cherrypy.session[fid] 
        except: # is None or unpack error 
            return 'done' 
        else: 
            currsize = os.stat(tempfilepath).st_size 
            return float(currsize) / length * 100 # float is just for python2 
   
    @cherrypy.expose
    def getImg(self,fileId=None):
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
            imgFile = open(realpath,"rb")
            content = imgFile.read()
            mc.set(fileId.encode("utf-8"),content)
        cherrypy.response.headers['Content-Type'] = "image"
        return content

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
        FileId = formFields['FileId'].value
        cherrypy.session[FileId] = (theFile.file.name, cherrypy.request.headers['Content-length']) 
        cherrypy.session.save() 
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
        os.link(theFile.file.name, realpath)

        return "%s" % FileId+'.'+suffix
    
def application(environ, start_response):
    cherrypy.server.max_request_body_size = 0
    cherrypy.server.socket_timeout = 60
    restful_conf = {
                    '/': {
                          'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                          'tools.sessions.on':True,
                          #'tools.sessions.storage_type':"file",
                          #'tools.sessions.storage_path':"sessions",
                          #'tools.sessions.timeout': 60
                         },
    }
    cherrypy.tree.mount(files(), '/files', config=restful_conf)
    cherrypy.tree.mount(fileUpload(), '/', config = {"/": {'tools.sessions.on':True,
                                                           #'tools.sessions.storage_type':"file",
                                                           #'tools.sessions.storage_path':"sessions",
                                                           #'tools.sessions.timeout': 60
                                                           }})
    return cherrypy.tree(environ, start_response)

server = wsgiserver.CherryPyWSGIServer(('localhost', 8000), application)
server.start()