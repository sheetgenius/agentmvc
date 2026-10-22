Room = Struct.new(:lock, :members)
def build(klass, name) = klass.new(name.to_s)
p Room[1, 2]
p build(Room, :a)
