require "base64"
require "digest"
require "json"

# Roundhouse cannot compile the JWT gem; this implements the app's HS256 paths.
class TokenCodec
  class DecodeError < StandardError
  end

  def self.encode(payload, secret)
    header = encode_segment(JSON.generate({ alg: "HS256", typ: "JWT" }))
    body = encode_segment(JSON.generate(payload))
    input = "#{header}.#{body}"
    "#{input}.#{encode_segment(hmac(secret, input))}"
  end

  def self.decode(token, secret)
    parts = token.split(".", -1)
    raise DecodeError unless parts.length == 3 && parts.all? { |part| part.match?(/\A[A-Za-z0-9_-]+\z/) }
    header = JSON.parse(Base64.urlsafe_decode64(parts[0]))
    raise DecodeError unless header.is_a?(Hash) && header["alg"] == "HS256"
    input = "#{parts[0]}.#{parts[1]}"
    signature = encode_segment(hmac(secret, input))
    raise DecodeError unless ActiveSupport::SecurityUtils.secure_compare(signature, parts[2])
    payload = JSON.parse(Base64.urlsafe_decode64(parts[1]))
    raise DecodeError unless payload.is_a?(Hash)
    now = Time.now.to_i
    raise DecodeError if payload.key?("exp") && payload["exp"].to_i <= now
    raise DecodeError if payload.key?("nbf") && payload["nbf"].to_i > now
    payload
  rescue ArgumentError, JSON::ParserError, TypeError, NoMethodError
    raise DecodeError
  end

  def self.encode_segment(bytes)
    Base64.strict_encode64(bytes).tr("+/", "-_").delete("=")
  end

  def self.hmac(secret, input)
    key = secret.bytesize > 64 ? Digest::SHA256.digest(secret) : secret
    inner = +""
    outer = +""
    position = 0
    while position < 64
      byte = position < key.bytesize ? key.getbyte(position) : 0
      inner << (byte ^ 0x36).chr
      outer << (byte ^ 0x5c).chr
      position += 1
    end
    Digest::SHA256.digest(outer + Digest::SHA256.digest(inner + input.b))
  end
end
