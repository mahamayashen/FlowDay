import { create } from 'zustand'
import type { User, TokenPair } from '../types/auth'

const STORAGE_KEY = 'flowday_tokens'

interface AuthState {
  user: User | null
  tokens: TokenPair | null
  isAuthenticated: boolean
  setTokens: (tokens: TokenPair) => void
  setUser: (user: User) => void
  login: (user: User, tokens: TokenPair) => void
  logout: () => void
  hydrate: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  tokens: null,
  isAuthenticated: false,

  setTokens: (tokens) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
    set({ tokens, isAuthenticated: true })
  },

  setUser: (user) => set({ user }),

  login: (user, tokens) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
    set({ user, tokens, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ user: null, tokens: null, isAuthenticated: false })
  },

  hydrate: () => {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    try {
      const tokens: TokenPair = JSON.parse(raw)
      set({ tokens, isAuthenticated: true })
    } catch {
      // invalid JSON — leave state untouched
    }
  },
}))
