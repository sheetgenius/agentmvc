class LoginThrottle
  @lock = Mutex.new
  @failures = Hash.new { |hash, key| hash[key] = [] }
  def self.fail!(email, ip)
    # Spinel loses custom exception attributes raised across Mutex#synchronize.
    limited = @lock.synchronize do
      key = [ email.downcase, ip ]
      now = Time.now.to_f
      # Spinel cannot dispatch reject! on the boxed Array from the default-block Hash.
      @failures[key] = @failures[key].select { |time| time >= now - 60 }
      @failures[key] << now
      @failures[key].length > 20
    end
    raise ApplicationController::Failure.new(429, :credentials, "rate limited") if limited
  end
end
