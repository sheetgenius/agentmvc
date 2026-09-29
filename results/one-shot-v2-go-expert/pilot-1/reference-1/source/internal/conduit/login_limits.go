package conduit

import (
	"sync"
	"time"
)

const loginAttemptLimit = 20
const loginWindowDuration = 15 * time.Minute

type loginWindow struct {
	failures, pending int
	expires           time.Time
}

type loginLimiter struct {
	mu      sync.Mutex
	windows map[string]*loginWindow
}

// Reserve before checking the password so concurrent requests cannot all pass
// the same remaining allowance. A successful login resets its window.
func (l *loginLimiter) admit(email string, now time.Time) *loginWindow {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.windows == nil {
		l.windows = make(map[string]*loginWindow)
	}
	w := l.windows[email]
	if w == nil || !now.Before(w.expires) {
		w = &loginWindow{expires: now.Add(loginWindowDuration)}
		l.windows[email] = w
	}
	if w.failures+w.pending >= loginAttemptLimit {
		return nil
	}
	w.pending++
	return w
}

func (l *loginLimiter) complete(email string, w *loginWindow, success bool) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.windows[email] != w {
		return // An expired or reset window cannot change its replacement.
	}
	w.pending--
	if success {
		delete(l.windows, email)
	} else {
		w.failures++
	}
}
