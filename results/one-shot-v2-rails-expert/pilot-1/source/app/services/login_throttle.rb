class LoginThrottle
  @lock = Mutex.new
  @failures = Hash.new { |hash, key| hash[key] = [] }
  def self.fail!(email, ip)
    @lock.synchronize do
      key = [ email.downcase, ip ]
      now = Time.now.to_f
      @failures[key].reject! { |time| time < now - 60 }
      @failures[key] << now
      raise ApplicationController::Failure.new(429, :credentials, "rate limited") if @failures[key].length > 20
    end
  end
end
