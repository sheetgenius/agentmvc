package conduit

import (
	"context"
	"crypto/sha256"
	"crypto/subtle"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"sync"
	"time"

	"github.com/coder/websocket"
	"github.com/go-chi/chi/v5"
)

type sharedArticleView struct {
	Slug     string `json:"slug"`
	Title    string `json:"title"`
	Body     string `json:"body"`
	Revision int    `json:"revision"`
}

func sharedView(v ArticleView) sharedArticleView {
	return sharedArticleView{v.Slug, v.Title, v.Body, v.Revision}
}
func (a *App) validShare(ctx context.Context, id, key string) (int64, error) {
	var articleID int64
	var hash []byte
	err := a.DB.DB.QueryRowContext(ctx, "SELECT article_id,key_hash FROM shares WHERE id=$1", id).Scan(&articleID, &hash)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return 0, fail(404, "share", "not found")
		}
		return 0, err
	}
	got := sha256.Sum256([]byte(key))
	if key == "" || subtle.ConstantTimeCompare(hash, got[:]) != 1 {
		return 0, fail(404, "share", "not found")
	}
	return articleID, nil
}
func (a *App) share(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	if err = own(x, viewer); err != nil {
		return err
	}
	a.rooms.mu.Lock()
	defer a.rooms.mu.Unlock()
	tx, err := a.DB.BeginTx(r.Context(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var old string
	_ = tx.Tx.QueryRowContext(r.Context(), "SELECT id FROM shares WHERE article_id=$1", x.ID).Scan(&old)
	if _, err = tx.Tx.ExecContext(r.Context(), "DELETE FROM shares WHERE article_id=$1", x.ID); err != nil {
		return err
	}
	if r.Method == "DELETE" {
		if err = tx.Commit(); err != nil {
			return err
		}
		if old != "" {
			a.rooms.revokeLocked(old)
		}
		send(w, 204, nil)
		return nil
	}
	id, key := randomURL(18), randomURL(32)
	sum := sha256.Sum256([]byte(key))
	_, err = tx.Tx.ExecContext(r.Context(), "INSERT INTO shares(id,article_id,key_hash) VALUES($1,$2,$3)", id, x.ID, sum[:])
	if err != nil {
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	if old != "" {
		a.rooms.revokeLocked(old)
	}
	send(w, 201, map[string]any{"share": map[string]string{"id": id, "key": key}})
	return nil
}
func (a *App) sharedArticle(w http.ResponseWriter, r *http.Request) error {
	id, key := chi.URLParam(r, "id"), r.Header.Get("X-Share-Key")
	articleID, err := a.validShare(r.Context(), id, key)
	if err != nil {
		return err
	}
	if r.Method == "GET" {
		v, err := a.viewArticle(r.Context(), articleID, 0, true)
		if err != nil {
			return err
		}
		send(w, 200, map[string]any{"article": sharedView(v)})
		return nil
	}
	obj, err := decodeShared(r)
	if err != nil {
		return err
	}
	revision, present, err := integer(obj, "revision")
	if err != nil {
		return err
	}
	if !present {
		return bad("revision")
	}
	v, err := a.saveArticle(r.Context(), articleID, 0, obj, true, revision, true, id, key)
	if err != nil {
		return err
	}
	send(w, 200, map[string]any{"article": sharedView(v)})
	return nil
}

type liveMessage struct {
	Type     string             `json:"type"`
	Article  *sharedArticleView `json:"article,omitempty"`
	Presence int                `json:"presence,omitempty"`
	Count    int                `json:"count,omitempty"`
	Limit    int                `json:"limit,omitempty"`
}
type liveClient struct {
	shareID string
	send    chan liveMessage
	done    chan struct{}
	last    int
	once    sync.Once
}

func (c *liveClient) close() { c.once.Do(func() { close(c.done) }) }

type room struct{ members map[*liveClient]bool }
type rooms struct {
	mu        sync.Mutex
	byArticle map[int64]*room
}

func newRooms() *rooms { return &rooms{byArticle: map[int64]*room{}} }
func (m *rooms) roomLocked(id int64) *room {
	r := m.byArticle[id]
	if r == nil {
		r = &room{members: map[*liveClient]bool{}}
		m.byArticle[id] = r
	}
	return r
}
func (m *rooms) sendLocked(c *liveClient, msg liveMessage) {
	select {
	case c.send <- msg:
	default:
		c.close()
	}
}
func (m *rooms) updatedLocked(id int64, v sharedArticleView) {
	if r := m.byArticle[id]; r != nil {
		for c := range r.members {
			if v.Revision > c.last {
				c.last = v.Revision
				m.sendLocked(c, liveMessage{Type: "updated", Article: &v})
			}
		}
	}
}
func (m *rooms) revokeLocked(shareID string) {
	for _, r := range m.byArticle {
		for c := range r.members {
			if c.shareID == shareID {
				m.sendLocked(c, liveMessage{Type: "revoked"})
				c.close()
				delete(r.members, c)
			}
		}
	}
}
func (m *rooms) revokeArticle(id int64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if r := m.byArticle[id]; r != nil {
		for c := range r.members {
			m.sendLocked(c, liveMessage{Type: "revoked"})
			c.close()
		}
		delete(m.byArticle, id)
	}
}
func (m *rooms) leave(id int64, c *liveClient) {
	m.mu.Lock()
	defer m.mu.Unlock()
	r := m.byArticle[id]
	if r == nil || !r.members[c] {
		return
	}
	delete(r.members, c)
	c.close()
	for other := range r.members {
		m.sendLocked(other, liveMessage{Type: "presence", Count: len(r.members)})
	}
	if len(r.members) == 0 {
		delete(m.byArticle, id)
	}
}
func (a *App) live(w http.ResponseWriter, r *http.Request) {
	conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{InsecureSkipVerify: true})
	if err != nil {
		return
	}
	defer conn.Close(websocket.StatusNormalClosure, "")
	ctx := context.Background()
	firstCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	_, data, err := conn.Read(firstCtx)
	cancel()
	if err != nil {
		return
	}
	var sub struct {
		Type string `json:"type"`
		Key  string `json:"key"`
	}
	if json.Unmarshal(data, &sub) != nil || sub.Type != "subscribe" {
		_ = conn.Write(ctx, websocket.MessageText, []byte(`{"type":"invalid_link"}`))
		return
	}
	id := chi.URLParam(r, "id")
	a.rooms.mu.Lock()
	articleID, err := a.validShare(ctx, id, sub.Key)
	if err != nil {
		a.rooms.mu.Unlock()
		_ = conn.Write(ctx, websocket.MessageText, []byte(`{"type":"invalid_link"}`))
		return
	}
	room := a.rooms.roomLocked(articleID)
	if len(room.members) >= 100 {
		a.rooms.mu.Unlock()
		_ = conn.Write(ctx, websocket.MessageText, []byte(`{"type":"room_full","limit":100}`))
		return
	}
	v, err := a.viewArticle(ctx, articleID, 0, true)
	if err != nil {
		a.rooms.mu.Unlock()
		return
	}
	c := &liveClient{shareID: id, send: make(chan liveMessage, 32), done: make(chan struct{}), last: v.Revision}
	room.members[c] = true
	sv := sharedView(v)
	a.rooms.sendLocked(c, liveMessage{Type: "ready", Article: &sv, Presence: len(room.members)})
	for other := range room.members {
		if other != c {
			a.rooms.sendLocked(other, liveMessage{Type: "presence", Count: len(room.members)})
		}
	}
	a.rooms.mu.Unlock()
	defer a.rooms.leave(articleID, c)
	writeDone := make(chan struct{})
	go func() {
		defer close(writeDone)
		write := func(msg liveMessage) bool {
			b, _ := json.Marshal(msg)
			writeCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			err := conn.Write(writeCtx, websocket.MessageText, b)
			cancel()
			return err == nil && msg.Type != "revoked"
		}
		for {
			select {
			case msg := <-c.send:
				if !write(msg) {
					return
				}
			case <-c.done:
				for {
					select {
					case msg := <-c.send:
						if !write(msg) {
							return
						}
					default:
						return
					}
				}
			}
		}
	}()
	for {
		readCtx, cancel := context.WithCancel(ctx)
		go func() {
			select {
			case <-c.done:
				cancel()
			case <-readCtx.Done():
			}
		}()
		_, _, err = conn.Read(readCtx)
		cancel()
		if err != nil {
			break
		}
	}
	c.close()
	<-writeDone
}
