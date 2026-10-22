require "digest"
class Filename
  def initialize(name); @name = name; end
  def append(s); @name << s; self; end
  def to_s = @name
end
class Maker
  def new = :fresh
end
def build(x, name) = x.new(name.to_s)
p build(Filename, :a).append("b").to_s
begin
  p build(Maker.new, :b)
rescue ArgumentError => e
  p e.class
end
begin
  p build(Digest::SHA256, :c)
rescue ArgumentError => e
  p e.class
end
