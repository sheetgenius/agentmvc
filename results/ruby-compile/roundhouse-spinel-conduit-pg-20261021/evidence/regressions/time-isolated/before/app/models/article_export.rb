require_relative "application_record"

class ArticleExport < ApplicationRecord
#<SPINEL_SOURCE>app/app/models/article_export.rb:1
  def id
    @id
  end

  def id=(value)
    @id = value
  end

  def articles
    JsonColumn.load(@articles)
  end

  def _write_articles_json_raw(value)
    @articles = value
    nil
  end

  def articles=(value)
    @articles = JsonColumn.dump(value)
  end

  def completed_at
    ActiveSupport.present_db(@__t_completed_at ||= ActiveSupport.parse_db_time(@completed_at_raw))
  end

  def completed_at_raw
    @completed_at_raw
  end

  def completed_at=(value)
    self.completed_at_raw = ActiveSupport.format_db_time(value)
  end

  def completed_at_raw=(value)
    @__t_completed_at = nil
    @completed_at_raw = value
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

  def status
    @status
  end

  def status=(value)
    @status = value
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

  def user_id
    @user_id
  end

  def user_id=(value)
    @user_id = value
    @user_loaded = false
  end

  def self.table_name
    "article_exports"
  end

  def self._table_sql
    "\"article_exports\""
  end

  def self.schema_columns
    [:id, :articles, :completed_at, :created_at, :status, :updated_at, :user_id]
  end

  def self.schema_time_columns
    [:completed_at, :created_at, :updated_at]
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
    { "article_exports.id" => 8, "id" => 8, "article_exports.user_id" => 8, "user_id" => 8, "article_shares.article_id" => 8, "articles.id" => 8, "articles.author_id" => 8, "articles.revision" => 4, "comments.id" => 8, "comments.article_id" => 8, "comments.author_id" => 8, "favorites.article_id" => 8, "favorites.user_id" => 8, "follows.followed_id" => 8, "follows.follower_id" => 8, "good_job_batches.callback_priority" => 4, "good_job_executions.error_event" => 4, "good_job_processes.lock_type" => 4, "good_jobs.error_event" => 4, "good_jobs.executions_count" => 4, "good_jobs.lock_type" => 4, "good_jobs.priority" => 4, "users.id" => 8 }
  end

  def self.instantiate(row)
    instance = ArticleExport.from_row(ArticleExportRow.from_raw(row))
    instance.mark_persisted!
    instance._note_projection(row)
    instance
  end

  def self.from_row(row)
    instance = ArticleExport.new
    instance.id = row.id
    instance._write_articles_json_raw(row.articles&.to_s)
    instance.completed_at_raw = row.completed_at&.to_s
    instance.created_at_raw = row.created_at
    instance.status = row.status
    instance.updated_at_raw = row.updated_at
    instance.user_id = row.user_id
    instance._note_hydrated
    instance
  end

  def self.from_stmt(stmt)
    instance = ArticleExport.new
    instance.id = Db.column_int(stmt, 0)
    instance._write_articles_json_raw(Db.column_text_opt(stmt, 1))
    instance.completed_at_raw = Db.column_text_opt(stmt, 2)
    instance.created_at_raw = Db.column_text(stmt, 3)
    instance.status = Db.column_text(stmt, 4)
    instance.updated_at_raw = Db.column_text(stmt, 5)
    instance.user_id = Db.column_int(stmt, 6)
    instance.mark_persisted!
    instance._note_hydrated
    instance
  end

  def initialize(attrs = ActiveRecord::Base::EMPTY_ATTRS)
    super()
    self.id = (attrs[:id] || 0).to_i
    self.articles = attrs[:articles]
    self.completed_at_raw = attrs[:completed_at]
    self.completed_at_raw = ActiveSupport.format_db_time(attrs[:completed_at]) if !(attrs[:completed_at].nil?)
    self.created_at_raw = attrs[:created_at] || ""
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if !(attrs[:created_at].nil?)
    self.status = (attrs[:status] || "pending").to_s
    self.updated_at_raw = attrs[:updated_at] || ""
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if !(attrs[:updated_at].nil?)
    self.user_id = attrs[:user_id] || 0
    self.user = attrs[:user] if !(attrs[:user].nil?)
  end
  private :initialize

  def attributes
    { "articles" => JsonColumn.load(@articles), "completed_at" => @completed_at_raw, "created_at" => @created_at_raw, "status" => @status, "updated_at" => @updated_at_raw, "user_id" => @user_id }
  end

  def [](name)
    case name.to_sym
    when :id
      @id
    when :articles
      JsonColumn.load(@articles)
    when :completed_at
      @completed_at_raw&.to_s
    when :created_at
      @created_at_raw
    when :status
      @status
    when :updated_at
      @updated_at_raw
    when :user_id
      @user_id
    else
      _projection_attribute name.to_s
    end
  end

  def []=(name, value)
    case name
    when :id
      @id = (value).to_i
    when :articles
      @articles = JsonColumn.dump(value)
    when :completed_at
      self.completed_at_raw = ActiveSupport.format_db_time(value)
    when :created_at
      self.created_at_raw = ActiveSupport.format_db_time(value)
    when :status
      @status = (value).to_s
    when :updated_at
      self.updated_at_raw = ActiveSupport.format_db_time(value)
    when :user_id
      @user_id = (value).to_i
    end
  end

  def update(attrs)
    self.articles = attrs[:articles] if attrs.key?(:articles)
    self.completed_at_raw = attrs[:completed_at]&.to_s if attrs.key?(:completed_at)
    self.completed_at_raw = ActiveSupport.format_db_time(attrs[:completed_at]) if attrs.key?(:completed_at)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.status = (attrs[:status]).to_s if attrs.key?(:status)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.user_id = (attrs[:user_id]).to_i if attrs.key?(:user_id)
    self.save
  end

  def update!(attrs)
    self.articles = attrs[:articles] if attrs.key?(:articles)
    self.completed_at_raw = attrs[:completed_at]&.to_s if attrs.key?(:completed_at)
    self.completed_at_raw = ActiveSupport.format_db_time(attrs[:completed_at]) if attrs.key?(:completed_at)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.status = (attrs[:status]).to_s if attrs.key?(:status)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.user_id = (attrs[:user_id]).to_i if attrs.key?(:user_id)
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
    stmt = Db.prepare("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = ArticleExport.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_all
    stmt = Db.prepare("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\"")
    begin
      results = []
      while Db.step?(stmt)
        results << ArticleExport.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

  def self._adapter_last
    stmt = Db.prepare("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\" ORDER BY \"id\" DESC LIMIT 1")
    begin
      result = nil
      if Db.step?(stmt)
        result = ArticleExport.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def _adapter_insert
    Db.insert_returning_int("INSERT INTO \"article_exports\" (\"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\") VALUES (" + Db.escape_string_opt(@articles) + ", " + Db.escape_string_opt(@completed_at_raw) + ", " + Db.escape_string(@created_at_raw) + ", " + Db.escape_string(@status) + ", " + Db.escape_string(@updated_at_raw) + ", " + Db.escape_int(@user_id) + ")" + " RETURNING \"id\"")
  end

  def _adapter_update
    Db.exec("UPDATE \"article_exports\" SET \"articles\" = " + Db.escape_string_opt(@articles) + ", \"completed_at\" = " + Db.escape_string_opt(@completed_at_raw) + ", \"created_at\" = " + Db.escape_string(@created_at_raw) + ", \"status\" = " + Db.escape_string(@status) + ", \"updated_at\" = " + Db.escape_string(@updated_at_raw) + ", \"user_id\" = " + Db.escape_int(@user_id) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_touch
    Db.exec("UPDATE \"article_exports\" SET \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_delete
    Db.exec("TRUNCATE \"article_exports\" RESTART IDENTITY CASCADE")
  end

  def self._adapter_count
    stmt = Db.prepare("SELECT COUNT(*) FROM \"article_exports\"")
    begin
      Db.step?(stmt)
      result = Db.column_int(stmt, 0)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_any?
    stmt = Db.prepare("SELECT 1 FROM \"article_exports\" LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_exists_by_id?(id)
    stmt = Db.prepare("SELECT 1 FROM \"article_exports\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_truncate
    Db.exec("DELETE FROM \"article_exports\"")
  end

  def self.delete_all
    Db.exec("DELETE FROM \"article_exports\"")
    Db.changes
  end

  def _adapter_reload
    @user_loaded = false
    stmt = Db.prepare("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_int(stmt, 1, @id)
      if Db.step?(stmt)
        @id = Db.column_int(stmt, 0)
        @articles = Db.column_text_opt(stmt, 1)
        @__t_completed_at = nil
        @completed_at_raw = Db.column_text_opt(stmt, 2)
        @__t_created_at = nil
        @created_at_raw = Db.column_text(stmt, 3)
        @status = Db.column_text(stmt, 4)
        @__t_updated_at = nil
        @updated_at_raw = Db.column_text(stmt, 5)
        @user_id = Db.column_int(stmt, 6)
        self.mark_persisted!
      end
    ensure
      Db.finalize(stmt)
    end
    self
  end

  def _adapter_reload_lock
    @user_loaded = false
    stmt = Db.prepare_locked("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\" WHERE \"id\" = ? LIMIT 1")
    Db.bind_int(stmt, 1, @id)
    if Db.step?(stmt)
      @id = Db.column_int(stmt, 0)
      @articles = Db.column_text_opt(stmt, 1)
      @__t_completed_at = nil
      @completed_at_raw = Db.column_text_opt(stmt, 2)
      @__t_created_at = nil
      @created_at_raw = Db.column_text(stmt, 3)
      @status = Db.column_text(stmt, 4)
      @__t_updated_at = nil
      @updated_at_raw = Db.column_text(stmt, 5)
      @user_id = Db.column_int(stmt, 6)
      self.mark_persisted!
    end
    Db.finalize(stmt)
    self
  end

  def self._columns_sql
    "\"article_exports\".\"id\" AS \"id\", \"article_exports\".\"articles\" AS \"articles\", \"article_exports\".\"completed_at\" AS \"completed_at\", \"article_exports\".\"created_at\" AS \"created_at\", \"article_exports\".\"status\" AS \"status\", \"article_exports\".\"updated_at\" AS \"updated_at\", \"article_exports\".\"user_id\" AS \"user_id\""
  end

  def self._hydrate_all(sql)
    stmt = Db.prepare(sql)
    begin
      results = []
      while Db.step?(stmt)
        results << ArticleExport.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

#<SPINEL_SOURCE>app/app/models/article_export.rb:2
  def validate
    if @user_id.nil? || @user_id == 0 || !(User.exists?(@user_id))
      self.errors << "User must exist"
      self.error_details << ActiveRecord::ErrorDetail.new("user", "blank", "must exist", "User must exist", true, true)
    end
  end

  def user
    return @user_cache if @user_loaded
    @user_cache = if @user_id == 0
      nil
    else
      stmt = Db.prepare("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @user_id.to_s, 8) + " LIMIT 1")
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
    @user_loaded = true
    @user_cache
  end

  def user=(value)
    @user_loaded = false
    if value.nil?
      @user_id = 0
    else
      @user_id = value.id
      @user_cache = value
      @user_loaded = true
    end
  end

  def user_loaded?
    @user_loaded
  end

#<SPINEL_SOURCE>app/app/models/article_export.rb:1
  def self._association_names
    [:user]
  end

#<SPINEL_SOURCE>app/app/models/article_export.rb:4
  def self.recover_pending!
#<SPINEL_SOURCE>app/app/models/article_export.rb:6
    stmt = Db.prepare("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\" WHERE \"status\" = 'pending'")
    begin
      results = []
      while Db.step?(stmt)
        results << ArticleExport.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results.each { |export| ExportArticlesJob.perform_later(export.id) }
  end

#<SPINEL_SOURCE>app/app/models/article_export.rb:1
  def dom_prefix
    "article_export"
  end

  def to_param
    @id.to_s
  end

  def dom_record_key
    @id.to_s
  end

  def cache_key
    if self.persisted?
      "article_exports/#{@id}"
    else
      "article_exports/new"
    end
  end

  def cache_key_with_version
    if self.persisted?
      "article_exports/#{@id}-#{@updated_at_raw}"
    else
      "article_exports/new-#{@updated_at_raw}"
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
    GlobalID.param("ArticleExport", self.id)
  end

  def to_gid_uri
    GlobalID.uri("ArticleExport", self.id)
  end

  def _autosave_user
    if @user_loaded && @user_id == 0 && !(@user_cache.nil?)
      @user_cache.save
      @user_id = @user_cache.id
    end
  end

  def before_validation
    _autosave_user
  end

  def self._preload_batch_user(records)
    ids = []
    records.each do |r|
      v = r.user_id
      if v.nil? || v == 0
        nil
      else
        ids << v
      end
    end
    ids.uniq!
    by_id = {}
    User._hydrate_all("SELECT " + User._columns_sql + " FROM users WHERE users.id IN (" + Db.escape_int_list(ids) + ")").each do |rec| by_id[rec.id] = rec end if ids.length > 0
    records.each do |r| r._preload_user(by_id[r.user_id]) end
    by_id.values
  end

  def _preload_user(rec)
    @user_cache = rec
    @user_loaded = true
    nil
  end

  def self._preload_dispatch(records, name, nested)
    case name
    when :user
      loaded = _preload_batch_user(records)
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
