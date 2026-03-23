# FlowDay — Frontend Context

@import ../docs/CONVENTIONS.md

## Layout

```
frontend/
├── src/
│   ├── components/      # UI components (one per file, co-locate *.test.tsx)
│   ├── pages/           # Route-level page components
│   ├── hooks/           # Custom React hooks
│   ├── stores/          # Zustand stores (client state)
│   ├── api/             # React Query hooks + API client (server state)
│   ├── types/           # Shared TypeScript types/interfaces
│   └── utils/           # Pure utility functions
├── public/
└── index.html
```

## Patterns

- **Functional components only** — no class components, explicit return types on all components
- **Server state:** React Query (`useQuery`, `useMutation`) — all API calls go through `src/api/`
- **Client state:** Zustand stores in `src/stores/` — one store per domain (e.g., `timerStore`, `plannerStore`)
- Props interfaces named `{ComponentName}Props`, defined in the same file as the component
- No `any` — use `unknown` + type guards; prefer discriminated unions

## Theme

- Background: `#111113`
- Accent: warm colors (amber/orange range)
- Dark theme is non-negotiable — never introduce light-only styles

## Testing

- Framework: Vitest + React Testing Library
- Test user interactions (drag-drop, timer start/stop), not implementation details
- No snapshot tests
- Test files co-located: `Button.tsx` → `Button.test.tsx`

## Key Commands (run from `frontend/`)

```bash
npm run dev     # Vite dev server
npm run build   # Production build
npm run lint    # ESLint
npx vitest      # Run tests
```
