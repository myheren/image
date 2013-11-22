#!/usr/bin/python2.4

import cherrypy
import cgi
import tempfile
import memcache
import uuid
import os
from cherrypy import wsgiserver
import json
import shutil

mc = memcache.Client(['127.0.0.1:11211'])
imgroot = "img"

class myFieldStorage(cgi.FieldStorage):
    
    def make_file(self, binary=None):

        tmpfile = tempfile.NamedTemporaryFile() 
        return tmpfile
        
def noBodyProcess():
    cherrypy.request.process_request_body = False

cherrypy.tools.noBodyProcess = cherrypy.Tool('before_request_body', noBodyProcess)

def CORS(): 
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
    cherrypy.response.headers['Access-Control-Allow-Methods'] = "GET,PUT,POST,DELETE,OPTIONS"
    cherrypy.response.headers['Access-Control-Allow-Headers'] = "Content-Type, Content-Range, Content-Disposition, Content-Description"
    #cherrypy.response.headers['Access-Control-Allow-Credentials'] = "true"
    cherrypy.response.headers['Allow'] = "GET,PUT,POST,DELETE"
    
cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)

class files(object):
    exposed = True
    
    @cherrypy.tools.CORS()
    def OPTIONS(self):
        return ''
    
    @cherrypy.tools.CORS()
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
    @cherrypy.tools.CORS()
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
        try:
            FileId = formFields['FileId'].value
        except:
            FileId = None
        namelist = theFile.filename.split('.')
        suffix = namelist[len(namelist)-1]
        if suffix == '':
            suffix = 'none'
            
        if FileId == None:
            uid = uuid.uuid4();
            FileId = uid.hex;
                        
        stored_path = '/'.join([imgroot,suffix,FileId[0:3], FileId[3:6], FileId[6:9],FileId[9:]]);
        dirname = "/".join([imgroot,suffix,FileId[0:3], FileId[3:6], FileId[6:9]]);
            
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        
        realpath = stored_path
        if suffix != 'none':
            realpath = stored_path+'.'+suffix
        
        if os.path.exists(realpath):
            destination = open(realpath, 'ab')
            shutil.copyfileobj(theFile.file, destination)
            destination.close()
        else:    
            os.link(theFile.file.name, realpath)
        try:
            cherrypy.response.headers['location'] = formFields['cb'].value
        except:
            pass
        if 'Content-Range' in cherrypy.request.headers:
            print cherrypy.request.headers['Content-Range']
            cherrypy.response.headers['Range'] = cherrypy.request.headers['Content-Range'].split('/')[0].split(' ')[1]
        print cherrypy.response.headers
        dict = {"files":[{"name": FileId+'.'+suffix,"size":int(cherrypy.request.headers['Content-Range'].split('/')[0].split('-')[1]),"type":"image/"+suffix,"url":"","thumbnail_url":""}]}
        return json.dumps(dict)

class upload(object):
    @cherrypy.expose
    def index(self):
        return "<div id='hi'>hello</div>"        
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
    #cherrypy.tree.mount(upload(), '/', None)
    return cherrypy.tree(environ, start_response)

server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8000), application)
server.start()