require "faye/websocket"

class ShareSocket
  PATH = %r{\A/api/shares/([A-Za-z0-9_-]+)/live\z}

  def initialize(app)
    @app = app
  end

  def call(env)
    id = env["PATH_INFO"].match(PATH)&.captures&.first
    return @app.call(env) unless id && Faye::WebSocket.websocket?(env)

    socket = Faye::WebSocket.new(env, nil, ping: 30, max_length: 4096)
    subscribed = false
    state = Mutex.new
    timeout = Thread.new do
      sleep 4
      state.synchronize do
        unless subscribed
          subscribed = true
          EventMachine.schedule { socket.close }
        end
      end
    end

    socket.on :message do |event|
      state.synchronize do
        next if subscribed

        subscribed = true
        timeout.kill
        message = JSON.parse(event.data) rescue nil
        result = Rails.application.executor.wrap { ShareRoom.join(id, message.is_a?(Hash) && message["type"] == "subscribe" ? message["key"] : nil, socket) }
        case result
        when :invalid
          socket.send({ type: "invalid_link" }.to_json)
          socket.close
        when :full
          socket.send({ type: "room_full", limit: ShareRoom::LIMIT }.to_json)
          socket.close
        end
      end
    end
    socket.on :close do
      timeout.kill
      ShareRoom.leave(id, socket)
    end
    socket.rack_response
  end
end
