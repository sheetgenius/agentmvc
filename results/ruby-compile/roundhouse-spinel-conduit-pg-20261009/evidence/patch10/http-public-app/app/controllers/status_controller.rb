class StatusController < ApplicationController
  def code
    202
  end
  def show
    head code
  end
end
