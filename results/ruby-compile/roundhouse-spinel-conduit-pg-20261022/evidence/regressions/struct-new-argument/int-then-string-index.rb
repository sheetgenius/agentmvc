Room = Struct.new(:lock, :members)
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p Room[1, 2]
p Holder.new(Room).param(:b)
