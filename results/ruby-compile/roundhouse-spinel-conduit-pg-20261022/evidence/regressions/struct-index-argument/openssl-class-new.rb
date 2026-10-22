require "openssl"
def make(klass, name) = klass.new(name.to_s)
p make(OpenSSL::Digest, :SHA256).hexdigest[0, 8]
p make(String, :x)
