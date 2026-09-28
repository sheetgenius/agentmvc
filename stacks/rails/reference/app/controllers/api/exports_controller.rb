module Api
  class ExportsController < ApplicationController
    before_action :authenticate_user!

    def create
      export = current_user.exports.create!
      ExportJob.perform_later(export)
      render json: { export: present(export) }, status: :accepted
    end

    def show
      export = current_user.exports.find_by(id: params[:id].to_s[/\A\d+\z/])
      return render_error(:export, "not found", :not_found) unless export
      render json: { export: present(export) }
    end

    private

    def present(export)
      { id: export.id, status: export.status, createdAt: export.created_at, completedAt: export.completed_at, articles: export.articles }
    end
  end
end
