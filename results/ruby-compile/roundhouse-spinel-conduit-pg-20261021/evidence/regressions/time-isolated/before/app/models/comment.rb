require_relative "application_record"

class Comment < ApplicationRecord
#<SPINEL_SOURCE>app/app/models/comment.rb:1
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
    "comments"
  end

  def self._table_sql
    "\"comments\""
  end

  def self.schema_columns
    [:id, :article_id, :author_id, :body, :created_at, :updated_at]
  end

  def self.schema_time_columns
    [:created_at, :updated_at]
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
    { "article_exports.id" => 8, "article_exports.user_id" => 8, "article_shares.article_id" => 8, "articles.id" => 8, "articles.author_id" => 8, "articles.revision" => 4, "comments.id" => 8, "id" => 8, "comments.article_id" => 8, "article_id" => 8, "comments.author_id" => 8, "author_id" => 8, "favorites.article_id" => 8, "favorites.user_id" => 8, "follows.followed_id" => 8, "follows.follower_id" => 8, "good_job_batches.callback_priority" => 4, "good_job_executions.error_event" => 4, "good_job_processes.lock_type" => 4, "good_jobs.error_event" => 4, "good_jobs.executions_count" => 4, "good_jobs.lock_type" => 4, "good_jobs.priority" => 4, "users.id" => 8 }
  end

  def self.instantiate(row)
    instance = Comment.from_row(CommentRow.from_raw(row))
    instance.mark_persisted!
    instance._note_projection(row)
    instance
  end

  def self.from_row(row)
    instance = Comment.new
    instance.id = row.id
    instance.article_id = row.article_id
    instance.author_id = row.author_id
    instance.body = row.body
    instance.created_at_raw = row.created_at
    instance.updated_at_raw = row.updated_at
    instance._note_hydrated
    instance
  end

  def self.from_stmt(stmt)
    instance = Comment.new
    instance.id = Db.column_int(stmt, 0)
    instance.article_id = Db.column_int(stmt, 1)
    instance.author_id = Db.column_int(stmt, 2)
    instance.body = Db.column_text(stmt, 3)
    instance.created_at_raw = Db.column_text(stmt, 4)
    instance.updated_at_raw = Db.column_text(stmt, 5)
    instance.mark_persisted!
    instance._note_hydrated
    instance
  end

  def initialize(attrs = ActiveRecord::Base::EMPTY_ATTRS)
    super()
    self.id = (attrs[:id] || 0).to_i
    self.article_id = attrs[:article_id] || 0
    self.author_id = attrs[:author_id] || 0
    self.body = (attrs[:body] || "").to_s
    self.created_at_raw = attrs[:created_at] || ""
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if !(attrs[:created_at].nil?)
    self.updated_at_raw = attrs[:updated_at] || ""
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if !(attrs[:updated_at].nil?)
    self.article = attrs[:article] if !(attrs[:article].nil?)
    self.author = attrs[:author] if !(attrs[:author].nil?)
  end
  private :initialize

  def attributes
    { "article_id" => @article_id, "author_id" => @author_id, "body" => @body, "created_at" => @created_at_raw, "updated_at" => @updated_at_raw }
  end

  def [](name)
    case name.to_sym
    when :id
      @id
    when :article_id
      @article_id
    when :author_id
      @author_id
    when :body
      @body
    when :created_at
      @created_at_raw
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
    when :article_id
      @article_id = (value).to_i
    when :author_id
      @author_id = (value).to_i
    when :body
      @body = (value).to_s
    when :created_at
      self.created_at_raw = ActiveSupport.format_db_time(value)
    when :updated_at
      self.updated_at_raw = ActiveSupport.format_db_time(value)
    end
  end

  def update(attrs)
    self.article_id = (attrs[:article_id]).to_i if attrs.key?(:article_id)
    self.author_id = (attrs[:author_id]).to_i if attrs.key?(:author_id)
    self.body = (attrs[:body]).to_s if attrs.key?(:body)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.save
  end

  def update!(attrs)
    self.article_id = (attrs[:article_id]).to_i if attrs.key?(:article_id)
    self.author_id = (attrs[:author_id]).to_i if attrs.key?(:author_id)
    self.body = (attrs[:body]).to_s if attrs.key?(:body)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
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
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\" FROM \"comments\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = Comment.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_all
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\" FROM \"comments\"")
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

  def self._adapter_last
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\" FROM \"comments\" ORDER BY \"id\" DESC LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = Comment.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def _adapter_insert
    Db.insert_returning_int("INSERT INTO \"comments\" (\"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\") VALUES (" + Db.escape_int(@article_id) + ", " + Db.escape_int(@author_id) + ", " + Db.escape_string(@body) + ", " + Db.escape_string(@created_at_raw) + ", " + Db.escape_string(@updated_at_raw) + ")" + " RETURNING \"id\"")
  end

  def _adapter_update
    Db.exec("UPDATE \"comments\" SET \"article_id\" = " + Db.escape_int(@article_id) + ", \"author_id\" = " + Db.escape_int(@author_id) + ", \"body\" = " + Db.escape_string(@body) + ", \"created_at\" = " + Db.escape_string(@created_at_raw) + ", \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_touch
    Db.exec("UPDATE \"comments\" SET \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_delete
    Db.exec("TRUNCATE \"comments\" RESTART IDENTITY CASCADE")
  end

  def self._adapter_count
    stmt = Db.prepare("SELECT COUNT(*) FROM \"comments\"")
    begin
      Db.step?(stmt)
      result = Db.column_int(stmt, 0)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_any?
    stmt = Db.prepare("SELECT 1 FROM \"comments\" LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_exists_by_id?(id)
    stmt = Db.prepare("SELECT 1 FROM \"comments\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_truncate
    Db.exec("DELETE FROM \"comments\"")
  end

  def self.delete_all
    Db.exec("DELETE FROM \"comments\"")
    Db.changes
  end

  def _adapter_reload
    @article_loaded = false
    @author_loaded = false
    stmt = Db.prepare("SELECT \"id\", \"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\" FROM \"comments\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_int(stmt, 1, @id)
      if Db.step?(stmt)
        @id = Db.column_int(stmt, 0)
        @article_id = Db.column_int(stmt, 1)
        @author_id = Db.column_int(stmt, 2)
        @body = Db.column_text(stmt, 3)
        @__t_created_at = nil
        @created_at_raw = Db.column_text(stmt, 4)
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
    @author_loaded = false
    stmt = Db.prepare_locked("SELECT \"id\", \"article_id\", \"author_id\", \"body\", \"created_at\", \"updated_at\" FROM \"comments\" WHERE \"id\" = ? LIMIT 1")
    Db.bind_int(stmt, 1, @id)
    if Db.step?(stmt)
      @id = Db.column_int(stmt, 0)
      @article_id = Db.column_int(stmt, 1)
      @author_id = Db.column_int(stmt, 2)
      @body = Db.column_text(stmt, 3)
      @__t_created_at = nil
      @created_at_raw = Db.column_text(stmt, 4)
      @__t_updated_at = nil
      @updated_at_raw = Db.column_text(stmt, 5)
      self.mark_persisted!
    end
    Db.finalize(stmt)
    self
  end

  def self._columns_sql
    "\"comments\".\"id\" AS \"id\", \"comments\".\"article_id\" AS \"article_id\", \"comments\".\"author_id\" AS \"author_id\", \"comments\".\"body\" AS \"body\", \"comments\".\"created_at\" AS \"created_at\", \"comments\".\"updated_at\" AS \"updated_at\""
  end

  def self._hydrate_all(sql)
    stmt = Db.prepare(sql)
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

#<SPINEL_SOURCE>app/app/models/comment.rb:2
  def validate
    if @article_id.nil? || @article_id == 0 || !(Article.exists?(@article_id))
      self.errors << "Article must exist"
      self.error_details << ActiveRecord::ErrorDetail.new("article", "blank", "must exist", "Article must exist", true, true)
    end
#<SPINEL_SOURCE>app/app/models/comment.rb:3
    if @author_id.nil? || @author_id == 0 || !(User.exists?(@author_id))
      self.errors << "Author must exist"
      self.error_details << ActiveRecord::ErrorDetail.new("author", "blank", "must exist", "Author must exist", true, true)
    end
#<SPINEL_SOURCE>app/app/models/comment.rb:4
    if @body.nil? || @body.empty?
      self.errors << "Body can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("body", "blank", "can't be blank", "Body can't be blank", true, true)
    end
  end

  def article
    return @article_cache if @article_loaded
#<SPINEL_SOURCE>app/app/models/comment.rb:2
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

  def author
    return @author_cache if @author_loaded
#<SPINEL_SOURCE>app/app/models/comment.rb:3
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

#<SPINEL_SOURCE>app/app/models/comment.rb:1
  def self._association_names
    [:article, :author]
  end

  def dom_prefix
    "comment"
  end

  def to_param
    @id.to_s
  end

  def dom_record_key
    @id.to_s
  end

  def cache_key
    if self.persisted?
      "comments/#{@id}"
    else
      "comments/new"
    end
  end

  def cache_key_with_version
    if self.persisted?
      "comments/#{@id}-#{@updated_at_raw}"
    else
      "comments/new-#{@updated_at_raw}"
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
    GlobalID.param("Comment", self.id)
  end

  def to_gid_uri
    GlobalID.uri("Comment", self.id)
  end

  def _autosave_article
    if @article_loaded && @article_id == 0 && !(@article_cache.nil?)
      @article_cache.save
      @article_id = @article_cache.id
    end
  end

  def before_validation
    _autosave_author
    _autosave_article
  end

  def _autosave_author
    if @author_loaded && @author_id == 0 && !(@author_cache.nil?)
      @author_cache.save
      @author_id = @author_cache.id
    end
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

  def self._preload_dispatch(records, name, nested)
    case name
    when :article
      loaded = _preload_batch_article(records)
      if nested.nil?
        nil
      else
        Article.preload_associations(loaded, [nested])
      end
    when :author
      loaded = _preload_batch_author(records)
      if nested.nil?
        nil
      else
        User.preload_associations(loaded, [nested])
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
