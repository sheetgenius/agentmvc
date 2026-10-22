Room = Struct.new(:lock, :members)
class Maker
  def new = :fresh
end
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p Maker.new.new
p Holder.new({"a" => 1}).param(:a)
p Holder.new(Room).param(:b)
