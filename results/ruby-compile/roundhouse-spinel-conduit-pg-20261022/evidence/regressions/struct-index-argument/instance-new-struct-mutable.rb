Room = Struct.new(:lock, :members)
class Filename
  def initialize(name); @name = name; end
  def append(s); @name << s; self; end
  def to_s = @name
end
class Maker
  def new = :fresh
end
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p Maker.new.new
p Filename.new(+"x").append("y").to_s
p Holder.new({"a" => 1}).param(:a)
p Holder.new(Room).param(:b)
