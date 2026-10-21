class Box
  attr_reader :data
  def initialize; @data = {"seed" => ""}; end
end
b = Box.new
def put(b, v); b.data["x"] = v; end
s = "a"
put(b, s)
s << "b"
p b.data["x"]
