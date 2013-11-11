import MultipartPostHandler, urllib2, cookielib
import uuid

cookies = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
#this is in practice you will do
#uid = uuid.uuid4();
#print uid.hex
#opener.addheaders = [('FileId', uid.hex)]

#this is for test

opener.addheaders = [('FileId', "testtesttesttesttesttest")]

params = {"theFile" : open("files/c.rmvb", "rb") }
print opener.open("http://localhost/files/", params).read()