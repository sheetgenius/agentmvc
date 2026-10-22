class Filename
  def initialize(name); @name = name; end
  def append(s); @name << s; self; end
  def to_s = @name
end
class Maker
  def new = :fresh
end
def build(klass, name) = klass.new(name.to_s)
p Maker.new.new
p build(Filename, :b).append("c").to_s
p build(String, :a)
