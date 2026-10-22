def matches?(value, etag)
  value.split(",").any? { |candidate| candidate.strip == etag }
end
tag = +"a"
p matches?(" a,b ", tag)
