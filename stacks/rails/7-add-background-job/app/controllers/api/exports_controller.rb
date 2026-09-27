module Api
  class ExportsController < ApplicationController
    before_action :authenticate_user!

    def create
      Export.transaction do
        @export = current_user.exports.create!
        BuildExportJob.perform_later(@export)
      end
      render :show, status: :accepted
    end

    def show
      @export = current_user.exports.find(params[:id])
    end
  end
end
