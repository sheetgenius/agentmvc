require "json"
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(JSON.parse('{"s":" a,b "}')["s"])
