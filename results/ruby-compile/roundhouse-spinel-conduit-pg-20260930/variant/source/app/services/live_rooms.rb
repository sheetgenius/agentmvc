class LiveRooms
  # Spinel Struct#members collides with the room member field.
  class Room
    attr_reader :lock, :members
    def initialize
      @lock = Mutex.new
      # A nil key seeds Spinel's boxed-key hash representation.
      @members = { nil => 0 }
      @members.delete(nil)
    end
  end

  def self.room(id)
    state = Rails.application.config.x.live_rooms_state
    state[:lock].synchronize { state[:rooms][id] ||= Room.new }
  end

  def self.join(share, socket)
    room = room(share.id)
    room.lock.synchronize do
      return nil unless share.reload.revoked_at.nil?
      return :full if room.members.length >= 100
      article = share.article.reload.shared_json
      room.members[socket] = article[:revision]
      send_json(socket, type: "ready", article: article, presence: room.members.length)
      broadcast(room, type: "presence", count: room.members.length)
    end
    room
  end

  def self.leave(room, socket)
    return unless room
    room.lock.synchronize do
      if room.members.delete(socket)
        broadcast(room, type: "presence", count: room.members.length)
      end
    end
  end

  def self.updated(article)
    article.article_shares.active.pluck(:id).each do |id|
      room = room(id)
      room.lock.synchronize do
        room.members.each do |socket, revision|
          next if revision >= article.revision
          send_json(socket, type: "updated", article: article.shared_json)
          room.members[socket] = article.revision
        end
      end
    end
  end

  def self.revoked(ids)
    ids.each do |id|
      room = room(id)
      room.lock.synchronize do
        room.members.each_key do |socket|
          EventMachine.schedule do
            socket.send(JSON.generate(type: "revoked"))
            socket.close
          end
        end
        room.members.clear
      end
    end
  end

  def self.broadcast(room, message)
    room.members.each_key { |socket| send_json(socket, message) }
  end

  def self.send_json(socket, message)
    payload = JSON.generate(message)
    EventMachine.schedule { socket.send(payload) }
  rescue StandardError
    EventMachine.schedule { socket.close }
  end
end
