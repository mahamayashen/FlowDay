import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './authStore'

beforeEach(() => {
  useAuthStore.setState({ user: null, token: null, isAuthenticated: false })
})

describe('authStore', () => {
  it('has correct initial state', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('login sets user token and isAuthenticated', () => {
    const { login } = useAuthStore.getState()
    login({ id: '1', email: 'a@b.com', name: 'Alice' }, 'tok123')
    const state = useAuthStore.getState()
    expect(state.user).toEqual({ id: '1', email: 'a@b.com', name: 'Alice' })
    expect(state.token).toBe('tok123')
    expect(state.isAuthenticated).toBe(true)
  })

  it('logout resets state to initial', () => {
    useAuthStore.getState().login({ id: '1', email: 'a@b.com', name: 'Alice' }, 'tok123')
    useAuthStore.getState().logout()
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
