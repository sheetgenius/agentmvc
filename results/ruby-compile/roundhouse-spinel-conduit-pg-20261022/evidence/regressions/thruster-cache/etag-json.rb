def matches?(value, etag)
  value.split(",").any? { |candidate| candidate.strip == etag }
end
require "json"
p matches?(" a,b ", JSON.parse('{"tag":"a"}')["tag"])
