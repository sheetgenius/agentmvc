pr = proc { |a| puts a }
pr.call(["99", 1][0])
pr.call(["1_000", 1][0])
pr.call(["abc", 1][0])
