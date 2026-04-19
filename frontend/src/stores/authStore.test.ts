import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from './authStore'
import type { TokenPair, User } from '../types/auth'

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockUser: User = {
  id: 'usr-1',
  email: 'alice@example.com',
  name: 'Alice',
  settings_json: {},
  created_at: '2026-01-01T00:00:00Z',
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false })
})

describe('authStore — initial state', () => {
  it('has correct initial state', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.tokens).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})

describe('authStore — setTokens', () => {
  it('updates tokens in state and sets isAuthenticated', () => {
    useAuthStore.getState().setTokens(mockTokens)
    const state = useAuthStore.getState()
    expect(state.tokens).toEqual(mockTokens)
    expect(state.isAuthenticated).toBe(true)
  })

  it('persists tokens to localStorage', () => {
    useAuthStore.getState().setTokens(mockTokens)
    const stored = localStorage.getItem('flowday_tokens')
    expect(stored).not.toBeNull()
    expect(JSON.parse(stored!)).toEqual(mockTokens)
  })
})

describe('authStore — setUser', () => {
  it('updates user in state', () => {
    useAuthStore.getState().setUser(mockUser)
    expect(useAuthStore.getState().user).toEqual(mockUser)
  })
})

describe('authStore — logout', () => {
  it('resets all state to initial values', () => {
    useAuthStore.getState().setTokens(mockTokens)
    useAuthStore.getState().setUser(mockUser)
    useAuthStore.getState().logout()
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.tokens).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('removes tokens from localStorage', () => {
    useAuthStore.getState().setTokens(mockTokens)
    useAuthStore.getState().logout()
    expect(localStorage.getItem('flowday_tokens')).toBeNull()
  })
})

describe('authStore — hydrate', () => {
  it('restores tokens from localStorage and sets isAuthenticated', () => {
    localStorage.setItem('flowday_tokens', JSON.stringify(mockTokens))
    useAuthStore.getState().hydrate()
    const state = useAuthStore.getState()
    expect(state.tokens).toEqual(mockTokens)
    expect(state.isAuthenticated).toBe(true)
  })

  it('does nothing when localStorage has no tokens', () => {
    useAuthStore.getState().hydrate()
    const state = useAuthStore.getState()
    expect(state.tokens).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('does nothing when localStorage has invalid JSON', () => {
    localStorage.setItem('flowday_tokens', 'not-json')
    useAuthStore.getState().hydrate()
    expect(useAuthStore.getState().tokens).toBeNull()
  })
})

describe('authStore — login (convenience)', () => {
  it('sets user, tokens, and isAuthenticated in one call', () => {
    useAuthStore.getState().login(mockUser, mockTokens)
    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.tokens).toEqual(mockTokens)
    expect(state.isAuthenticated).toBe(true)
  })
})
