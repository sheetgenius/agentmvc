require "json"
require "base64"
module ActiveSupport
  module SecurityUtils
    def self.secure_compare(a, b); a == b; end
  end
end
require "digest"


class TokenCodec
#<SPINEL_SOURCE>app/app/services/token_codec.rb:10
  def self.encode(payload, secret)
#<SPINEL_SOURCE>app/app/services/token_codec.rb:11
    header = encode_segment(JSON.generate({ alg: "HS256", typ: "JWT" }))
#<SPINEL_SOURCE>app/app/services/token_codec.rb:12
    body = encode_segment(JSON.generate(payload))
#<SPINEL_SOURCE>app/app/services/token_codec.rb:13
    input = "#{header}.#{body}"
#<SPINEL_SOURCE>app/app/services/token_codec.rb:14
    "#{input}.#{encode_segment(hmac(secret, input))}"
  end

#<SPINEL_SOURCE>app/app/services/token_codec.rb:17
  def self.decode(token, secret)
    begin
      parts = token.split(".", -1)
#<SPINEL_SOURCE>app/app/services/token_codec.rb:19
      if parts.length == 3 && parts.all? { |part| part.match?(/\A[A-Za-z0-9_-]+\z/) }
        nil
      else
        raise TokenCodec::DecodeError
      end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:20
      header = JSON.parse(Base64.urlsafe_decode64(parts[0]))
#<SPINEL_SOURCE>app/app/services/token_codec.rb:21
      if header.is_a?(Hash) && header["alg"] == "HS256"
        nil
      else
        raise TokenCodec::DecodeError
      end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:22
      input = "#{parts[0]}.#{parts[1]}"
#<SPINEL_SOURCE>app/app/services/token_codec.rb:23
      signature = encode_segment(hmac(secret, input))
#<SPINEL_SOURCE>app/app/services/token_codec.rb:24
      if ActiveSupport::SecurityUtils.secure_compare(signature, parts[2])
        nil
      else
        raise TokenCodec::DecodeError
      end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:25
      payload = JSON.parse(Base64.urlsafe_decode64(parts[1]))
#<SPINEL_SOURCE>app/app/services/token_codec.rb:26
      if payload.is_a?(Hash)
        nil
      else
        raise TokenCodec::DecodeError
      end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:27
      now = Time.now.to_i
#<SPINEL_SOURCE>app/app/services/token_codec.rb:28
      raise TokenCodec::DecodeError if payload.key?("exp") && payload["exp"].to_i <= now
#<SPINEL_SOURCE>app/app/services/token_codec.rb:29
      raise TokenCodec::DecodeError if payload.key?("nbf") && payload["nbf"].to_i > now
#<SPINEL_SOURCE>app/app/services/token_codec.rb:30
      payload
    rescue ArgumentError, JSON::ParserError, TypeError, NoMethodError
      raise TokenCodec::DecodeError
    end
  end

#<SPINEL_SOURCE>app/app/services/token_codec.rb:35
  def self.encode_segment(bytes)
#<SPINEL_SOURCE>app/app/services/token_codec.rb:36
    Base64.strict_encode64(bytes).tr("+/", "-_").delete("=")
  end

#<SPINEL_SOURCE>app/app/services/token_codec.rb:39
  def self.hmac(secret, input)
#<SPINEL_SOURCE>app/app/services/token_codec.rb:40
    key = if secret.bytesize > 64
      Digest::SHA256.digest(secret)
    else
      secret
    end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:41
    inner = +""
#<SPINEL_SOURCE>app/app/services/token_codec.rb:42
    outer = +""
#<SPINEL_SOURCE>app/app/services/token_codec.rb:43
    position = 0
#<SPINEL_SOURCE>app/app/services/token_codec.rb:44
    while position < 64
      byte = if position < key.bytesize
        key.getbyte(position)
      else
        0
      end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:46
      inner << (byte ^ 54).chr
#<SPINEL_SOURCE>app/app/services/token_codec.rb:47
      outer << (byte ^ 92).chr
#<SPINEL_SOURCE>app/app/services/token_codec.rb:48
      position += 1
    end
#<SPINEL_SOURCE>app/app/services/token_codec.rb:50
    Digest::SHA256.digest(outer + Digest::SHA256.digest(inner + input.b))
  end
  class DecodeError < StandardError
  end
end

class Header
  attr_reader :value
  def initialize(value); @value = value; end
end
class Config
  attr_reader :key
  def initialize; @key = ENV.fetch("SECRET_KEY_BASE", "secret"); end
end
def read(header, config)
  text = header.value.to_s
  TokenCodec.decode(text.delete_prefix("Token "), config.key)
end
config = Config.new
value = TokenCodec.encode({sub: 1}, config.key)
p read(Header.new("Token " + value), config)
