Room = Struct.new(:lock, :members)
class Maker
  def new = :fresh
end
def build(x, name) = x.new(name.to_s)
p build(Room, :a)
begin
  p build(Maker.new, :b)
rescue ArgumentError => e
  p e.class
end
