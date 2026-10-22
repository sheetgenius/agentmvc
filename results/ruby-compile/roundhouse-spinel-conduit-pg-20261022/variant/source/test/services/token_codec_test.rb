require "test_helper"
require "openssl"

class TokenCodecTest < ActiveSupport::TestCase
  test "HMAC matches OpenSSL across short long and binary keys" do
    [ "", "test-key", "k" * 64, "k" * 65, "k" * 200, "nul\0key", "\xFF\x80\0".b, "ключ" ].each do |key|
      [ "", "payload", "\0binary\xFF".b, "café" ].each do |input|
        assert_equal OpenSSL::HMAC.digest("SHA256", key, input), TokenCodec.hmac(key, input)
      end
    end
  end

  test "issued tokens interoperate in both directions with JWT" do
    payload = { sub: 42, exp: Time.now.to_i + 3600 }
    key = "interop-test-key"
    encoded = TokenCodec.encode(payload, key)
    assert_equal payload.transform_keys(&:to_s), JWT.decode(encoded, key, true, algorithm: "HS256").first
    assert_equal payload.transform_keys(&:to_s), TokenCodec.decode(JWT.encode(payload, key, "HS256"), key)
  end

  test "expiration not-before signatures and algorithms are verified" do
    key = "claims-test-key"
    [ { exp: Time.now.to_i - 1 }, { exp: Time.now.to_i }, { nbf: Time.now.to_i + 3600 } ].each do |payload|
      assert_raises(TokenCodec::DecodeError) { TokenCodec.decode(JWT.encode(payload, key, "HS256"), key) }
    end
    assert_raises(TokenCodec::DecodeError) { TokenCodec.decode(JWT.encode({ sub: 42 }, key, "HS256"), "wrong-key") }
    assert_raises(TokenCodec::DecodeError) { TokenCodec.decode(JWT.encode({ sub: 42 }, key, "HS384"), key) }
    assert_raises(TokenCodec::DecodeError) { TokenCodec.decode(JWT.encode({ sub: 42 }, nil, "none"), key) }
  end

  test "malformed token segments and non-object claims are rejected" do
    [ "", "a.b", "a.b.c.d", "a.b.", "!.b.c", "e30.e30.c" ].each do |token|
      assert_raises(TokenCodec::DecodeError) { TokenCodec.decode(token, "malformed-test-key") }
    end
    token = TokenCodec.encode([ 42 ], "malformed-test-key")
    assert_raises(TokenCodec::DecodeError) { TokenCodec.decode(token, "malformed-test-key") }
  end
end
