# Mechanism reduced from the two actual Roundhouse runtime method bodies.
# The original generated keyless join model inherits a raising id= writer.
class Keyless
  def self.schema_columns = [:owner_id]
  def self.primary_key = "id"
  def id=(_value)
    raise NotImplementedError, "id=: subclasses must override"
  end
  def _adapter_insert = 0
  def save_after_validation
    key = _adapter_insert
    self.id = key if self.class.schema_columns.include?(self.class.primary_key.to_sym)
    true
  end
end
puts Keyless.new.save_after_validation # v10's guarded base: true
class Keyless
  def save_after_validation
    self.id = _adapter_insert # #1295's Ruby overlay bypasses the base guard
    true
  end
end
puts Keyless.new.save_after_validation # NotImplementedError
