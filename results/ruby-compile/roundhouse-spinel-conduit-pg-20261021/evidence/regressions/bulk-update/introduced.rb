module ActiveRecord
  def self.adapter; Adapter.new; end
end
class Adapter
  def escape_value(value); value.to_s; end
  def execute_ddl(sql); puts sql; end
  def changes; 1; end
end
class Relation
  def initialize; @null = false; @table = '"widgets"'; end
  def scoped_write_where; " WHERE id = 1"; end
    def update_all(updates)
      return 0 if @null
      set_sql = if updates.is_a?(Hash)
        parts = []
        updates.each do |key, val|
          parts.push("#{key} = #{ActiveRecord.adapter.escape_value(val)}")
        end
        parts.join(", ")
      else
        updates.to_s
      end
      # The table quoted, as Rails' Arel renders it (`UPDATE "memberships"
      # SET ...`): a test that picks the statement out of the SQL log
      # (campfire's creation-commit test) matches that spelling.
      sql = "UPDATE \"#{@table}\" SET #{set_sql}#{scoped_write_where}"
      ActiveRecord.adapter.execute_ddl(sql)
      ActiveRecord.adapter.changes
    end
end
p Relation.new.update_all({"value" => 2})
