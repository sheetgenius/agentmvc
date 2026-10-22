require "json"
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
def pick(flag); return :other if flag; JSON.parse('{"s":" a,b "}')["s"]; end
p matches?(pick(false))
