require_relative "application_record"
require_relative "../../runtime/gem_facades"

class User < ApplicationRecord
#<SPINEL_SOURCE>app/app/models/user.rb:1
  def id
    @id
  end

  def id=(value)
    @id = value
  end

  def bio
    @bio
  end

  def bio=(value)
    @bio = value
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

  def email
    @email
  end

  def email=(value)
    @email = value
  end

  def image
    @image
  end

  def image=(value)
    @image = value
  end

  def password_digest
    @password_digest
  end

  def password_digest=(value)
    @password_digest = value
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

  def username
    @username
  end

  def username=(value)
    @username = value
  end

  def self.table_name
    "users"
  end

  def self._table_sql
    "\"users\""
  end

  def self.schema_columns
    [:id, :bio, :created_at, :email, :image, :password_digest, :updated_at, :username]
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
    { "article_exports.id" => 8, "article_exports.user_id" => 8, "article_shares.article_id" => 8, "articles.id" => 8, "articles.author_id" => 8, "articles.revision" => 4, "comments.id" => 8, "comments.article_id" => 8, "comments.author_id" => 8, "favorites.article_id" => 8, "favorites.user_id" => 8, "follows.followed_id" => 8, "follows.follower_id" => 8, "good_job_batches.callback_priority" => 4, "good_job_executions.error_event" => 4, "good_job_processes.lock_type" => 4, "good_jobs.error_event" => 4, "good_jobs.executions_count" => 4, "good_jobs.lock_type" => 4, "good_jobs.priority" => 4, "users.id" => 8, "id" => 8 }
  end

  def self.instantiate(row)
    instance = User.from_row(UserRow.from_raw(row))
    instance.mark_persisted!
    instance._note_projection(row)
    instance
  end

  def self.from_row(row)
    instance = User.new
    instance.id = row.id
    instance.bio = row.bio&.to_s
    instance.created_at_raw = row.created_at
    instance.email = row.email
    instance.image = row.image&.to_s
    instance.password_digest = row.password_digest
    instance.updated_at_raw = row.updated_at
    instance.username = row.username
    instance._note_hydrated
    instance
  end

  def self.from_stmt(stmt)
    instance = User.new
    instance.id = Db.column_int(stmt, 0)
    instance.bio = Db.column_text_opt(stmt, 1)
    instance.created_at_raw = Db.column_text(stmt, 2)
    instance.email = Db.column_text(stmt, 3)
    instance.image = Db.column_text_opt(stmt, 4)
    instance.password_digest = Db.column_text(stmt, 5)
    instance.updated_at_raw = Db.column_text(stmt, 6)
    instance.username = Db.column_text(stmt, 7)
    instance.mark_persisted!
    instance._note_hydrated
    instance
  end

  def initialize(attrs = ActiveRecord::Base::EMPTY_ATTRS)
    super()
    self.id = (attrs[:id] || 0).to_i
    self.bio = attrs[:bio]&.to_s
    self.created_at_raw = attrs[:created_at] || ""
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if !(attrs[:created_at].nil?)
    self.email = (attrs[:email] || "").to_s
    self.image = attrs[:image]&.to_s
    self.password_digest = (attrs[:password_digest] || "").to_s
    self.updated_at_raw = attrs[:updated_at] || ""
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if !(attrs[:updated_at].nil?)
    self.username = (attrs[:username] || "").to_s
    self.password = attrs[:password] if attrs.key? :password
    self.password_confirmation = attrs[:password_confirmation] if attrs.key? :password_confirmation
    @articles_cache = nil
    @articles_loaded = false
    @article_exports_cache = nil
    @article_exports_loaded = false
  end
  private :initialize

  def attributes
    { "bio" => @bio, "created_at" => @created_at_raw, "email" => @email, "image" => @image, "password_digest" => @password_digest, "updated_at" => @updated_at_raw, "username" => @username }
  end

  def [](name)
    case name.to_sym
    when :id
      @id
    when :bio
      @bio&.to_s
    when :created_at
      @created_at_raw
    when :email
      @email
    when :image
      @image&.to_s
    when :password_digest
      @password_digest
    when :updated_at
      @updated_at_raw
    when :username
      @username
    else
      _projection_attribute name.to_s
    end
  end

  def []=(name, value)
    case name
    when :id
      @id = (value).to_i
    when :bio
      @bio = value&.to_s
    when :created_at
      self.created_at_raw = ActiveSupport.format_db_time(value)
    when :email
      @email = (value).to_s
    when :image
      @image = value&.to_s
    when :password_digest
      @password_digest = (value).to_s
    when :updated_at
      self.updated_at_raw = ActiveSupport.format_db_time(value)
    when :username
      @username = (value).to_s
    end
  end

  def update(attrs)
    self.bio = attrs[:bio]&.to_s if attrs.key?(:bio)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.email = (attrs[:email]).to_s if attrs.key?(:email)
    self.image = attrs[:image]&.to_s if attrs.key?(:image)
    self.password_digest = (attrs[:password_digest]).to_s if attrs.key?(:password_digest)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.username = (attrs[:username]).to_s if attrs.key?(:username)
    self.password = attrs[:password] if attrs.key?(:password)
    self.password_confirmation = attrs[:password_confirmation] if attrs.key?(:password_confirmation)
    self.save
  end

  def update!(attrs)
    self.bio = attrs[:bio]&.to_s if attrs.key?(:bio)
    self.created_at_raw = (attrs[:created_at]).to_s if attrs.key?(:created_at)
    self.created_at_raw = ActiveSupport.format_db_time(attrs[:created_at]) if attrs.key?(:created_at)
    self.email = (attrs[:email]).to_s if attrs.key?(:email)
    self.image = attrs[:image]&.to_s if attrs.key?(:image)
    self.password_digest = (attrs[:password_digest]).to_s if attrs.key?(:password_digest)
    self.updated_at_raw = (attrs[:updated_at]).to_s if attrs.key?(:updated_at)
    self.updated_at_raw = ActiveSupport.format_db_time(attrs[:updated_at]) if attrs.key?(:updated_at)
    self.username = (attrs[:username]).to_s if attrs.key?(:username)
    self.password = attrs[:password] if attrs.key?(:password)
    self.password_confirmation = attrs[:password_confirmation] if attrs.key?(:password_confirmation)
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
    stmt = Db.prepare("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
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

  def self._adapter_all
    stmt = Db.prepare("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\"")
    begin
      results = []
      while Db.step?(stmt)
        results << User.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

  def self._adapter_last
    stmt = Db.prepare("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\" ORDER BY \"id\" DESC LIMIT 1")
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

  def _adapter_insert
    Db.insert_returning_int("INSERT INTO \"users\" (\"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\") VALUES (" + Db.escape_string_opt(@bio) + ", " + Db.escape_string(@created_at_raw) + ", " + Db.escape_string(@email) + ", " + Db.escape_string_opt(@image) + ", " + Db.escape_string(@password_digest) + ", " + Db.escape_string(@updated_at_raw) + ", " + Db.escape_string(@username) + ")" + " RETURNING \"id\"")
  end

  def _adapter_update
    Db.exec("UPDATE \"users\" SET \"bio\" = " + Db.escape_string_opt(@bio) + ", \"created_at\" = " + Db.escape_string(@created_at_raw) + ", \"email\" = " + Db.escape_string(@email) + ", \"image\" = " + Db.escape_string_opt(@image) + ", \"password_digest\" = " + Db.escape_string(@password_digest) + ", \"updated_at\" = " + Db.escape_string(@updated_at_raw) + ", \"username\" = " + Db.escape_string(@username) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_touch
    Db.exec("UPDATE \"users\" SET \"updated_at\" = " + Db.escape_string(@updated_at_raw) + " WHERE " + ActiveRecord.integer_query_predicate("\"id\"", @id.to_s, 8))
  end

  def _adapter_delete
    Db.exec("TRUNCATE \"users\" RESTART IDENTITY CASCADE")
  end

  def self._adapter_count
    stmt = Db.prepare("SELECT COUNT(*) FROM \"users\"")
    begin
      Db.step?(stmt)
      result = Db.column_int(stmt, 0)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_any?
    stmt = Db.prepare("SELECT 1 FROM \"users\" LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_exists_by_id?(id)
    stmt = Db.prepare("SELECT 1 FROM \"users\" WHERE " + ActiveRecord.integer_query_predicate("\"id\"", id.to_s, 8) + " LIMIT 1")
    begin
      result = Db.step?(stmt)
    ensure
      Db.finalize(stmt)
    end
    result
  end

  def self._adapter_truncate
    Db.exec("DELETE FROM \"users\"")
  end

  def self.delete_all
    Db.exec("DELETE FROM \"users\"")
    Db.changes
  end

  def _adapter_reload
    @articles_loaded = false
    @article_exports_loaded = false
    stmt = Db.prepare("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\" WHERE \"id\" = ? LIMIT 1")
    begin
      Db.bind_int(stmt, 1, @id)
      if Db.step?(stmt)
        @id = Db.column_int(stmt, 0)
        @bio = Db.column_text_opt(stmt, 1)
        @__t_created_at = nil
        @created_at_raw = Db.column_text(stmt, 2)
        @email = Db.column_text(stmt, 3)
        @image = Db.column_text_opt(stmt, 4)
        @password_digest = Db.column_text(stmt, 5)
        @__t_updated_at = nil
        @updated_at_raw = Db.column_text(stmt, 6)
        @username = Db.column_text(stmt, 7)
        self.mark_persisted!
      end
    ensure
      Db.finalize(stmt)
    end
    self
  end

  def _adapter_reload_lock
    @articles_loaded = false
    @article_exports_loaded = false
    stmt = Db.prepare_locked("SELECT \"id\", \"bio\", \"created_at\", \"email\", \"image\", \"password_digest\", \"updated_at\", \"username\" FROM \"users\" WHERE \"id\" = ? LIMIT 1")
    Db.bind_int(stmt, 1, @id)
    if Db.step?(stmt)
      @id = Db.column_int(stmt, 0)
      @bio = Db.column_text_opt(stmt, 1)
      @__t_created_at = nil
      @created_at_raw = Db.column_text(stmt, 2)
      @email = Db.column_text(stmt, 3)
      @image = Db.column_text_opt(stmt, 4)
      @password_digest = Db.column_text(stmt, 5)
      @__t_updated_at = nil
      @updated_at_raw = Db.column_text(stmt, 6)
      @username = Db.column_text(stmt, 7)
      self.mark_persisted!
    end
    Db.finalize(stmt)
    self
  end

  def self._columns_sql
    "\"users\".\"id\" AS \"id\", \"users\".\"bio\" AS \"bio\", \"users\".\"created_at\" AS \"created_at\", \"users\".\"email\" AS \"email\", \"users\".\"image\" AS \"image\", \"users\".\"password_digest\" AS \"password_digest\", \"users\".\"updated_at\" AS \"updated_at\", \"users\".\"username\" AS \"username\""
  end

  def self._hydrate_all(sql)
    stmt = Db.prepare(sql)
    begin
      results = []
      while Db.step?(stmt)
        results << User.from_stmt(stmt)
      end
    ensure
      Db.finalize(stmt)
    end
    results
  end

#<SPINEL_SOURCE>app/app/models/user.rb:6
  def validate
    if @username.nil? || @username.empty?
      self.errors << "Username can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("username", "blank", "can't be blank", "Username can't be blank", true, true)
    end
    if @email.nil? || @email.empty?
      self.errors << "Email can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("email", "blank", "can't be blank", "Email can't be blank", true, true)
    end
#<SPINEL_SOURCE>app/app/models/user.rb:7
    if (if @username.nil?
      ActiveRecord::Relation.new(User).where({ username: @username })
    else
      ActiveRecord::Relation.new(User).where("LOWER(users.username) = LOWER(?)", @username)
    end).not(id: @id).exists?
      self.errors << "Username has already been taken"
      self.error_details << ActiveRecord::ErrorDetail.new("username", "taken", "has already been taken", "Username has already been taken", true, false)
    end
#<SPINEL_SOURCE>app/app/models/user.rb:8
    if (if @email.nil?
      ActiveRecord::Relation.new(User).where({ email: @email })
    else
      ActiveRecord::Relation.new(User).where("LOWER(users.email) = LOWER(?)", @email)
    end).not(id: @id).exists?
      self.errors << "Email has already been taken"
      self.error_details << ActiveRecord::ErrorDetail.new("email", "taken", "has already been taken", "Email has already been taken", true, false)
    end
#<SPINEL_SOURCE>app/app/models/user.rb:9
    password_has_minimum_length
#<SPINEL_SOURCE>app/app/models/user.rb:10
    password_is_present_when_supplied
#<SPINEL_SOURCE>app/app/models/user.rb:1
    if @password_digest.nil? || @password_digest.empty?
      self.errors << "Password can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("password", "blank", "can't be blank", "Password can't be blank", true, true)
    end
    if !(@password.nil? || @password.empty?) && @password.bytesize > 72
      self.errors << "Password is too long"
      self.error_details << ActiveRecord::ErrorDetail.new("password", "password_too_long", "is too long", "Password is too long", true, true)
    end
    if !(@password.nil? || @password.empty?) && !(@password_confirmation.nil?) && @password_confirmation != @password
      self.errors << "Password confirmation doesn't match Password"
      self.error_details << ActiveRecord::ErrorDetail.new("password_confirmation", "confirmation", "doesn't match Password", "Password confirmation doesn't match Password", true, false)
    end
  end

#<SPINEL_SOURCE>app/app/models/user.rb:4
  def articles
    return __articles_cache if @articles_loaded
    stmt = Db.prepare("SELECT \"id\", \"author_id\", \"body\", \"created_at\", \"description\", \"published_at\", \"revision\", \"slug\", \"status\", \"tag_list\", \"title\", \"updated_at\" FROM \"articles\" WHERE " + ActiveRecord.integer_query_predicate("\"author_id\"", @id.to_s, 8))
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

  def _preload_articles(list)
    @articles_cache = list
    @articles_loaded = true
  end

  def articles_loaded?
    @articles_loaded
  end

  def reload_articles
    @articles_loaded = false
    self.articles
  end

  def articles_target
    __articles_cache
  end

  def article_ids
    self.articles.map { |rh_id_record| rh_id_record.id }
  end

#<SPINEL_SOURCE>app/app/models/user.rb:5
  def article_exports
    return __article_exports_cache if @article_exports_loaded
    stmt = Db.prepare("SELECT \"id\", \"articles\", \"completed_at\", \"created_at\", \"status\", \"updated_at\", \"user_id\" FROM \"article_exports\" WHERE " + ActiveRecord.integer_query_predicate("\"user_id\"", @id.to_s, 8))
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

  def _preload_article_exports(list)
    @article_exports_cache = list
    @article_exports_loaded = true
  end

  def article_exports_loaded?
    @article_exports_loaded
  end

  def reload_article_exports
    @article_exports_loaded = false
    self.article_exports
  end

  def article_exports_target
    __article_exports_cache
  end

  def article_export_ids
    self.article_exports.map { |rh_id_record| rh_id_record.id }
  end

#<SPINEL_SOURCE>app/app/models/user.rb:1
  def self._association_names
    [:articles, :article_exports]
  end

#<SPINEL_SOURCE>app/app/models/user.rb:4
  def before_destroy
    self.articles.each { |c| c.destroy }
#<SPINEL_SOURCE>app/app/models/user.rb:5
    self.article_exports.each { |c| c.destroy }
  end

#<SPINEL_SOURCE>app/app/models/user.rb:1
  def authenticate(unencrypted_password)
    if BCrypt::Password.new(@password_digest) == unencrypted_password
      self
    else
      false
    end
  end

  def password
    @password
  end

  def password_confirmation
    @password_confirmation
  end

  def password_confirmation=(value)
    @password_confirmation = value
  end

  def password_reset_token
    ActiveRecord::TokenFor.generate(ActiveRecord::TokenFor.secure_password_data(self.id, @password_digest), "User\\npassword_reset\\n900", 900)
  end

  def password_reset_token_expires_in
    900
  end

  def self.find_by_password_reset_token(token)
    data = ActiveRecord::TokenFor.verified_data(token, "User\\npassword_reset\\n900")
    record = find_by({ id: ActiveRecord::TokenFor.data_id(data) })
    if record.nil?
      nil
    else
      record if ActiveRecord::TokenFor.secure_password_data(record.id, record.password_digest) == data
    end
  end

  def self.find_by_password_reset_token!(token)
    data = ActiveRecord::TokenFor.verified_data(token, "User\\npassword_reset\\n900")
    raise ActiveSupport::MessageVerifier::InvalidSignature if data == ""
    record = find(ActiveRecord::TokenFor.data_id(data))
    if ActiveRecord::TokenFor.secure_password_data(record.id, record.password_digest) == data
      nil
    else
      raise ActiveSupport::MessageVerifier::InvalidSignature
    end
    record
  end

#<SPINEL_SOURCE>app/app/models/user.rb:12
  def normalize_optional_fields
#<SPINEL_SOURCE>app/app/models/user.rb:13
    self.bio = nil if self.bio == ""
#<SPINEL_SOURCE>app/app/models/user.rb:14
    self.image = nil if self.image == ""
  end

#<SPINEL_SOURCE>app/app/models/user.rb:18
  def password_has_minimum_length
#<SPINEL_SOURCE>app/app/models/user.rb:19
    if ActiveSupport.present?(self.password) && self.password.length < 8
      self.errors << "Password is too short (minimum is 8 characters)"
      self.error_details << ActiveRecord::ErrorDetail.new("password", "is too short (minimum is 8 characters)", "is too short (minimum is 8 characters)", "Password is too short (minimum is 8 characters)", false, true)
    end
  end

#<SPINEL_SOURCE>app/app/models/user.rb:22
  def password_is_present_when_supplied
#<SPINEL_SOURCE>app/app/models/user.rb:23
    if @password_supplied && ActiveSupport.blank?(self.password)
      self.errors << "Password can't be blank"
      self.error_details << ActiveRecord::ErrorDetail.new("password", "can't be blank", "can't be blank", "Password can't be blank", false, true)
    end
  end

#<SPINEL_SOURCE>app/app/models/user.rb:26
  def password=(value)
#<SPINEL_SOURCE>app/app/models/user.rb:27
    @password_supplied = true
#<SPINEL_SOURCE>app/app/models/user.rb:28
    _secure_password_writer(value)
  end

#<SPINEL_SOURCE>app/app/models/user.rb:1
  def _secure_password_writer(unencrypted_password)
    @password = unencrypted_password
    if unencrypted_password.nil?
      nil
    else
      @password_digest = BCrypt::Password.create(unencrypted_password).to_s
    end
  end

  def dom_prefix
    "user"
  end

  def to_param
    @id.to_s
  end

  def dom_record_key
    @id.to_s
  end

  def cache_key
    if self.persisted?
      "users/#{@id}"
    else
      "users/new"
    end
  end

  def cache_key_with_version
    if self.persisted?
      "users/#{@id}-#{@updated_at_raw}"
    else
      "users/new-#{@updated_at_raw}"
    end
  end

#<SPINEL_SOURCE>app/app/models/user.rb:2
  def before_validation
    normalize_optional_fields
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
    GlobalID.param("User", self.id)
  end

  def to_gid_uri
    GlobalID.uri("User", self.id)
  end

  def self._preload_batch_articles(records)
    ids = []
    records.each do |r| ids << r.id end
    loaded = []
    loaded = ActiveRecord::Relation.new(Article).where(author_id: ids).to_a if ids.length > 0
    grouped = {}
    loaded.each do |rec|
      k = rec.author_id
      grouped[k] = [] if grouped[k].nil?
      grouped[k] << rec
    end
    records.each do |r| r._preload_articles(grouped[r.id] || []) end
    loaded
  end

  def self._preload_batch_article_exports(records)
    ids = []
    records.each do |r| ids << r.id end
    loaded = []
    loaded = ActiveRecord::Relation.new(ArticleExport).where(user_id: ids).to_a if ids.length > 0
    grouped = {}
    loaded.each do |rec|
      k = rec.user_id
      grouped[k] = [] if grouped[k].nil?
      grouped[k] << rec
    end
    records.each do |r| r._preload_article_exports(grouped[r.id] || []) end
    loaded
  end

  def self._preload_dispatch(records, name, nested)
    case name
    when :articles
      loaded = _preload_batch_articles(records)
      if nested.nil?
        nil
      else
        Article.preload_associations(loaded, [nested])
      end
    when :article_exports
      loaded = _preload_batch_article_exports(records)
      if nested.nil?
        nil
      else
        ArticleExport.preload_associations(loaded, [nested])
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

  def __articles_cache
    c = @articles_cache
    if c.nil?
      c = []
      @articles_cache = c
    end
    c
  end

  def __article_exports_cache
    c = @article_exports_cache
    if c.nil?
      c = []
      @article_exports_cache = c
    end
    c
  end
end
