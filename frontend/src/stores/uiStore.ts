import { create } from 'zustand'

interface UIState {
  theme: 'dark'
  sidebarOpen: boolean
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'dark',
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))
