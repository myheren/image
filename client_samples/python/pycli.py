import MultipartPostHandler, urllib2, cookielib

cookies = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
params = { "filename" : "a.png",
           "theFile" : open("files/a.png", "rb") }
print opener.open("http://localhost/files/", params).read()