#do these things first
#sudo apt-get install curl libcurl3 libcurl3-gnutls libcurl4-openssl-dev
#gem install curb

require 'curb'
require "securerandom"

# post
c = Curl::Easy.new('http://localhost/files/')
c.multipart_form_post = true
c.headers["FileId"] = SecureRandom.hex
print c.headers["FileId"]
c.http_post(Curl::PostField.file('theFile', 'files/c.rmvb'))

# print response
print c.body_str
