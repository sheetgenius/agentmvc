require "json"

class User
  def initialize(id); @id = id; end
  def id; @id; end
end

# A second class answering #merge makes `permitted(...).merge(...)` a
# boxed-receiver (poly) dispatch, as in the generated Rails controller.
class Bag
  def merge(other); self; end
end

def permitted(input, names)
  return Bag.new if names.empty?
  h = {}
  names.each { |k| h[k] = input[k.to_s] if input.key?(k.to_s) }
  h
end

def slug_for(title)
  # allocation-heavy, like parameterize + SecureRandom
  s = ""
  20.times { |k| s = s + title.downcase + k.to_s }
  title.downcase + "-" + s.size.to_s
end

class Art
  def initialize(attrs = {})
    @title = (attrs[:title] || "").to_s
    @published_at = attrs[:published_at]
    @tag_list = attrs[:tag_list] || []
    @slug = (attrs[:slug] || "").to_s
  end
  def title; @title; end
  def published_at; @published_at; end
  def tag_list; @tag_list; end
  def slug; @slug; end
end

def encode_array(values)
  encoded = values.map do |v|
    out = '"'
    v.each_char { |c| out += c }
    out + '"'
  end
  "{" + encoded.join(",") + "}"
end

iters = (ARGV[0] || "300").to_i
user = User.new(7)
bad = 0
iters.times do |i|
  body = "{\"article\":{\"title\":\"T#{i}\",\"tagList\":[\"tag#{i}a\",\"tag#{i}b\",\"tag#{i}a\"]}}"
  input = JSON.parse(body)["article"]
  tags = input["tagList"]
  status = i >= 0 ? "published" : "draft"
  a = Art.new(permitted(input, %i[title description body]).merge(author: user, status: status, published_at: (Time.at(1700000000 + i) if status == "published"), tag_list: tags.uniq, slug: slug_for(input["title"])))
  input = nil
  tags = nil
  enc = encode_array(a.tag_list)
  if enc != "{\"tag#{i}a\",\"tag#{i}b\"}"
    bad += 1
    puts "BAD tags #{i}: #{enc.inspect}" if bad < 5
  end
  if !a.published_at.is_a?(Time) || a.published_at.to_i != 1700000000 + i
    bad += 1
    puts "BAD time #{i}: #{a.published_at.inspect}" if bad < 5
  end
end
puts "done bad=#{bad}"
