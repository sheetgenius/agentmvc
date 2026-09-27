class ShareRoom
  LIMIT = 100
  Room = Struct.new(:clients, :revision)
  @rooms = {}
  @mutex = Mutex.new

  class << self
    def join(id, key, socket)
      mutex.synchronize do
        share = ArticleShare.authenticate(id, key)
        return :invalid unless share

        room = rooms[id] ||= Room.new([], 0)
        return :full if room.clients.size >= LIMIT

        article = share.article.reload.shared_payload
        room.clients << socket
        room.revision = [ room.revision, article[:revision] ].max
        broadcast([ socket ], type: "ready", article: article, presence: room.clients.size)
        broadcast(room.clients - [ socket ], type: "presence", count: room.clients.size)
        :ready
      end
    end

    def leave(id, socket)
      mutex.synchronize do
        room = rooms[id]
        return unless room&.clients&.delete(socket)

        if room.clients.empty?
          rooms.delete(id)
        else
          broadcast(room.clients, type: "presence", count: room.clients.size)
        end
      end
    end

    def updated(id, article)
      mutex.synchronize do
        room = rooms[id]
        return unless room && article[:revision] > room.revision

        room.revision = article[:revision]
        broadcast(room.clients, type: "updated", article: article)
      end
    end

    def revoke(id)
      clients = mutex.synchronize { rooms.delete(id)&.clients || [] }
      EventMachine.schedule do
        clients.each do |socket|
          socket.send({ type: "revoked" }.to_json)
          socket.close
        end
      end
    end

    private

    def rooms
      @rooms
    end

    def mutex
      @mutex
    end

    def broadcast(clients, message)
      data = message.to_json
      recipients = clients.dup
      EventMachine.schedule { recipients.each { |socket| socket.send(data) } }
    end
  end
end
