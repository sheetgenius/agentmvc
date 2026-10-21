require "test_helper"

class CompileVariantContractTest < ActionDispatch::IntegrationTest
  test "registration tokens authenticate and duplicate accounts conflict" do
    input = { username: "variant_signup", email: "variant_signup@test.com", password: "password123" }
    post "/api/users", params: { user: input }, as: :json
    assert_response :created
    token = response.parsed_body.fetch("user").fetch("token")
    get "/api/user", headers: { "Authorization" => "Token #{token}" }
    assert_response :ok
    assert_equal input[:email], response.parsed_body.fetch("user").fetch("email")

    post "/api/users", params: { user: input.merge(email: "other_variant@test.com") }, as: :json
    assert_response :conflict
    assert_equal [ "has already been taken" ], response.parsed_body.dig("errors", "username")

    post "/api/users", params: { user: input.merge(username: "other_variant") }, as: :json
    assert_response :conflict
    assert_equal [ "has already been taken" ], response.parsed_body.dig("errors", "email")
  end

  test "invalid registration retains the attribute message response" do
    post "/api/users", params: { user: { username: "", email: "", password: "short" } }, as: :json
    assert_response :unprocessable_entity
    assert_includes response.parsed_body.fetch("errors").fetch("username"), "can't be blank"
    assert_includes response.parsed_body.fetch("errors").fetch("email"), "can't be blank"
  end

  test "tags remain distinct ordered and publication filtered in PostgreSQL" do
    owner = User.create!(username: "variant_tags", email: "variant_tags@test.com", password: "password123")
    [ [ "published", [ "zebra", "alpha", "alpha" ] ], [ "published", [ "beta", "alpha" ] ], [ "draft", [ "private_tag" ] ] ].each_with_index do |(status, tags), index|
      Article.create!(author: owner, title: "Tag #{index}", slug: "variant-tag-#{index}", description: "Description",
        body: "Body", status: status, tag_list: tags, published_at: status == "published" ? Time.current : nil)
    end
    get "/api/tags"
    assert_response :ok
    assert_equal [ "alpha", "beta", "zebra" ], response.parsed_body.fetch("tags")
  end
end
