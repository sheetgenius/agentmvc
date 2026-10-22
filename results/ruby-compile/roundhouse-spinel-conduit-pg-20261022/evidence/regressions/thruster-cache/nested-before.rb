class Item
  attr_reader :value
  def initialize(value); @value = value; end
end
p [[Item.new(1)]].any? { |x| x[0].value == 1 }
def matches?(value)
  value.split(",").any? { |candidate| candidate.strip == "a" }
end
p matches?(" a,b ")
