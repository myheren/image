import MultipartPostHandler, urllib2, cookielib
import uuid

cookies = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
uid = uuid.uuid4();
params = { "FileId" : uid.hex,
           "theFile" : open("files/a.png", "rb") }
print opener.open("http://localhost/files/", params).read()