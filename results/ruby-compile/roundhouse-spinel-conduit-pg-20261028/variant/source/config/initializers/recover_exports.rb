# Roundhouse boot hooks omit the reference bin/rails runner; also recover on Rails server boot.
if defined?(Rails::Server)
  Rails.application.config.after_initialize do
    ArticleExport.recover_pending!
  end
end
