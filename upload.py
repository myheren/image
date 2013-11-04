#!/usr/bin/python2.4

import cherrypy
import cgi
import tempfile
import memcache
import uuid
import os

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
                    File: <input type="file" name="theFile"/> <br/>
                    <input type="submit"/>
                </form>
            </body>
            </html>
            """

    @cherrypy.expose
    @cherrypy.tools.noBodyProcess()
    def upload(self, theFile=None):
        cherrypy.response.timeout = 3600

        lcHDRS = {}
        for key, val in cherrypy.request.headers.iteritems():
            lcHDRS[key.lower()] = val
            
        formFields = myFieldStorage(fp=cherrypy.request.rfile,
                                    headers=lcHDRS,
                                    environ={'REQUEST_METHOD':'POST'},
                                    keep_blank_values=True)

        theFile = formFields['theFile']
        namelist = theFile.filename.split('.')
        suffix = namelist[len(namelist)-1]
        if suffix == '':
            suffix = 'none'
        
        uid = uuid.uuid4();
        stored_path = '/'.join([imgroot,suffix,uid.hex[0:3], uid.hex[4:6], uid.hex[7:9],uid.hex[10:]]);
        dirname = "/".join([imgroot,suffix,uid.hex[0:3], uid.hex[4:6], uid.hex[7:9]]);
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        realpath = stored_path
        if suffix != 'none':
            realpath = stored_path+'.'+suffix
            
        realfile = open(realpath,"w+b")
        realfile.write(theFile.file.read());

        return "%s" % uid.hex+'_'+suffix

    @cherrypy.expose
    def getImg(self,fileId=None):
        if fileId == None:
            return "no file id"
        #mc.set("hello","world")
        #print mc.get("hello")
        filenamelists = fileId.split('_')
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
        filenamelists = fileId.split('_')
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
   
    @cherrypy.tools.noBodyProcess()
    def POST(self, theFile=None):
        cherrypy.response.timeout = 3600

        lcHDRS = {}
        for key, val in cherrypy.request.headers.iteritems():
            lcHDRS[key.lower()] = val
            
        formFields = myFieldStorage(fp=cherrypy.request.rfile,
                                    headers=lcHDRS,
                                    environ={'REQUEST_METHOD':'POST'},
                                    keep_blank_values=True)

        theFile = formFields['theFile']
        namelist = theFile.filename.split('.')
        suffix = namelist[len(namelist)-1]
        if suffix == '':
            suffix = 'none'
        
        uid = uuid.uuid4();
        stored_path = '/'.join([imgroot,suffix,uid.hex[0:3], uid.hex[4:6], uid.hex[7:9],uid.hex[10:]]);
        dirname = "/".join([imgroot,suffix,uid.hex[0:3], uid.hex[4:6], uid.hex[7:9]]);
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        realpath = stored_path
        if suffix != 'none':
            realpath = stored_path+'.'+suffix
            
        realfile = open(realpath,"w+b")
        realfile.write(theFile.file.read());

        return "%s" % uid.hex+'_'+suffix
    
def application(environ, start_response):
    cherrypy.server.max_request_body_size = 0
    cherrypy.server.socket_timeout = 60
    restful_conf = {
                    '/': {
                          'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                         },
    }
    cherrypy.tree.mount(files(), '/files', config=restful_conf)
    return cherrypy.tree(environ, start_response)

