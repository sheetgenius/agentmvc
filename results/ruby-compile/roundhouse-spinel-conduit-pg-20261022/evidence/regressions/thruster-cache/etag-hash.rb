def matches?(value, etag)
  value.split(",").any? { |candidate| candidate.strip == etag }
end
h = {"tag" => +"a"}
p matches?(" a,b ", h["tag"])
