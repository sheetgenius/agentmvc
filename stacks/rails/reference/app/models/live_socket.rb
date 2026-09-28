require "websocket/driver"

class LiveSocket
  attr_reader :env, :url

  def initialize(env, id)
    @env = env
    @id = id
    @url = "ws://#{env['HTTP_HOST']}#{env['REQUEST_URI']}"
    @driver = WebSocket::Driver.rack(self)
    @write_lock = Mutex.new
    @driver.on(:message) { |event| subscribe(event.data) }
    @driver.on(:close) { LiveRooms.leave(self, @id) }
  end

  def start
    env["rack.hijack"].call
    @io = env["rack.hijack_io"]
    @driver.start
    Thread.new do
      begin
        until @subscribed
          break unless IO.select([ @io ], nil, nil, 5)
          @driver.parse(@io.readpartial(4096))
        end
        unless @subscribed
          terminate("invalid_link")
          next
        end
        @driver.parse(@io.readpartial(4096)) while true
      rescue EOFError, IOError, Errno::ECONNRESET
        # The room is released when the peer disconnects.
      ensure
        LiveRooms.leave(self, @id)
        @io.close unless @io.closed?
      end
    end
  end

  def write(bytes)
    @write_lock.synchronize { @io.write(bytes) }
  rescue IOError, Errno::EPIPE
    nil
  end

  def send_message(message)
    @driver.text(message.to_json)
  end

  def terminate(type)
    send_message(type: type)
    @driver.close
  end

  private

  def subscribe(data)
    return if @subscribed
    message = JSON.parse(data)
    share = Share.authorized(@id, message["key"]) if message["type"] == "subscribe"
    unless share
      terminate("invalid_link")
      return
    end
    @subscribed = true
    unless LiveRooms.join(self, share)
      send_message(type: "room_full", limit: 100)
      @driver.close
    end
  rescue JSON::ParserError
    terminate("invalid_link")
  end
end
