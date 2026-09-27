require_relative "config/environment"
require_relative "app/services/share_socket"
use ShareSocket
run Rails.application
Rails.application.load_server
