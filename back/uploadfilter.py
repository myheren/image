import cgi
import cherrypy
import tempfile
import time

from filter import BaseFilter

class Upload_MaxConcError(Exception):
    pass
class Upload_TimeoutError(Exception):
    pass
class Upload_MaxSizeError(Exception):
    pass
class Upload_UnauthorizedError(Exception):
    pass
class Upload_UpSpeedError(Exception):
    pass

current_uploads = 0
cherrypy.file_transfers = dict()

class ProgressFile(object):
    def __init__(self, buf, *args, **kwargs):
        self.file_object = tempfile.TemporaryFile(
                *args, **kwargs)
        self.transferred = 0
        self.buf = buf
        self.pre_sized = float(cherrypy.request.headers['Content-length'])
        self.speed = 1
        self.remaining = 0
        self.eta = 0
        self._start = time.time()

    def write(self, data):
        now = time.time()
        self.transferred += len(data)
        upload_timeout = getattr(cherrypy.thread_data, 'upload_timeout', False)
        if upload_timeout:
            if (now - self._start) > upload_timeout:
                raise Upload_TimeoutError

        upload_maxsize = getattr(cherrypy.thread_data, 'upload_maxsize', False)
        if upload_maxsize:
            if self.transferred > upload_maxsize:
                raise Upload_MaxSizeError

        self.speed = self.transferred / (now - self._start)

        upload_minspeed = getattr(cherrypy.thread_data, 'upload_minspeed', False)
        if upload_minspeed:
            if self.transferred > (5 * self.buf): # gives us a reasonable wait period.
                if self.speed < upload_minspeed:
                    raise Upload_UpSpeedError

        self.remaining = self.pre_sized - self.transferred

        if self.speed == 0: self.eta = 9999999
        else: self.eta = self.remaining / self.speed

        return self.file_object.write(data)

    def seek(self, pos):
        self.post_sized = self.transferred
        self.transferred = True
        return self.file_object.seek(pos)

    def read(self, size):
        return self.file_object.read(size)

class FieldStorage(cgi.FieldStorage):
    ''' We want control over our timing and download status,
        so we've got to override the original. This will work
        transparently without interfering with the user, but
        might warrant addition to _cpcgifs '''

    def __del__(self, *args, **kwargs):
        return
        try:
            dcopy = cherrypy.file_transfers[cherrypy.request.remote_addr].copy()
            for key, val in dcopy.iteritems():
                if val.transferred == True:
                    del cherrypy.file_transfers[cherrypy.request.remote_addr][key]
            del dcopy
            if len(cherrypy.file_transfers[cherrypy.request.remote_addr]) == 0:
                del cherrypy.file_transfers[cherrypy.request.remote_addr]

        except KeyError:
            pass

    def make_file(self, binary=None):
        fo = ProgressFile(self.bufsize)
        if cherrypy.file_transfers.has_key(cherrypy.request.remote_addr):
            cherrypy.file_transfers[cherrypy.request.remote_addr]\
                    [self.filename] = fo
        else:
            cherrypy.file_transfers[cherrypy.request.remote_addr]\
                    = {self.filename:fo}

        return fo

class UploadFilter(BaseFilter):

    #def on_start_resource(self):
    #    cherrypy.request.rfile = cherrypy.request.rfile.rfile

    def before_request_body(self):
        global current_uploads

        if not cherrypy.config.get('upload_filter.on', False):
            return

        if cherrypy.request.headers.get('Content-Type', '').split(';')[0] ==\
            'multipart/form-data':

            upload_explicit = cherrypy.config.get('upload_filter.explicit', False)
            upload_declared = cherrypy.config.get('upload_filter.declared', False)
            upload_limit = cherrypy.config.get('upload_filter.max_concurrent', False)
            upload_timeout = cherrypy.config.get('upload_filter.timeout', False)
            upload_maxsize = cherrypy.config.get('upload_filter.max_size', False)
            upload_minspeed = cherrypy.config.get('upload_filter.min_upspeed', False)


            cherrypy.thread_data.upload_minspeed = upload_minspeed

            if upload_explicit and not upload_declared:
                raise Upload_UnauthorizedError

            if upload_limit:
                if current_uploads > upload_limit:
                    raise Upload_MaxConcError
                current_uploads += 1

            if upload_timeout:
                cherrypy.thread_data.upload_timeout = upload_timeout

            if upload_maxsize:
                upload_maxsize *= 1024
                cherrypy.thread_data.upload_maxsize = upload_maxsize
                size = float(cherrypy.request.headers['Content-length'])
                if size > upload_maxsize:
                    raise Upload_MaxSizeError
                # the following line is commented out to accomodate a
                # change in CherryPy >= 2.3.0
                #cherrypy.request.rfile = cherrypy.request.rfile.rfile

    def on_end_resource(self):
        global current_uploads

        if not cherrypy.config.get('upload_filter.on', False):
            return

        if cherrypy.request.headers.get('Content-Type', '').split(';')[0] ==\
            'multipart/form-data':

            upload_explicit = cherrypy.config.get('upload_filter.explicit',
                    False)
            upload_declared = cherrypy.config.get('upload_filter.declared',
                    False)
            upload_limit = cherrypy.config.get('upload_filter.max_concurrent',
                    False)
            upload_timeout = cherrypy.config.get('upload_filter.timeout',
                    False)
            upload_maxsize = cherrypy.config.get('upload_filter.max_size',
                    False)

            if upload_explicit and not upload_declared:
                return

            if upload_limit:
                current_uploads -= 1

            if upload_timeout:
                del cherrypy.thread_data.upload_timeout

            if upload_maxsize:
                del cherrypy.thread_data.upload_maxsize