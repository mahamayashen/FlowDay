import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from './uiStore'

beforeEach(() => {
  useUIStore.setState({ theme: 'dark', sidebarOpen: false })
})

describe('uiStore', () => {
  it('has correct initial state', () => {
    const state = useUIStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.sidebarOpen).toBe(false)
  })

  it('toggleSidebar sets sidebarOpen to true when false', () => {
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(true)
  })

  it('toggleSidebar sets sidebarOpen to false when true', () => {
    useUIStore.setState({ sidebarOpen: true })
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(false)
  })
})
