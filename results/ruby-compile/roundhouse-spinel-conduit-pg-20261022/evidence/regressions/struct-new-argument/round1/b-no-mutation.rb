Room = Struct.new(:lock, :members)
class Filename
  def initialize(name); @name = name; end
  def to_s = @name
end
def build(klass, name) = klass.new(name.to_s)
p build(Room, :a)
p build(Filename, :b).to_s
