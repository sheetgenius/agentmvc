package conduit

import (
	"sync"
	"testing"
	"time"
)

func TestConcurrentLoginAdmission(t *testing.T) {
	var limiter loginLimiter
	now := time.Unix(1000, 0)
	start := make(chan struct{})
	results := make(chan bool, 100)
	var workers sync.WaitGroup
	for i := 0; i < cap(results); i++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			<-start
			attempt := limiter.admit("one@example.test", now)
			results <- attempt != nil
			if attempt != nil {
				limiter.complete("one@example.test", attempt, false)
			}
		}()
	}
	close(start)
	workers.Wait()
	close(results)
	allowed := 0
	for ok := range results {
		if ok {
			allowed++
		}
	}
	if allowed != loginAttemptLimit {
		t.Fatalf("admitted %d concurrent failures; want %d", allowed, loginAttemptLimit)
	}
	if limiter.admit("other@example.test", now) == nil {
		t.Fatal("one account's limit blocked a different account")
	}
}

func TestLoginWindowExpiryAndReset(t *testing.T) {
	var limiter loginLimiter
	now := time.Unix(1000, 0)
	const email = "one@example.test"
	old := limiter.admit(email, now)
	for i := 1; i < loginAttemptLimit; i++ {
		limiter.complete(email, limiter.admit(email, now), false)
	}
	if limiter.admit(email, now.Add(loginWindowDuration-time.Nanosecond)) != nil {
		t.Fatal("window expired early or pending attempt was not counted")
	}
	fresh := limiter.admit(email, now.Add(loginWindowDuration))
	if fresh == nil || fresh == old {
		t.Fatal("expired window did not reopen")
	}
	limiter.complete(email, old, true)
	if limiter.windows[email] != fresh {
		t.Fatal("late completion from an expired window reset the new window")
	}
	limiter.complete(email, fresh, true)
	if _, exists := limiter.windows[email]; exists {
		t.Fatal("successful login did not clear the window")
	}
	if limiter.admit(email, now.Add(loginWindowDuration)) == nil {
		t.Fatal("successful login did not restore admission")
	}
}
