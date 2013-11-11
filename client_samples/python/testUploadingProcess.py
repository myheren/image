import urllib2
import urllib

params = urllib.urlencode({"fid" : "testtesttesttesttesttest" })
request = urllib2.Request("http://localhost/uploadingStatus/", params)
print urllib2.urlopen(request).read()