//go:build tools

// Package tooling keeps optional prepared libraries pinned before product code uses them.
package tooling

import (
	_ "github.com/coder/websocket"
	_ "github.com/golang-jwt/jwt/v5"
	_ "golang.org/x/crypto/bcrypt"
)
