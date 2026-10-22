Room = Struct.new(:lock, :members)
def build(klass, name) = klass.new(name.to_s)
p build(Room, :a)
p build(String, :b)
