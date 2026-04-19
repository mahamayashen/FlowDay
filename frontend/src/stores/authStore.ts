import { create } from 'zustand'
import type { User, TokenPair } from '../types/auth'

const STORAGE_KEY = 'flowday_tokens'

interface AuthState {
  user: User | null
  tokens: TokenPair | null
  isAuthenticated: boolean
  isUserLoading: boolean
  setTokens: (tokens: TokenPair) => void
  setUser: (user: User) => void
  login: (user: User, tokens: TokenPair) => void
  logout: () => void
  hydrate: () => void
  setUserLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  tokens: null,
  isAuthenticated: false,
  isUserLoading: false,

  setTokens: (tokens) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
    set({ tokens, isAuthenticated: true })
  },

  setUser: (user) => set({ user, isUserLoading: false }),

  setUserLoading: (loading) => set({ isUserLoading: loading }),

  login: (user, tokens) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
    set({ user, tokens, isAuthenticated: true, isUserLoading: false })
  },

  logout: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ user: null, tokens: null, isAuthenticated: false, isUserLoading: false })
  },

  hydrate: () => {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    try {
      const tokens: TokenPair = JSON.parse(raw)
      if (
        typeof tokens.access_token !== 'string' ||
        !tokens.access_token ||
        typeof tokens.refresh_token !== 'string' ||
        !tokens.refresh_token
      ) {
        localStorage.removeItem(STORAGE_KEY)
        return
      }
      set({ tokens, isAuthenticated: true })
    } catch {
      localStorage.removeItem(STORAGE_KEY)
    }
  },
}))
