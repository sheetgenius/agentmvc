require "json"
class Probe
  def self.pick(flag)
    return :full if flag
    JSON.parse('{"n":1}')
  end
  def self.consume(value); p value; end
  def self.run; consume(pick(false)); end
end
