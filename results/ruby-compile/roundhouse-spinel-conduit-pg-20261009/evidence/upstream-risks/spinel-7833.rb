class Rec
  def []=(name, value)
  end
end

def store(params, name)
  params[name] = store(params[name], name) if name == "x"
  params[name] = +""
end

h = {}
store(h, "a")
p h
