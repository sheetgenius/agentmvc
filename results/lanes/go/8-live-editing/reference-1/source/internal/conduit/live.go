package conduit

import (
	"context"
	"encoding/json"
	"net/http"
	"sync"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
	"github.com/go-chi/chi/v5"
)

const roomLimit = 100

type liveRooms struct {
	mu    sync.Mutex
	rooms map[int64]*liveRoom
}

type liveRoom struct {
	mu      sync.Mutex
	clients map[*liveClient]struct{}
}

type liveClient struct {
	conn    *websocket.Conn
	shareID string
	out     chan any
	last    int
}

func newLiveRooms() *liveRooms {
	return &liveRooms{rooms: make(map[int64]*liveRoom)}
}

func (rooms *liveRooms) room(articleID int64) *liveRoom {
	rooms.mu.Lock()
	defer rooms.mu.Unlock()
	room := rooms.rooms[articleID]
	if room == nil {
		room = &liveRoom{clients: make(map[*liveClient]struct{})}
		rooms.rooms[articleID] = room
	}
	return room
}

func (room *liveRoom) send(client *liveClient, message any) {
	select {
	case client.out <- message:
	default:
		// A client that cannot keep up must reconnect for a fresh snapshot.
		go client.conn.CloseNow()
	}
}

func (room *liveRoom) presence() {
	message := map[string]any{"type": "presence", "count": len(room.clients)}
	for client := range room.clients {
		room.send(client, message)
	}
}

// updated is called with the room lock held, after the article commit.
func (room *liveRoom) updated(article SharedArticle) {
	for client := range room.clients {
		if article.Revision > client.last {
			client.last = article.Revision
			room.send(client, map[string]any{"type": "updated", "article": article})
		}
	}
}

// revoke is called with the room lock held, after the share is removed.
func (room *liveRoom) revoke(shareID string) {
	changed := false
	for client := range room.clients {
		if client.shareID == shareID {
			delete(room.clients, client)
			// Older notifications can be discarded once the link is revoked.
		drain:
			for {
				select {
				case <-client.out:
				default:
					break drain
				}
			}
			room.send(client, map[string]any{"type": "revoked"})
			close(client.out)
			changed = true
		}
	}
	if changed {
		room.presence()
	}
}

func (room *liveRoom) leave(client *liveClient) {
	room.mu.Lock()
	defer room.mu.Unlock()
	if _, ok := room.clients[client]; ok {
		delete(room.clients, client)
		close(client.out)
		room.presence()
	}
}

func writeAndClose(conn *websocket.Conn, message any) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	_ = wsjson.Write(ctx, conn, message)
	_ = conn.Close(websocket.StatusNormalClosure, "")
}

func (a *App) liveShare(w http.ResponseWriter, r *http.Request) {
	conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{OriginPatterns: []string{"127.0.0.1:*", "localhost:*"}})
	if err != nil {
		return
	}
	defer conn.CloseNow()
	conn.SetReadLimit(4096)
	ctx, cancel := context.WithTimeout(r.Context(), 4*time.Second)
	_, bytes, err := conn.Read(ctx)
	cancel()
	var subscribe struct {
		Type string `json:"type"`
		Key  string `json:"key"`
	}
	if err != nil {
		return
	}
	if json.Unmarshal(bytes, &subscribe) != nil || subscribe.Type != "subscribe" {
		writeAndClose(conn, map[string]any{"type": "invalid_link"})
		return
	}
	id := chi.URLParam(r, "id")
	share, err := a.share(r.Context(), id, subscribe.Key)
	if err != nil {
		writeAndClose(conn, map[string]any{"type": "invalid_link"})
		return
	}
	room := a.rooms.room(share.ArticleID)
	room.mu.Lock()
	share, err = a.share(r.Context(), id, subscribe.Key)
	if err != nil {
		room.mu.Unlock()
		writeAndClose(conn, map[string]any{"type": "invalid_link"})
		return
	}
	if len(room.clients) >= roomLimit {
		room.mu.Unlock()
		writeAndClose(conn, map[string]any{"type": "room_full", "limit": roomLimit})
		return
	}
	article, err := a.sharedRecord(r.Context(), share)
	if err != nil {
		room.mu.Unlock()
		writeAndClose(conn, map[string]any{"type": "invalid_link"})
		return
	}
	client := &liveClient{conn: conn, shareID: id, out: make(chan any, 256), last: article.Revision}
	room.clients[client] = struct{}{}
	room.send(client, map[string]any{"type": "ready", "article": sharedArticle(article), "presence": len(room.clients)})
	for other := range room.clients {
		if other != client {
			room.send(other, map[string]any{"type": "presence", "count": len(room.clients)})
		}
	}
	room.mu.Unlock()
	go func() {
		for message := range client.out {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			err := wsjson.Write(ctx, conn, message)
			cancel()
			if err != nil {
				_ = conn.CloseNow()
				return
			}
		}
		_ = conn.Close(websocket.StatusNormalClosure, "")
	}()
	defer room.leave(client)
	for {
		if _, _, err := conn.Read(r.Context()); err != nil {
			return
		}
	}
}

func (a *App) broadcastArticle(article *Article) {
	room := a.rooms.room(article.ID)
	room.mu.Lock()
	room.updated(sharedArticle(article))
	room.mu.Unlock()
}
