def matches?(value, etag)
  return false if etag.length == 0 || value.length == 0
  value.split(",").any? { |candidate| candidate.strip == etag }
end
Mutex.new.synchronize { p matches?(" a,b ", +"a") }
