Room = Struct.new(:lock, :members)
class Maker
  def new = :fresh
  def [](key) = key
end
def fetch(x, name) = x[name.to_s]
p fetch(Room, :a)
p fetch(Maker.new, :b)
p fetch({"c" => 3}, :c)
