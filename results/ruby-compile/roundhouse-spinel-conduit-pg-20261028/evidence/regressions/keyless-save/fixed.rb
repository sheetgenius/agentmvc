class Probe
  def self.schema_columns; [:owner_id]; end
  def self.primary_key; "id"; end
  def id=(_value); raise NotImplementedError, "id=: subclasses must override"; end
  def _adapter_insert; 0; end
  def new_record?; true; end
  def stamps_timestamps?; false; end
  def method_missing(*, &block); block ? block.call : nil; end
    def save_after_validation
      before_save
      was_new = new_record?
      if was_new
        before_create
        fill_timestamps(true)
        inserted_key = _adapter_insert
        self.id = inserted_key if self.class.schema_columns.include?(self.class.primary_key.to_sym)
        @persisted = true
        __track_saved_changes(was_new)
        after_create
      else
        before_update
        fill_timestamps(false)
        _adapter_update
        __track_saved_changes(was_new)
        after_update
      end
      after_save
      # The commit callbacks fire once the save's own callbacks are
      # done, as Rails runs them after the transaction: an
      # `after_update_commit` reads what `after_save` wrote (an
      # attachment, a rich-text body), not the record half saved.
      _save_committed(was_new)
      true
    end
    def save_after_validation
      if _halted_by_abort { before_save }
        @_save_halted = true
        return false
      end
      was_new = new_record?
      if was_new
        if _halted_by_abort { before_create }
          @_save_halted = true
          return false
        end
        fill_timestamps(true)
        inserted_key = _adapter_insert
        self.id = inserted_key if self.class.schema_columns.include?(self.class.primary_key.to_sym)
        @persisted = true
        __track_saved_changes(was_new)
        after_create
      else
        if _halted_by_abort { before_update }
          @_save_halted = true
          return false
        end
        fill_timestamps(false)
        _adapter_update
        __track_saved_changes(was_new)
        after_update
      end
      after_save
      _save_committed(was_new)
      true
    end
end
begin
  puts Probe.new.save_after_validation
rescue NotImplementedError => error
  warn "#{error.class}: #{error.message}"
  exit 1
end
