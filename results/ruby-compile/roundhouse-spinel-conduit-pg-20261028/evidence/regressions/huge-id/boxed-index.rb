Room = Struct.new(:lock, :state)
class Holder
  def initialize(value); @params = value; end
  def param(name); @params[name.to_s]; end
end
def take(attrs); puts attrs[:id].to_s; end
take({id: Holder.new({"id" => "9" * 100}).param(:id), user_id: 1})
p Room.new("a", "b").lock
