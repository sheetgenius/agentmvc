class Token
  HEADER = Base64.urlsafe_encode64({ alg: "HS256", typ: "JWT" }.to_json, padding: false)

  def self.issue(user)
    payload = Base64.urlsafe_encode64({ sub: user.id, exp: 30.days.from_now.to_i }.to_json, padding: false)
    "#{HEADER}.#{payload}.#{signature("#{HEADER}.#{payload}")}"
  end

  def self.read(value)
    header, payload, signature_value = value.to_s.split(".", 3)
    return unless header && payload && signature_value && header == HEADER
    return unless ActiveSupport::SecurityUtils.secure_compare(signature_value, signature("#{header}.#{payload}"))
    data = JSON.parse(Base64.urlsafe_decode64(payload))
    User.find_by(id: data["sub"]) if data["exp"].is_a?(Integer) && data["exp"] > Time.current.to_i
  rescue ArgumentError, JSON::ParserError
    nil
  end

  def self.signature(data)
    Base64.urlsafe_encode64(OpenSSL::HMAC.digest("SHA256", Rails.application.secret_key_base, data), padding: false)
  end
end
