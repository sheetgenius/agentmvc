require "json"
Room = Struct.new(:lock, :members)
p Room[1, 2]
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p Holder.new(JSON.parse('{"a":1}')).param(:a)
