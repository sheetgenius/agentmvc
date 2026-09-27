class BuildExportJob < ApplicationJob
  def perform(export)
    export.build!
  end
end
