class LiveRooms
  @lock = Mutex.new
  @rooms = Hash.new { |rooms, id| rooms[id] = [] }

  class << self
    def join(socket, share)
      @lock.synchronize do
        room = @rooms[share.public_id]
        return false if room.size >= 100
        room << socket
        socket.send_message(type: "ready", article: share.article.reload.shared_json, presence: room.size)
        announce(room, room.size, except: socket)
        true
      end
    end

    def leave(socket, id)
      @lock.synchronize do
        room = @rooms[id]
        if room.delete(socket)
          announce(room, room.size)
          @rooms.delete(id) if room.empty?
        end
      end
    end

    def updated(article)
      share = article.share
      return unless share
      @lock.synchronize do
        @rooms[share.public_id].each { |socket| socket.send_message(type: "updated", article: article.shared_json) }
      end
    end

    def revoke(id)
      @lock.synchronize do
        @rooms.delete(id)&.each { |socket| socket.terminate("revoked") }
      end
    end

    private

    def announce(room, count, except: nil)
      room.each { |socket| socket.send_message(type: "presence", count: count) unless socket == except }
    end
  end
end
