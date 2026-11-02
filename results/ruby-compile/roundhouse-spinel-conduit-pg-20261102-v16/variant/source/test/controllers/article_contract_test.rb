require "test_helper"

class ArticleContractTest < ActionDispatch::IntegrationTest
  def user(name)
    User.create!(username: name, email: "#{name}@test.com", password: "password123")
  end

  def article(author)
    Article.create!(author: author, slug: Article.slug_for("Test"), title: "Test", description: "Description",
      body: "Before", status: "draft")
  end

  def authorization(user)
    token = JWT.encode({ sub: user.id, exp: 30.days.from_now.to_i }, Rails.application.secret_key_base, "HS256")
    { "Authorization" => "Token #{token}" }
  end

  test "author update rejects explicit null revision and accepts omission" do
    author = user("author")
    draft = article(author)
    put "/api/articles/#{draft.slug}", params: { article: { body: "Rejected", revision: nil } },
      headers: authorization(author), as: :json
    assert_response :unprocessable_entity
    assert_equal [ "is invalid" ], response.parsed_body.dig("errors", "revision")
    assert_equal [ "Before", 1 ], [ draft.reload.body, draft.revision ]

    put "/api/articles/#{draft.slug}", params: { article: { body: "Accepted" } },
      headers: authorization(author), as: :json
    assert_response :ok
    assert_equal [ "Accepted", 2 ], [ draft.reload.body, draft.revision ]
  end

  test "shared update rejects explicit null revision without mutation" do
    draft = article(user("shared_author"))
    share, key = ArticleShare.issue!(draft)
    put "/api/shares/#{share.id}/article",
      params: { article: { title: "Changed", body: "Rejected", revision: nil } },
      headers: { "X-Share-Key" => key }, as: :json
    assert_response :unprocessable_entity
    assert_equal [ "is invalid" ], response.parsed_body.dig("errors", "revision")
    assert_equal [ "Test", "Before", 1 ], [ draft.reload.title, draft.body, draft.revision ]
  end

  test "share changes notify the links they revoked" do
    author = user("link_author")
    draft = article(author)
    old, = ArticleShare.issue!(draft)
    notified = []
    test = self
    original = LiveRooms.method(:revoked)
    LiveRooms.define_singleton_method(:revoked, ->(ids) {
      notified << ids
      ids.each { |id| test.assert ArticleShare.find(id).revoked_at }
    })
    begin
      post "/api/articles/#{draft.slug}/share", headers: authorization(author)
      assert_response :created
      current_id = response.parsed_body.dig("share", "id")
      delete "/api/articles/#{draft.slug}/share", headers: authorization(author)
      assert_response :no_content
      assert_equal [ [ old.id ], [ current_id ] ], notified
    ensure
      LiveRooms.define_singleton_method(:revoked, original)
    end
  end

  test "comments list includes every comment by default" do
    author = user("commenter")
    published = article(author)
    published.publish!
    now = Time.current
    Comment.insert_all!(Array.new(101) { |index| { article_id: published.id, author_id: author.id,
      body: "Comment #{index}", created_at: now, updated_at: now } })

    get "/api/articles/#{published.slug}/comments"
    assert_response :ok
    assert_equal 101, response.parsed_body.fetch("comments").length
  end
end
