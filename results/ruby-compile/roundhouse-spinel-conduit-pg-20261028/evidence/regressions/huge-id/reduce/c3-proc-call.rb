pr = proc { |a| puts a }
["9" * 100, 1].each { |x| pr.call(x) }
