Room = Struct.new(:lock, :members)
p Room[1, 2]
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p Holder.new({"a" => 1}).param(:a)
p Holder.new(["x"]).param(:b) rescue p $!.class
