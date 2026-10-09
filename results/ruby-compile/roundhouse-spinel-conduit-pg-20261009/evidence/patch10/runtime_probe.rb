require "json"
require "time"
root = ARGV.fetch(0)
require File.join(root, "action_controller/base")
require File.join(root, "action_controller/parameter_missing")
require File.join(root, "action_dispatch/request")
require File.join(root, "active_record/base")
require File.join(root, "active_support_ext")
module Rails
  def self.application; self; end
  def self.config_time_zone; "UTC"; end
end
checks = {
  "nosniff" => -> { ActionController::Base.new.headers["X-Content-Type-Options"] == "nosniff" },
  "response_set_header" => -> { c = ActionController::Base.new; c.set_header("X-Mode", "api"); c.headers["X-Mode"] == "api" },
  "integer_status" => -> { c = ActionController::Base.new; c.head(202); c.status == 202 },
  "bad_request_class" => -> { ActionController::BadRequest < StandardError },
  "parse_error_class" => -> { ActionDispatch::Http::Parameters::ParseError < StandardError },
  "case_insensitive_headers" => -> { r = ActionDispatch::Request.new; r.headers["X-Key"] = "yes"; r.headers["x-key"] == "yes" },
  "authorization" => -> { r = ActionDispatch::Request.new; r.env["HTTP_AUTHORIZATION"] = "Bearer token"; r.authorization == "Bearer token" },
  "validation_message_storage" => -> { r = ActiveRecord::Base.new; r.record_validation_message(:name, "reserved"); r.errors_messages == { name: ["reserved"] } },
  "validation_message_reset" => -> { r = ActiveRecord::Base.new; r.record_validation_message(:name, "reserved"); r.valid?; r.errors_messages.empty? },
  "json_encoder" => -> { ActionController::JsonRender.encode({ ok: true }) == '{"ok":true}' },
  "utc_presentation" => -> { ActiveSupport.present(Time.at(0)).iso8601 == "1970-01-01T00:00:00Z" }
}
result = checks.transform_values do |check|
  begin
    { "pass" => check.call }
  rescue StandardError => error
    { "pass" => false, "error" => error.class.name, "message" => error.message.lines.first.strip }
  end
end
puts JSON.pretty_generate(result)
