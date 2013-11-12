#do these things first
#sudo apt-get install curl libcurl3 libcurl3-gnutls libcurl4-openssl-dev
#gem install curb

require 'curb'
require "securerandom"

# post
c = Curl::Easy.new('http://localhost/files/')
c.multipart_form_post = true
c.headers["FileId"] = "eb4d164d17ca0174c3e081511da0e6c6.png"#SecureRandom.hex+".png"
print c.headers["FileId"]
c.http_post(Curl::PostField.file('theFile', 'files/test.png'),Curl::PostField.content('mystr', 'haha'))

# print response
print c.body_str
