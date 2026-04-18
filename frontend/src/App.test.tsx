import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(document.getElementById('root') ?? document.body).toBeTruthy()
  })

  it('has dark background root element', () => {
    const { container } = render(<App />)
    const root = container.firstElementChild as HTMLElement
    expect(root).toBeTruthy()
    // The root div must carry the dark-bg class
    expect(root.className).toContain('dark-bg')
  })
})
