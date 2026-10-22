def matches?(value, etag)
  value.split(",").any? { |candidate| candidate.strip == etag }
end
p matches?(" a,b ", "a")
