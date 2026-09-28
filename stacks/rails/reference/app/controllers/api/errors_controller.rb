module Api
  class ErrorsController < ApplicationController
    def not_found
      render_error(:route, "not found", :not_found)
    end
  end
end
