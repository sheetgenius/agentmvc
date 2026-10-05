require "test_helper"

class HealthTest < ActionDispatch::IntegrationTest
  test "health route" do
    get "/health"
    assert_response :success
    assert_equal({ "status" => "ok" }, response.parsed_body)
  end
end
