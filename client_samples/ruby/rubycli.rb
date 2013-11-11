#do these things first
#sudo apt-get install curl libcurl3 libcurl3-gnutls libcurl4-openssl-dev
#gem install curb

require 'curb'
require "securerandom"

# post
c = Curl::Easy.new('http://localhost/files/')
c.multipart_form_post = true
c.http_post(Curl::PostField.file('theFile', 'files/a.png'),Curl::PostField.content('FileId', SecureRandom.hex))

# print response
print c.body_str
