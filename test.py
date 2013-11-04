from cherrypy import wsgiserver
from upload import application
server = wsgiserver.CherryPyWSGIServer(('localhost', 8000), application)
try:
    server.start()
except KeyboardInterrupt:
    server.stop()