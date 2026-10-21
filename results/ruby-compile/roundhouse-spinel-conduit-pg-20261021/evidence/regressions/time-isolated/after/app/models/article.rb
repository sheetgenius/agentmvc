require "securerandom"
require_relative "application_record"
require_relative "../../runtime/inflector"

class Article < ApplicationRecord
#<SPINEL_SOURCE>app/app/models/article.rb:1
  def id
    @id
  end

  def id=(value)
    @id = value
  end

  def author_id
    @author_id
  end

  def author_id=(value)
    @author_id = value
    @author_loaded = false
  end

  def body
    @body
  end

  def body=(value)
    @body = value
  end

  def created_at
    ActiveSupport.present_db(@__t_created_at ||= ActiveSupport.parse_db_time(@created_at_raw))
  end

  def created_at_raw
    @created_at_raw
  end

  def created_at=(value)
    self.created_at_raw = ActiveSupport.format_db_time(value)
  end

  def created_at_raw=(value)
    @__t_created_at = nil
    @created_at_raw = value
  end

  def description
    @description
  end

  def description=(value)
    @description = value
  end

  def published_at
    ActiveSupport.present_db(@__t_published_at ||= ActiveSupport.parse_db_time(@published_at_raw))
  end

  def published_at_raw
    @published_at_raw
  end

  def published_at=(value)
    self.published_at_raw = ActiveSupport.format_db_time(value)
  end

  def published_at_raw=(value)
    @__t_published_at = nil
    @published_at_raw = value
  end

  def revision
    @revision
  end

  def revision=(value)
    @revision = value
  end

  def slug
    @slug
  end

  def slug=(value)
    @slug = value
  end

  def status
    @status
  end

  def status=(value)
    @status = value
  end

  def tag_list
    @tag_list
  end

  def tag_list=(value)
    @tag_list = value
  end

  def title
    @title
  end

  def title=(value)
    @title = value
  end

  def updated_at
    ActiveSupport.present_db(@__t_updated_at ||= ActiveSupport.parse_db_time(@updated_at_raw))
  end

  def updated_at_raw
    @updated_at_raw
  end

  def updated_at=(value)
    self.updated_at_raw = ActiveSupport.format_db_time(value)
  end

  def updated_at_raw=(value)
    @__t_updated_at = nil
    @updated_at_raw = value
  end

  def self.table_name
    "articles"
  end

  def self._table_sql
    "\"articles\""
  end

  def self.schema_columns
    [:id, :author_id, :body, :created_at, :description, :published_at, :revision, :slug, :status, :tag_list, :title, :updated_at]
  end

  def self.schema_time_columns
    [:created_at, :published_at, :updated_at]
  end

  def self.schema_date_columns
    []
  end

  def self.schema_boolean_columns
    []
  end

  def self.schema_decimal_columns
    []
  end

  def self.schema_integer_limits
    { "article_exports.id" => 8, "article_exports.user_id" => 8, "article_shares.article_id" => 8, "articles.id" => 8, "id" => 8, "articles.author_id" => 8, "author_id" => 8, "articles.revision" => 4, "revision" => 4, "comments.id" => 8, "comments.article_id" => 8, "comments.author_id" => 8, "favorites.article_id" => 8, "favorites.user_id" => 8, "follows.followed_id" => 8, "follows.follower_id" => 8, "good_job_batches.callback_priority" => 4, "good_job_executions.error_event" => 4, "good_job_processes.lock_type" => 4, "good_jobs.error_event" => 4, "good_jobs.executions_count" => 4, "good_jobs.lock_type" => 4, "good_jobs.priority" => 4, "users.id" => 8 }
  end

  def self.instantiate(row)
    instance = Article.from_row(ArticleRow.from_raw(row))
    instance.mark_persisted!
    instance._note_projection(row)
    instance
  end

  def self.from_row(row)
    instance = Article.new
    instance.id = row.id
    instance.author_id = row.author_id
    instance.body = row.body
    instance.created_at_raw = row.created_at
    instance.description = row.description
    instance.published_at_raw = row.published_at&.to_s
    instance.revision = row.revision
    instance.slug = row.slug
    instance.status = row.status
    instance.tag_list = row.tag_list
    instance.title = row.title
    instance.updated_at_raw = row.updated_at
    instance._note_hydrated
    instance
  end

  def self.from_stmt(stmt)
    instance = Article.new
    instance.id = Db.column_int(stmt, 0)
    instance.author_id = Db.column_int(stmt, 1)
    instance.body = Db.column_text(stmt, 2)
    instance.created_at_raw = Db.column_text(stmt, 3)
    instance.description = Db.column_text(stmt, 4)
    instance.published_at_raw = Db.column_text_opt(stmt, 5)
    instance.revision = Db.column_int(stmt, 6)
    instance.slug = Db.column_text(stmt, 7)
    instance.status = Db.column_text(stmt, 8)
    instance.tag_list = Db.column_array(stmt, 9)
    instance.title = Db.column_text(stmt, 10)
    instance.updated_at_raw = Db.column_text(stmt, 11)
    instance.mark_persisted!
    instance._note_hydrated
    instance
  end

  def initialize(attrs = ActiveRecord::Base::EMPTY_ATTRS)
    super()
    self.id = (attrs[:id] || 0).to_i
    self.author_id = attrs[:author_id] || 0
    self.body = (attrs[:body] || "").to_s
    self.created_at_raw = ""
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if !(attrs[:created_at].nil?)
    self.description = (attrs[:description] || "").to_s
    self.published_at_raw = nil
    self.published_at_raw = ActiveSupport.format_db_time(attrs[:published_at]) if !(attrs[:published_at].nil?)
    self.revision = attrs[:revision] || 1
    self.slug = (attrs[:slug] || "").to_s
    self.status = (attrs[:status] || "published").to_s
    self.tag_list = attrs[:tag_list] || []
    self.title = (attrs[:title] || "").to_s
    self.updated_at_raw = ""
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if !(attrs[:updated_at].nil?)
    self.author = attrs[:author] if !(attrs[:author].nil?)
    @comments_cache = nil
    @comments_loaded = false
    @favorites_cache = nil
    @favorites_loaded = false
    @article_shares_cache = nil
    @article_shares_loaded = false
  end
  private :initialize

  def attributes
    { "author_id" => @author_id, "body" => @body, "created_at" => @created_at_raw, "description" => @description, "published_at" => @published_at_raw, "revision" => @revision, "slug" => @slug, "status" => @status, "tag_list" => @tag_list, "title" => @title, "updated_at" => @updated_at_raw }
  end

  def [](name)
    case name.to_sym
    when :id
      @id
    when :author_id
      @author_id
    when :body
      @body
    when :created_at
      @created_at_raw
    when :description
      @description
    when :published_at
      @published_at_raw&.to_s
    when :revision
      @revision
    when :slug
      @slug
    when :status
      @status
    when :tag_list
      @tag_list
    when :title
      @title
    when :updated_at
      @updated_at_raw
    else
      _projection_attribute name.to_s
    end
  end

  def []=(name, value)
    case name
    when :id
      @id = (value).to_i
    when :author_id
      @author_id = (value).to_i
    when :body
      @body = (value).to_s
    when :created_at
      self.created_at_raw = ActiveSupport.format_db_time(value)
    when :description
      @description = (value).to_s
    when :published_at
      self.published_at_raw = ActiveSupport.format_db_time(value)
    when :revision
      @revision = (value).to_i
    when :slug
      @slug = (value).to_s
    when :status
      @status = (value).to_s
    when :tag_list
      @tag_list = value
    when :title
      @title = (value).to_s
    when :updated_at
      self.updated_at_raw = ActiveSupport.format_db_time(value)
    end
  end

  def update(attrs)
    self.author_id = (attrs[:author_id]).to_i if attrs.key?(:author_id)
    self.body = (attrs[:body]).to_s if attrs.key?(:body)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.description = (attrs[:description]).to_s if attrs.key?(:description)
    self.published_at_raw = attrs[:published_at]&.to_s if attrs.key?(:published_at)
    self.published_at_raw = ActiveSupport.format_db_time(attrs[:published_at]) if attrs.key?(:published_at)
    self.revision = (attrs[:revision]).to_i if attrs.key?(:revision)
    self.slug = (attrs[:slug]).to_s if attrs.key?(:slug)
    self.status = (attrs[:status]).to_s if attrs.key?(:status)
    self.tag_list = attrs[:tag_list] if attrs.key?(:tag_list)
    self.title = (attrs[:title]).to_s if attrs.key?(:title)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.save
  end

  def update!(attrs)
    self.author_id = (attrs[:author_id]).to_i if attrs.key?(:author_id)
    self.body = (attrs[:body]).to_s if attrs.key?(:body)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.description = (attrs[:description]).to_s if attrs.key?(:description)
    self.published_at_raw = attrs[:published_at]&.to_s if attrs.key?(:published_at)
    self.published_at_raw = ActiveSupport.format_db_time(attrs[:published_at]) if attrs.key?(:published_at)
    self.revision = (attrs[:revision]).to_i if attrs.key?(:revision)
    self.slug = (attrs[:slug]).to_s if attrs.key?(:slug)
    self.status = (attrs[:status]).to_s if attrs.key?(:status)
    self.tag_list = attrs[:tag_list] if attrs.key?(:tag_list)
    self.title = (attrs[:title]).to_s if attrs.key?(:title)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.save!
    self
  end

  def fill_timestamps(creating)
    now = ActiveSupport.db_now
    if !(creating) || @updated_at_raw.nil? || @updated_at_raw.empty?
      @__t_updated_at = nil
      @updated_at_raw = now
    end
    if creating && (@created_at_raw.nil? || @created_at_raw.empty?)
      @__t_created_at = nil
      @created_at_raw = now
    end
  end

  def self._find_primary_key_input(id)
    cast = ActiveRecord::IntegerKeyCast.parse(id)
    _adapter_find_by_id(cast.value) if cast.valid
  end

  def self._exists_primary_key_input(id)
    cast = ActiveRecord::IntegerKeyCast.parse(id)
    if cast.valid
      _adapter_exists_by_id?(cast.value)
    else
      false
    end
  end

  def self._adapter_find_by_id(id)
    stmt = Db.prepare("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = Article.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_all
    stmt = Db.prepare("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\"")
    begin
      results = []
      while Db.step?(stmt)
        results << Article.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

  def self._adapter_last
    stmt = Db.prepare("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\" ORDER BY \"id\" DESC LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = Article.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def _adapter_insert
    Db.insert_returning_int("INSERT INTO \"articles\" (\"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\") VALUES (" + Db.escape_int(@author_id) + ", " + Db.escape_string(@body) + ", " + Db.escape_string(@created_at_raw) + ", " + Db.escape_string(@description) + ", " + Db.escape_string_opt(@published_at_raw) + ", " + Db.escape_int(@revision) + ", " + Db.escape_string(@slug) + ", " + Db.escape_string(@status) + ", " + Db.escape_array(@tag_list) + ", " + Db.escape_string(@title) + ", " + Db.escape_string(@updated_at_raw) + ")" + " RETURNING \"id\"")
  end

  def _adapter_update
    Db.exec("UPDATE \"articles\" SET \"author_id\" = " + Db.escape_int(@author_id) + ", \"body\" = " + Db.escape_string(@body) + ", \"created_at\" = " + Db.escape_string(@created_at_raw) + ", \"description\" = " + Db.escape_string(@description) + ", \"published_at\" = " + Db.escape_string_opt(@published_at_raw) + ", \"revision\" = " + Db.escape_int(@revision) + ", \"slug\" = " + Db.escape_string(@slug) + ", \"status\" = " + Db.escape_string(@status) + ", \"tag_list\" = " + Db.escape_array(@tag_list) + ", \"title\" = " + Db.escape_string(@title) + ", \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_touch
    Db.exec("UPDATE \"articles\" SET \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_delete
    Db.exec("TRUNCATE \"articles\" RESTART IDENTITY CASCADE")
  end

  def self._adapter_count
    stmt = Db.prepare("SELECT COUNT(*) FROM \"articles\"")
    begin
      Db.step?(stmt)
      result = Db.column_int(stmt, 0)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_any?
    stmt = Db.prepare("SELECT 1 FROM \"articles\" LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_exists_by_id?(id)
    stmt = Db.prepare("SELECT 1 FROM \"articles\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_truncate
    Db.exec("DELETE FROM \"articles\"")
  end

  def self.delete_all
    Db.exec("DELETE FROM \"articles\"")
    Db.changes
  end

  def _adapter_reload
    @author_loaded = false
    @comments_loaded = false
    @favorites_loaded = false
    @article_shares_loaded = false
    stmt = Db.prepare("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_int(stmt, 1, @id)
      if Db.step?(stmt)
        @id = Db.column_int(stmt, 0)
        @author_id = Db.column_int(stmt, 1)
        @body = Db.column_text(stmt, 2)
        @__t_created_at = nil
        @created_at_raw = Db.column_text(stmt, 3)
        @description = Db.column_text(stmt, 4)
        @__t_published_at = nil
        @published_at_raw = Db.column_text_opt(stmt, 5)
        @revision = Db.column_int(stmt, 6)
        @slug = Db.column_text(stmt, 7)
        @status = Db.column_text(stmt, 8)
        @tag_list = Db.column_array(stmt, 9)
        @title = Db.column_text(stmt, 10)
        @__t_updated_at = nil
        @updated_at_raw = Db.column_text(stmt, 11)
        self.mark_persisted!
      end
    ensure
      Db.finalize(stmt)
    end
    self
  end

  def _adapter_reload_lock
    @author_loaded = false
    @comments_loaded = false
    @favorites_loaded = false
    @article_shares_loaded = false
    stmt = Db.prepare_locked("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\" WHERE \"id\" = ? LIMIT 1")
    Db.bind_int(stmt, 1, @id)
    if Db.step?(stmt)
      @id = Db.column_int(stmt, 0)
      @author_id = Db.column_int(stmt, 1)
      @body = Db.column_text(stmt, 2)
      @__t_created_at = nil
      @created_at_raw = Db.column_text(stmt, 3)
      @description = Db.column_text(stmt, 4)
      @__t_published_at = nil
      @published_at_raw = Db.column_text_opt(stmt, 5)
      @revision = Db.column_int(stmt, 6)
      @slug = Db.column_text(stmt, 7)
      @status = Db.column_text(stmt, 8)
      @tag_list = Db.column_array(stmt, 9)
      @title = Db.column_text(stmt, 10)
      @__t_updated_at = nil
      @updated_at_raw = Db.column_text(stmt, 11)
      self.mark_persisted!
    end
    Db.finalize(stmt)
    self
  end

  def self._columns_sql
    "\"articles\".\"id\" AS \"id\", \"articles\".\"author_id\" AS \"author_id\", \"articles\".\"body\" AS \"body\", \"articles\".\"created_at\" AS \"created_at\", \"articles\".\"description\" AS \"description\", \"articles\".\"published_at\" AS \"published_at\", \"articles\".\"revision\" AS \"revision\", \"articles\".\"slug\" AS \"slug\", \"articles\".\"status\" AS \"status\", \"articles\".\"tag_list\" AS \"tag_list\", \"articles\".\"title\" AS \"title\", \"articles\".\"updated_at\" AS \"updated_at\""
  end

  def self._hydrate_all(sql)
    stmt = Db.prepare(sql)
    begin
      results = []
      while Db.step?(stmt)
        results << Article.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

#<SPINEL_SOURCE>app/app/models/article.rb:2
  def validate
    if @author_id.nil? || @author_id == 0 || !(User.exists?(@author_id))
      self.errors << "Author must exist"
      self.error_details << ActiveRecord::ErrorDetail.new("author", "blank", "must exist", "Author must exist", true, true)
    end
#<SPINEL_SOURCE>app/app/models/article.rb:6
    if @title.nil? || @title.empty?
      self.errors << "Title can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("title", "blank", "can't be blank", "Title can't be blank", true, true)
    end
    if @description.nil? || @description.empty?
      self.errors << "Description can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("description", "blank", "can't be blank", "Description can't be blank", true, true)
    end
    if @body.nil? || @body.empty?
      self.errors << "Body can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("body", "blank", "can't be blank", "Body can't be blank", true, true)
    end
#<SPINEL_SOURCE>app/app/models/article.rb:7
    if !(["draft", "published"].include?(@status))
      self.errors << "Status is not included in the list"
      self.error_details << ActiveRecord::ErrorDetail.new("status", "inclusion", "is not included in the list", "Status is not included in the list", true, false)
    end
#<SPINEL_SOURCE>app/app/models/article.rb:8
    if ActiveRecord::Relation.new(Article).where({ slug: @slug }).not(id: @id).exists?
      self.errors << "Slug has already been taken"
      self.error_details << ActiveRecord::ErrorDetail.new("slug", "taken", "has already been taken", "Slug has already been taken", true, false)
    end
  end

  def author
    return @author_cache if @author_loaded
#<SPINEL_SOURCE>app/app/models/article.rb:2
    @author_cache = if @author_id == 0
      nil
    else
      stmt = Db.prepare("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @author_id.to_s, 8) + " LIMIT 1")
      begin
        result = nil
        if Db.step?(stmt)
          result = User.from_stmt(stmt)
        end
      ensure
        Db.finalize(stmt)
      end
      result
    end
    @author_loaded = true
    @author_cache
  end

  def author=(value)
    @author_loaded = false
    if value.nil?
      @author_id = 0
    else
      @author_id = value.id
      @author_cache = value
      @author_loaded = true
    end
  end

  def author_loaded?
    @author_loaded
  end

#<SPINEL_SOURCE>app/app/models/article.rb:3
  def comments
    return __comments_cache if @comments_loaded
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\" FROM \"comments\" WHERE " + ActiveRecord.integer_query_predicate("\"article_id\"", @id.to_s, 8))
    begin
      results = []
      while Db.step?(stmt)
        results << Comment.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

  def _preload_comments(list)
    @comments_cache = list
    @comments_loaded = true
  end

  def comments_loaded?
    @comments_loaded
  end

  def reload_comments
    @comments_loaded = false
    self.comments
  end

  def comments_target
    __comments_cache
  end

  def comment_ids
    self.comments.map { |rh_id_record| rh_id_record.id }
  end

#<SPINEL_SOURCE>app/app/models/article.rb:4
  def favorites
    return __favorites_cache if @favorites_loaded
    stmt = Db.prepare("SELECT \"article_id\", \"user_id\" FROM \"favorites\" WHERE " + ActiveRecord.integer_query_predicate("\"article_id\"", @id.to_s, 8))
    begin
      results = []
      while Db.step?(stmt)
        results << Favorite.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

  def _preload_favorites(list)
    @favorites_cache = list
    @favorites_loaded = true
  end

  def favorites_loaded?
    @favorites_loaded
  end

  def reload_favorites
    @favorites_loaded = false
    self.favorites
  end

  def favorites_target
    __favorites_cache
  end

  def favorite_ids
    self.favorites.map { |rh_id_record| rh_id_record.id }
  end

#<SPINEL_SOURCE>app/app/models/article.rb:5
  def article_shares
    return __article_shares_cache if @article_shares_loaded
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\" FROM \"article_shares\" WHERE " + ActiveRecord.integer_query_predicate("\"article_id\"", @id.to_s, 8))
    begin
      results = []
      while Db.step?(stmt)
        results << ArticleShare.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

  def _preload_article_shares(list)
    @article_shares_cache = list
    @article_shares_loaded = true
  end

  def article_shares_loaded?
    @article_shares_loaded
  end

  def reload_article_shares
    @article_shares_loaded = false
    self.article_shares
  end

  def article_shares_target
    __article_shares_cache
  end

  def article_share_ids
    self.article_shares.map { |rh_id_record| rh_id_record.id }
  end

#<SPINEL_SOURCE>app/app/models/article.rb:1
  def self._association_names
    [:author, :comments, :favorites, :article_shares]
  end

#<SPINEL_SOURCE>app/app/models/article.rb:3
  def before_destroy
    self.comments.each { |c| c.destroy }
#<SPINEL_SOURCE>app/app/models/article.rb:4
    ActiveRecord::Relation.new(Favorite).where({ article_id: @id }).delete_all
#<SPINEL_SOURCE>app/app/models/article.rb:5
    self.article_shares.each { |c| c.destroy }
  end

#<SPINEL_SOURCE>app/app/models/article.rb:12
  def self.slug_for(title)
#<SPINEL_SOURCE>app/app/models/article.rb:13
    "#{(if (Inflector.parameterize(title.to_s) || "").strip.empty?
      nil
    else
      Inflector.parameterize(title.to_s)
    end) || "article"}-#{SecureRandom.hex(5)}"
  end

#<SPINEL_SOURCE>app/app/models/article.rb:16
  def shared_json
#<SPINEL_SOURCE>app/app/models/article.rb:17
    { slug: self.slug, title: self.title, body: self.body, revision: self.revision }
  end

#<SPINEL_SOURCE>app/app/models/article.rb:20
  def publish!
#<SPINEL_SOURCE>app/app/models/article.rb:21
    published = false
#<SPINEL_SOURCE>app/app/models/article.rb:22
    with_lock do
      if self.status == "draft"
        update!({ status: "published", published_at: Time.now.utc, revision: self.revision + 1 })
#<SPINEL_SOURCE>app/app/models/article.rb:25
        published = true
      end
    end
#<SPINEL_SOURCE>app/app/models/article.rb:28
    LiveRooms.updated(self) if published
  end

#<SPINEL_SOURCE>app/app/models/article.rb:1
  def dom_prefix
    "article"
  end

  def to_param
    @id.to_s
  end

  def dom_record_key
    @id.to_s
  end

  def cache_key
    if self.persisted?
      "articles/#{@id}"
    else
      "articles/new"
    end
  end

  def cache_key_with_version
    if self.persisted?
      "articles/#{@id}-#{@updated_at_raw}"
    else
      "articles/new-#{@updated_at_raw}"
    end
  end

  def reload(options = nil)
    super(options)
    self
  end

  def lock!(lock = true)
    super(lock)
    self
  end

  def to_gid_param
    GlobalID.param("Article", self.id)
  end

  def to_gid_uri
    GlobalID.uri("Article", self.id)
  end

#<SPINEL_SOURCE>app/app/models/article.rb:9
  def self.published(__rel = ActiveRecord::Relation.new(self))
    __rel = __rel.spawn
    __rel.spawn.where(status: "published")
  end

#<SPINEL_SOURCE>app/app/models/article.rb:10
  def self.visible_to(user, __rel = ActiveRecord::Relation.new(self))
    __rel = __rel.spawn
    __rel.spawn.spawn.where(status: "published").or(__rel.spawn.spawn.where(author_id: user && user.id))
  end

  def self.__scope_published__0(__rel)
    Article.published(__rel)
  end

  def self.__scope_visible_to__1(__rel, user)
    Article.visible_to(user, __rel)
  end

  def _autosave_author
    if @author_loaded && @author_id == 0 && !(@author_cache.nil?)
      @author_cache.save
      @author_id = @author_cache.id
    end
  end

  def before_validation
    _autosave_author
  end

  def self._preload_batch_author(records)
    ids = []
    records.each do |r|
      v = r.author_id
      if v.nil? || v == 0
        nil
      else
        ids << v
      end
    end
    ids.uniq!
    by_id = {}
    User._hydrate_all("SELECT " + User._columns_sql + " FROM users WHERE users.id IN (" + Db.escape_int_list(ids) + ")").each do |rec| by_id[rec.id] = rec end if ids.length > 0
    records.each do |r| r._preload_author(by_id[r.author_id]) end
    by_id.values
  end

  def _preload_author(rec)
    @author_cache = rec
    @author_loaded = true
    nil
  end

  def self._preload_batch_comments(records)
    ids = []
    records.each do |r| ids << r.id end
    loaded = []
    loaded = ActiveRecord::Relation.new(Comment).where(article_id: ids).to_a if ids.length > 0
    grouped = {}
    loaded.each do |rec|
      k = rec.article_id
      grouped[k] = [] if grouped[k].nil?
      grouped[k] << rec
    end
    records.each do |r| r._preload_comments(grouped[r.id] || []) end
    loaded
  end

  def self._preload_batch_favorites(records)
    ids = []
    records.each do |r| ids << r.id end
    loaded = []
    loaded = ActiveRecord::Relation.new(Favorite).where(article_id: ids).to_a if ids.length > 0
    grouped = {}
    loaded.each do |rec|
      k = rec.article_id
      grouped[k] = [] if grouped[k].nil?
      grouped[k] << rec
    end
    records.each do |r| r._preload_favorites(grouped[r.id] || []) end
    loaded
  end

  def self._preload_batch_article_shares(records)
    ids = []
    records.each do |r| ids << r.id end
    loaded = []
    loaded = ActiveRecord::Relation.new(ArticleShare).where(article_id: ids).to_a if ids.length > 0
    grouped = {}
    loaded.each do |rec|
      k = rec.article_id
      grouped[k] = [] if grouped[k].nil?
      grouped[k] << rec
    end
    records.each do |r| r._preload_article_shares(grouped[r.id] || []) end
    loaded
  end

  def self._preload_dispatch(records, name, nested)
    case name
    when :author
      loaded = _preload_batch_author(records)
      if nested.nil?
        nil
      else
        User.preload_associations(loaded, [nested])
      end
    when :comments
      loaded = _preload_batch_comments(records)
      if nested.nil?
        nil
      else
        Comment.preload_associations(loaded, [nested])
      end
    when :favorites
      loaded = _preload_batch_favorites(records)
      if nested.nil?
        nil
      else
        Favorite.preload_associations(loaded, [nested])
      end
    when :article_shares
      loaded = _preload_batch_article_shares(records)
      if nested.nil?
        nil
      else
        ArticleShare.preload_associations(loaded, [nested])
      end
    end
    nil
  end

  def self.preload_associations(records, specs)
    return if records.length == 0
    specs.each do |spec|
      if spec.is_a?(Hash)
        spec.each do |name, nested| _preload_dispatch(records, name, nested) end
      else
        if spec.is_a?(Array)
          preload_associations(records, spec)
        else
          _preload_dispatch(records, spec, nil) if !(spec.nil?)
        end
      end
    end
    nil
  end

  def __comments_cache
    c = @comments_cache
    if c.nil?
      c = []
      @comments_cache = c
    end
    c
  end

  def __favorites_cache
    c = @favorites_cache
    if c.nil?
      c = []
      @favorites_cache = c
    end
    c
  end

  def __article_shares_cache
    c = @article_shares_cache
    if c.nil?
      c = []
      @article_shares_cache = c
    end
    c
  end
end
