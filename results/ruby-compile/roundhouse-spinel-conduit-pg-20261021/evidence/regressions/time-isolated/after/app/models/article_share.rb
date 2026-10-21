require "securerandom"
require "digest"
require_relative "application_record"
require_relative "../../runtime/security_utils"

class ArticleShare < ApplicationRecord
#<SPINEL_SOURCE>app/app/models/article_share.rb:2
  def id
    @id
  end

  def id=(value)
    @id = value
  end

  def article_id
    @article_id
  end

  def article_id=(value)
    @article_id = value
    @article_loaded = false
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

  def key_hash
    @key_hash
  end

  def key_hash=(value)
    @key_hash = value
  end

  def revoked_at
    ActiveSupport.present_db(@__t_revoked_at ||= ActiveSupport.parse_db_time(@revoked_at_raw))
  end

  def revoked_at_raw
    @revoked_at_raw
  end

  def revoked_at=(value)
    self.revoked_at_raw = ActiveSupport.format_db_time(value)
  end

  def revoked_at_raw=(value)
    @__t_revoked_at = nil
    @revoked_at_raw = value
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
    "article_shares"
  end

  def self._table_sql
    "\"article_shares\""
  end

  def self._string_primary_key
    true
  end

  def self._conflict_predicate(columns)
    if columns == "article_id"
      "(revoked_at IS NULL)"
    else
      ""
    end
  end

  def self.schema_columns
    [:id, :article_id, :created_at, :key_hash, :revoked_at, :updated_at]
  end

  def self.schema_time_columns
    [:created_at, :revoked_at, :updated_at]
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
    { "article_exports.id" => 8, "article_exports.user_id" => 8, "article_shares.article_id" => 8, "article_id" => 8, "articles.id" => 8, "articles.author_id" => 8, "articles.revision" => 4, "comments.id" => 8, "comments.article_id" => 8, "comments.author_id" => 8, "favorites.article_id" => 8, "favorites.user_id" => 8, "follows.followed_id" => 8, "follows.follower_id" => 8, "good_job_batches.callback_priority" => 4, "good_job_executions.error_event" => 4, "good_job_processes.lock_type" => 4, "good_jobs.error_event" => 4, "good_jobs.executions_count" => 4, "good_jobs.lock_type" => 4, "good_jobs.priority" => 4, "users.id" => 8 }
  end

  def self.instantiate(row)
    instance = ArticleShare.from_row(ArticleShareRow.from_raw(row))
    instance.mark_persisted!
    instance._note_projection(row)
    instance
  end

  def self.from_row(row)
    instance = ArticleShare.new
    instance.id = row.id
    instance.article_id = row.article_id
    instance.created_at_raw = row.created_at
    instance.key_hash = row.key_hash
    instance.revoked_at_raw = row.revoked_at&.to_s
    instance.updated_at_raw = row.updated_at
    instance._note_hydrated
    instance
  end

  def self.from_stmt(stmt)
    instance = ArticleShare.new
    instance.id = Db.column_text(stmt, 0)
    instance.article_id = Db.column_int(stmt, 1)
    instance.created_at_raw = Db.column_text(stmt, 2)
    instance.key_hash = Db.column_text(stmt, 3)
    instance.revoked_at_raw = Db.column_text_opt(stmt, 4)
    instance.updated_at_raw = Db.column_text(stmt, 5)
    instance.mark_persisted!
    instance._note_hydrated
    instance
  end

  def initialize(attrs = ActiveRecord::Base::EMPTY_ATTRS)
    super()
    self.id = (attrs[:id] || "").to_s
    self.article_id = attrs[:article_id] || 0
    self.created_at_raw = ""
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if !(attrs[:created_at].nil?)
    self.key_hash = (attrs[:key_hash] || "").to_s
    self.revoked_at_raw = nil
    self.revoked_at_raw = ActiveSupport.format_db_time(attrs[:revoked_at]) if !(attrs[:revoked_at].nil?)
    self.updated_at_raw = ""
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if !(attrs[:updated_at].nil?)
    self.article = attrs[:article] if !(attrs[:article].nil?)
  end
  private :initialize

  def attributes
    { "article_id" => @article_id, "created_at" => @created_at_raw, "key_hash" => @key_hash, "revoked_at" => @revoked_at_raw, "updated_at" => @updated_at_raw }
  end

  def [](name)
    case name.to_sym
    when :id
      @id
    when :article_id
      @article_id
    when :created_at
      @created_at_raw
    when :key_hash
      @key_hash
    when :revoked_at
      @revoked_at_raw&.to_s
    when :updated_at
      @updated_at_raw
    else
      _projection_attribute name.to_s
    end
  end

  def []=(name, value)
    case name
    when :id
      @id = (value).to_s
    when :article_id
      @article_id = (value).to_i
    when :created_at
      self.created_at_raw = ActiveSupport.format_db_time(value)
    when :key_hash
      @key_hash = (value).to_s
    when :revoked_at
      self.revoked_at_raw = ActiveSupport.format_db_time(value)
    when :updated_at
      self.updated_at_raw = ActiveSupport.format_db_time(value)
    end
  end

  def update(attrs)
    self.article_id = (attrs[:article_id]).to_i if attrs.key?(:article_id)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.key_hash = (attrs[:key_hash]).to_s if attrs.key?(:key_hash)
    self.revoked_at_raw = attrs[:revoked_at]&.to_s if attrs.key?(:revoked_at)
    self.revoked_at_raw = ActiveSupport.format_db_time(attrs[:revoked_at]) if attrs.key?(:revoked_at)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.save
  end

  def update!(attrs)
    self.article_id = (attrs[:article_id]).to_i if attrs.key?(:article_id)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.key_hash = (attrs[:key_hash]).to_s if attrs.key?(:key_hash)
    self.revoked_at_raw = attrs[:revoked_at]&.to_s if attrs.key?(:revoked_at)
    self.revoked_at_raw = ActiveSupport.format_db_time(attrs[:revoked_at]) if attrs.key?(:revoked_at)
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
    _adapter_find_by_id(ActiveRecord::IntegerKeyCast.input_text(id))
  end

  def self._exists_primary_key_input(id)
    _adapter_exists_by_id?(ActiveRecord::IntegerKeyCast.input_text(id))
  end

  def self._adapter_find_by_id(id)
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\" FROM \"article_shares\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_text(stmt, 1, id)
      result = nil
      if Db.step?(stmt)
        result = ArticleShare.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_all
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\" FROM \"article_shares\"")
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

  def self._adapter_last
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\" FROM \"article_shares\" ORDER BY \"id\" DESC LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = ArticleShare.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def _adapter_insert
    Db.insert_returning_text("INSERT INTO \"article_shares\" (\"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\") VALUES (" + Db.escape_int(@article_id) + ", " + Db.escape_string(@created_at_raw) + ", " + Db.escape_string(@key_hash) + ", " + Db.escape_string_opt(@revoked_at_raw) + ", " + Db.escape_string(@updated_at_raw) + ")" + " RETURNING \"id\"")
  end

  def _adapter_update
    Db.exec("UPDATE \"article_shares\" SET \"article_id\" = " + Db.escape_int(@article_id) + ", \"created_at\" = " + Db.escape_string(@created_at_raw) + ", \"key_hash\" = " + Db.escape_string(@key_hash) + ", \"revoked_at\" = " + Db.escape_string_opt(@revoked_at_raw) + ", \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE \"id\" = " + Db.escape_string(@id))
  end

  def _adapter_touch
    Db.exec("UPDATE \"article_shares\" SET \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE \"id\" = " + Db.escape_string(@id))
  end

  def _adapter_delete
    Db.exec("TRUNCATE \"article_shares\" RESTART IDENTITY CASCADE")
  end

  def self._adapter_count
    stmt = Db.prepare("SELECT COUNT(*) FROM \"article_shares\"")
    begin
      Db.step?(stmt)
      result = Db.column_int(stmt, 0)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_any?
    stmt = Db.prepare("SELECT 1 FROM \"article_shares\" LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_exists_by_id?(id)
    stmt = Db.prepare("SELECT 1 FROM \"article_shares\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_text(stmt, 1, id)
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_truncate
    Db.exec("DELETE FROM \"article_shares\"")
  end

  def self.delete_all
    Db.exec("DELETE FROM \"article_shares\"")
    Db.changes
  end

  def _adapter_reload
    @article_loaded = false
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\" FROM \"article_shares\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_text(stmt, 1, @id)
      if Db.step?(stmt)
        @id = Db.column_text(stmt, 0)
        @article_id = Db.column_int(stmt, 1)
        @__t_created_at = nil
        @created_at_raw = Db.column_text(stmt, 2)
        @key_hash = Db.column_text(stmt, 3)
        @__t_revoked_at = nil
        @revoked_at_raw = Db.column_text_opt(stmt, 4)
        @__t_updated_at = nil
        @updated_at_raw = Db.column_text(stmt, 5)
        self.mark_persisted!
      end
    ensure
      Db.finalize(stmt)
    end
    self
  end

  def _adapter_reload_lock
    @article_loaded = false
    stmt = Db.prepare_locked("SELECT \"id\", \"article_id\", \"created_at\", \"key_hash\", \"revoked_at\", \"updated_at\" FROM \"article_shares\" WHERE \"id\" = ? LIMIT 1")
    Db.bind_text(stmt, 1, @id)
    if Db.step?(stmt)
      @id = Db.column_text(stmt, 0)
      @article_id = Db.column_int(stmt, 1)
      @__t_created_at = nil
      @created_at_raw = Db.column_text(stmt, 2)
      @key_hash = Db.column_text(stmt, 3)
      @__t_revoked_at = nil
      @revoked_at_raw = Db.column_text_opt(stmt, 4)
      @__t_updated_at = nil
      @updated_at_raw = Db.column_text(stmt, 5)
      self.mark_persisted!
    end
    Db.finalize(stmt)
    self
  end

  def self._columns_sql
    "\"article_shares\".\"id\" AS \"id\", \"article_shares\".\"article_id\" AS \"article_id\", \"article_shares\".\"created_at\" AS \"created_at\", \"article_shares\".\"key_hash\" AS \"key_hash\", \"article_shares\".\"revoked_at\" AS \"revoked_at\", \"article_shares\".\"updated_at\" AS \"updated_at\""
  end

  def self._hydrate_all(sql)
    stmt = Db.prepare(sql)
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

#<SPINEL_SOURCE>app/app/models/article_share.rb:3
  def validate
    if @article_id.nil? || @article_id == 0 || !(Article.exists?(@article_id))
      self.errors << "Article must exist"
      self.error_details << ActiveRecord::ErrorDetail.new("article", "blank", "must exist", "Article must exist", true, true)
    end
  end

  def article
    return @article_cache if @article_loaded
    @article_cache = if @article_id == 0
      nil
    else
      stmt = Db.prepare("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @article_id.to_s, 8) + " LIMIT 1")
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
    @article_loaded = true
    @article_cache
  end

  def article=(value)
    @article_loaded = false
    if value.nil?
      @article_id = 0
    else
      @article_id = value.id
      @article_cache = value
      @article_loaded = true
    end
  end

  def article_loaded?
    @article_loaded
  end

#<SPINEL_SOURCE>app/app/models/article_share.rb:2
  def self._association_names
    [:article]
  end

#<SPINEL_SOURCE>app/app/models/article_share.rb:6
  def self.issue!(article)
#<SPINEL_SOURCE>app/app/models/article_share.rb:7
    key = SecureRandom.urlsafe_base64(32)
#<SPINEL_SOURCE>app/app/models/article_share.rb:8
    share = nil
#<SPINEL_SOURCE>app/app/models/article_share.rb:9
    old = nil
#<SPINEL_SOURCE>app/app/models/article_share.rb:10
    article.with_lock do
      old = ArticleShare.active.where(article_id: article).pluck(:id)
#<SPINEL_SOURCE>app/app/models/article_share.rb:12
      ArticleShare.active.where(article_id: article).update_all(revoked_at: Time.now.utc)
#<SPINEL_SOURCE>app/app/models/article_share.rb:13
      share = create!(article: article, key_hash: Digest::SHA256.hexdigest(key))
    end
#<SPINEL_SOURCE>app/app/models/article_share.rb:15
    [ share, key, old ]
  end

#<SPINEL_SOURCE>app/app/models/article_share.rb:18
  def valid_key?(key)
#<SPINEL_SOURCE>app/app/models/article_share.rb:19
    if self.revoked_at.nil? && key.is_a?(String)
      nil
    else
      return false
    end
#<SPINEL_SOURCE>app/app/models/article_share.rb:20
    hash = Digest::SHA256.hexdigest(key)
#<SPINEL_SOURCE>app/app/models/article_share.rb:21
    ActiveSupport::SecurityUtils.secure_compare(self.key_hash, hash)
  end

#<SPINEL_SOURCE>app/app/models/article_share.rb:2
  def dom_prefix
    "article_share"
  end

  def to_param
    @id.to_s
  end

  def dom_record_key
    @id.to_s
  end

  def cache_key
    if self.persisted?
      "article_shares/#{@id}"
    else
      "article_shares/new"
    end
  end

  def cache_key_with_version
    if self.persisted?
      "article_shares/#{@id}-#{@updated_at_raw}"
    else
      "article_shares/new-#{@updated_at_raw}"
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
    GlobalID.param("ArticleShare", self.id)
  end

  def to_gid_uri
    GlobalID.uri("ArticleShare", self.id)
  end

#<SPINEL_SOURCE>app/app/models/article_share.rb:4
  def self.active(__rel = ActiveRecord::Relation.new(self))
    __rel = __rel.spawn
    __rel.spawn.where(revoked_at: nil)
  end

  def self.__scope_active__0(__rel)
    ArticleShare.active(__rel)
  end

  def _autosave_article
    if @article_loaded && @article_id == 0 && !(@article_cache.nil?)
      @article_cache.save
      @article_id = @article_cache.id
    end
  end

  def before_validation
    _autosave_article
  end

  def self._preload_batch_article(records)
    ids = []
    records.each do |r|
      v = r.article_id
      if v.nil? || v == 0
        nil
      else
        ids << v
      end
    end
    ids.uniq!
    by_id = {}
    Article._hydrate_all("SELECT " + Article._columns_sql + " FROM articles WHERE articles.id IN (" + Db.escape_int_list(ids) + ")").each do |rec| by_id[rec.id] = rec end if ids.length > 0
    records.each do |r| r._preload_article(by_id[r.article_id]) end
    by_id.values
  end

  def _preload_article(rec)
    @article_cache = rec
    @article_loaded = true
    nil
  end

  def self._preload_dispatch(records, name, nested)
    case name
    when :article
      loaded = _preload_batch_article(records)
      if nested.nil?
        nil
      else
        Article.preload_associations(loaded, [nested])
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
end
