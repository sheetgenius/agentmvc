def matches?(value, etag)
  return false if etag.length == 0 || value.length == 0
  value.split(",").any? { |candidate| candidate.strip == etag }
end
Thread.new { p matches?(" a,b ", +"a") }.join
