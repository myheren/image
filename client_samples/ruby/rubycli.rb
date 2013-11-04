#do these things first
#sudo apt-get install curl libcurl3 libcurl3-gnutls libcurl4-openssl-dev
#gem install curb

require 'curb'

# post
c = Curl::Easy.new('http://localhost/files/')
c.multipart_form_post = true
c.http_post(Curl::PostField.file('theFile', 'files/a.png'))

# print response
print [c.response_code, c.body_str]
