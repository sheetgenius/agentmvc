require "test_helper"

class ProductRulesTest < ActiveSupport::TestCase
  def user(name)
    User.create!(username: name, email: "#{name}@test.com", password: "password123")
  end

  def article(author, status = "draft")
    Article.create!(author: author, slug: Article.slug_for("Test"), title: "Test", description: "Description",
      body: "Before", status: status, published_at: (Time.current if status == "published"))
  end

  test "password policy applies to registration and update" do
    account = User.new(username: "short", email: "short@test.com", password: "seven77")
    assert_not account.valid?
    account.password = "a" * 64
    assert account.save!
    account.password = "short"
    assert_not account.valid?
    account.password = "bonjour1"
    assert account.save!
  end

  test "draft visibility and publication are consistent" do
    owner = user("owner")
    draft = article(owner)
    assert_equal 0, Article.published.count
    assert_equal draft, Article.visible_to(owner).first
    assert_empty Article.visible_to(user("reader"))
    draft.publish!
    assert_equal 2, draft.revision
    assert_equal 1, Article.published.count
    published_at = draft.published_at
    draft.publish!
    assert_equal 2, draft.revision
    assert_equal published_at, draft.published_at
  end

  test "owner and shared commits use one revision rule" do
    draft = article(user("writer"))
    share, key = ArticleShare.issue!(draft)
    shared = ->(a) { a.shared_json }
    ArticleCommit.call(draft, { "body" => "Owner" }, expected: 1, representation: shared)
    assert_equal 2, draft.revision
    assert_raises(ApplicationController::Failure) do
      ArticleCommit.call(draft, { "body" => "Stale" }, expected: 1, representation: shared, share: share, key: key)
    end
    ArticleCommit.call(draft, { "title" => "New", "body" => "Shared" }, expected: 2, representation: shared, share: share, key: key)
    assert_equal [ "Shared", 3 ], [ draft.body, draft.revision ]
    ArticleShare.issue!(draft)
    assert_raises(ApplicationController::Failure) do
      ArticleCommit.call(draft, { "body" => "Revoked" }, expected: 3, representation: shared, share: share, key: key)
    end
  end


  test "room admits one hundred authorized sockets and releases a slot" do
    Faye::WebSocket.ensure_reactor_running
    draft = article(user("room_owner"))
    share, = ArticleShare.issue!(draft)
    socket_class = Class.new do
      def send(_payload); end
      def close; end
    end
    sockets = Array.new(100) { socket_class.new }
    room = nil
    sockets.each { |socket| room = LiveRooms.join(share, socket) }
    assert_equal 100, room.members.length
    assert_equal :full, LiveRooms.join(share, socket_class.new)
    LiveRooms.leave(room, sockets.first)
    assert_instance_of LiveRooms::Room, LiveRooms.join(share, socket_class.new)
    assert_equal 100, room.members.length
    room.members.keys.each { |socket| LiveRooms.leave(room, socket) }
  end

  test "startup recovery requeues only pending exports" do
    owner = user("recoverer")
    pending = ArticleExport.create!(user: owner)
    finished = ArticleExport.create!(user: owner, status: "done", articles: [], completed_at: Time.current)
    queued = []
    original = ExportArticlesJob.method(:perform_later)
    begin
      ExportArticlesJob.define_singleton_method(:perform_later) { |id| queued << id }
      ArticleExport.recover_pending!
    ensure
      ExportArticlesJob.define_singleton_method(:perform_later, original)
    end
    assert_includes queued, pending.id
    assert_not_includes queued, finished.id
  end

  test "export job finishes once and preserves snapshot" do
    owner = user("exporter")
    draft = article(owner)
    export = ArticleExport.create!(user: owner)
    ExportArticlesJob.perform_now(export.id)
    assert_equal "done", export.reload.status
    assert_equal "Before", export.articles.first["body"]
    draft.update!(body: "After")
    ExportArticlesJob.perform_now(export.id)
    assert_equal "Before", export.reload.articles.first["body"]
  end
end
