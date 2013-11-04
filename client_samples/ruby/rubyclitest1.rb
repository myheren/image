require 'uri'
require 'net/http'
uri = URI.parse("http://localhost/files/")
filepath = "files/a.png"
http = Net::HTTP.new(uri.host, uri.port)
request = Net::HTTP::Post.new(uri.request_uri)
request.body_stream=File.open(filepath)
request["Content-Type"] = "multipart/form-data"
request.add_field('Content-Length', File.size(filepath))
response=http.request(request)
puts "Request Headers: #{request.to_hash.inspect}"
#puts "Sending POST #{uri.request_uri} to #{uri.host}:#{uri.port}"
puts "Response #{response.code} #{response.message}"
puts "#{response.body}"
puts "Headers: #{response.to_hash.inspect}"
