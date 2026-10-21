class Probe
#<SPINEL_SOURCE>case/lib/probe.rb:3
  def self.pick(flag)
#<SPINEL_SOURCE>case/lib/probe.rb:4
    return :full if flag
#<SPINEL_SOURCE>case/lib/probe.rb:5
    JSON.parse("{\"n\":1}")
  end

#<SPINEL_SOURCE>case/lib/probe.rb:7
  def self.consume(value)
    p value
  end

#<SPINEL_SOURCE>case/lib/probe.rb:8
  def self.run
    consume(pick(false))
  end
end
