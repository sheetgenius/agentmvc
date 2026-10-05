require "faye/websocket"
class LiveSocket
  def self.open(env, id)
    return [ 400, {}, [] ] unless Faye::WebSocket.websocket?(env)
    socket = Faye::WebSocket.new(env, nil, ping: 30)
    room = nil
    timer = Thread.new do
      sleep 5
      EventMachine.schedule { socket.close } unless room
    end
    socket.on :message do |event|
      next if room
      message = subscription_message(event.data)
      share = ArticleShare.active.find_by(id: id)
      if message["type"] != "subscribe" || !share&.valid_key?(message["key"])
        LiveRooms.send_json(socket, type: "invalid_link")
        socket.close
        next
      end
      result = LiveRooms.join(share, socket)
      if result == :full
        LiveRooms.send_json(socket, type: "room_full", limit: 100)
        socket.close
      elsif result
        room = result
        timer.kill
      else
        LiveRooms.send_json(socket, type: "invalid_link")
        socket.close
      end
    end
    socket.on :close do |_event|
      timer.kill
      LiveRooms.leave(room, socket)
    end
    socket.rack_response
  end

  def self.subscription_message(data)
    message = JSON.parse(data)
    message.is_a?(Hash) ? message : {}
  rescue JSON::ParserError, TypeError
    {}
  end
end
