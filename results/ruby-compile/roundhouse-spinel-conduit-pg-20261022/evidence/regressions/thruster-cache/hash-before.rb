p [{"a" => "b"}].any? { |x| x["a"] == "b" }
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(" a,b ")
