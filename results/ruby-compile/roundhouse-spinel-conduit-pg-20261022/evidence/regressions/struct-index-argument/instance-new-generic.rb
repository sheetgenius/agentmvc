class Maker
  def new = :fresh
end
def build(klass, name) = klass.new(name.to_s)
p Maker.new.new
p build(String, :a)
