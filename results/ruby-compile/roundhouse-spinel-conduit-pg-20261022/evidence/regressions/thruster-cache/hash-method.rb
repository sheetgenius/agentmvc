def others(v); v.any? { |x| x["a"] == "b" }; end
p others([{"a" => "b"}])
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(" a,b ")
