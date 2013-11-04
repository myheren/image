require 'uri'
require 'net/http'
require 'net/http/post/multipart'
url = URI.parse('http://localhost/files/')
File.open("files/a.png") do |file|
  req = Net::HTTP::Post::Multipart.new url.path,
    "theFile" => UploadIO.new(file, "multipart/form-data", "a.png"),
    "filename" => "a.png"
  res = Net::HTTP.start(url.host, url.port) do |http|
    http.request(req)
  end
  print res.body
end
