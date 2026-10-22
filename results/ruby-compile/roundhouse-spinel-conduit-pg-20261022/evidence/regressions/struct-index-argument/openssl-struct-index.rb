require "openssl"
Room = Struct.new(:lock, :members)
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p OpenSSL::Digest.new("SHA256").new.hexdigest[0, 8]
p Holder.new({"a" => 1}).param(:a)
p Holder.new(Room).param(:b)
