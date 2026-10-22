def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
def pick(flag); return 1 if flag; " a,b "; end
p matches?(pick(false))
