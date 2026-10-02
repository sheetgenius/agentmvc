class ArticleExport < ApplicationRecord
  belongs_to :user

  def self.recover_pending!
    # Roundhouse folds this model-class query to an Array before find_each dispatch.
    where(status: "pending").each { |export| ExportArticlesJob.perform_later(export.id) }
  end
end
