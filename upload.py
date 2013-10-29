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
            
        uid = uuid.uuid4();
        stored_path = '/'.join([uid.hex[0:3], uid.hex[4:6], uid.hex[7:9],uid.hex[10:]]);
        dirname = "/".join([imgroot,uid.hex[0:3], uid.hex[4:6], uid.hex[7:9]]);
        if not os.path.exists(dirname):
            os.makedirs(dirname);
        formFields = myFieldStorage(fp=cherrypy.request.rfile,
                                    headers=lcHDRS,
                                    environ={'REQUEST_METHOD':'POST'},
                                    keep_blank_values=True)

        theFile = formFields['theFile']
        realfile = open(imgroot+"/"+stored_path,"w+b")
        realfile.write(theFile.file.read());

        return "%s" % stored_path

    @cherrypy.expose
    def getImg(self,fileName=None):
        if fileName == None:
            return ""
        #mc.set("hello","world")
        #print mc.get("hello")
        content = mc.get(fileName.encode("utf-8"))
        if  content == None:
            imgFile = open(imgroot+"/"+fileName,"rb")
            content = imgFile.read()
            mc.set(fileName.encode("utf-8"),content)
        cherrypy.response.headers['Content-Type'] = "image"
        return content


cherrypy.server.max_request_body_size = 0

cherrypy.server.socket_timeout = 60

cherrypy.quickstart(fileUpload())
