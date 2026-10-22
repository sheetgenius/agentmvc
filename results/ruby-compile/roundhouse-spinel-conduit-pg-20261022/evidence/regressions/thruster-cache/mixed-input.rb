def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
values = [" a,b ", nil]
p matches?(values[0])
