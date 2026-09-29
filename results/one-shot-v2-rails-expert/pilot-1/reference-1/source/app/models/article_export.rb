class ArticleExport < ApplicationRecord
  belongs_to :user

  def self.recover_pending!
    where(status: "pending").find_each { |export| ExportArticlesJob.perform_later(export.id) }
  end
end
