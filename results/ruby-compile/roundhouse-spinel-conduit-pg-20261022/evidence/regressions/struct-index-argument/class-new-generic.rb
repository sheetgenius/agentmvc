require "digest"
Room = Struct.new(:lock, :members)
class Filename
  def initialize(name); @name = name; end
  def append(s); @name << s; self; end
  def to_s; @name; end
end
def build(klass, name) = klass.new(name.to_s)
p Room[1, 2]
p Filename.new(+"x").append("y").to_s
p Digest::SHA256.new.hexdigest[0, 8]
p build(Room, :a)
p build(Filename, :b).append("c").to_s
