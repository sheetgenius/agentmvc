class Other; def any?; false; end; end
p Other.new.any?
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(" a,b ")
