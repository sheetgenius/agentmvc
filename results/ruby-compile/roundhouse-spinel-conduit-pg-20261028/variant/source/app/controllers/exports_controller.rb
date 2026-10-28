class ExportsController < ApplicationController
  def create
    require_user!
    export = @current_user.article_exports.create!
    ExportArticlesJob.perform_later(export.id)
    render json: { export: export_json(export) }, status: :accepted
  end
  def show
    require_user!
    # Roundhouse association find_by still derives current_user_id from the ivar name.
    export = ArticleExport.find_by(id: param(:id), user_id: @current_user.id)
    raise Failure.new(404, :export, "not found") unless export
    render json: { export: export_json(export) }
  end
  private
  def export_json(export)
    { id: export.id, status: export.status, createdAt: export.created_at.iso8601(3),
      completedAt: export.completed_at&.iso8601(3), articles: export.articles }
  end
end
