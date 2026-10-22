require "digest"
require "openssl"
Room = Struct.new(:lock, :members)
class Filename
  def initialize(name); @name = name; end
  def append(s); @name << s; self; end
  def to_s; @name; end
end
class Holder
  def initialize(params); @params = params; end
  def param(name); @params[name.to_s]; end
end
p Room[1, 2]
p Filename.new(+"x").append("y").to_s
p Digest::SHA256.new.hexdigest[0, 8]
p OpenSSL::Digest.new("SHA256").new.hexdigest[0, 8]
p Holder.new({"a" => 1}).param(:a)
p Holder.new(Room).param(:b)
