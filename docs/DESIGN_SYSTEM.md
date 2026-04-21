# FlowDay — Design System

> Living reference for the v2 visual language. Source of truth is
> `frontend/src/index.css` (design tokens) plus the per-page CSS files.
> When you change a token here, update `index.css` in the same PR.

---

## Philosophy

| Word | Meaning |
|---|---|
| **Sleek** | Dark backgrounds, sharp type, crisp borders. No rounded-cartoon vibes. |
| **Tactile** | Every interactive element has a hover state (lift, glow, colour shift). |
| **Discoverable** | Content dense, not whitespace-heavy. Cards expand on hover to reveal more. |
| **Monospaced authority** | Numbers, timestamps, agent labels, meta info — all mono. |
| **Neon-on-navy** | Four accent colours against a near-black navy. No pastels, no greys. |

Inspiration anchor: Linear + Raycast aesthetic with a freelancer/studio warmth.

---

## Color palette

The entire app is built on **five colours** (plus neutrals). If a new UI needs
a sixth colour, ask first — it's almost certainly wrong.

### Brand

| Token | Hex | Role |
|---|---|---|
| `--yellow` | `#FFDE42` | **Focus / energy.** Active timers, CTAs, current day, logo, progress end-state. Always pair with near-black text. |
| `--cyan` | `#53CBF3` | **AI / insight.** Narrative Writer, Judge scores, pipeline running state, AI coach cards, agent labels. |
| `--blue` | `#5478FF` | **Interactive.** Links, selected states, input focus ring, hover borders, "Start without a block" ad-hoc CTA. |
| `--navy` | `#111FA2` | **Depth.** NavBar background. Never used for body text. |

Each brand colour has two companions:

- `--{color}-dim` — ~10-12% alpha, for tinted backgrounds (badges, cards)
- `--{color}-glow` — ~22-28% alpha, for box-shadow bloom on hover

Example pattern:

```css
.something {
  background: var(--cyan-dim);
  color: var(--cyan);
  border: 1px solid rgba(83, 203, 243, 0.22);
}
.something:hover { box-shadow: 0 0 20px var(--cyan-glow); }
```

### Backgrounds (layered dark)

| Token | Hex | Where |
|---|---|---|
| `--bg`   | `#080C1A` | Page background (deep navy) |
| `--bg-1` | `#0D1224` | Cards, header bars, elevated surfaces |
| `--bg-2` | `#131829` | Inputs, nested rows, hover on bg-1 |
| `--bg-3` | `#181e30` | Deepest fill — neutral badges, dashed skeletons |

### Text

| Token | Hex | Use |
|---|---|---|
| `--text-1` | `#F0F4FF` | Primary body copy, headlines |
| `--text-2` | `#8B9BC8` | Secondary — labels, meta, sidebar items |
| `--text-3` | `#4A5580` | Tertiary — eyebrows, mono meta, placeholders |

### Borders

All borders are **transparent blue** (not grey). This keeps everything
coherent and lets hover states "lift" naturally by raising the alpha.

| Token | Alpha | Use |
|---|---|---|
| `--border`        | 12% | Default resting border |
| `--border-hover`  | 30% | Hover state |
| `--border-focus`  | 55% | Keyboard focus, selected |

### Status

| Token | Hex | Use |
|---|---|---|
| `--success` | `#34D399` | Green — "done" agent chips, completed tasks |
| `--warning` | `#FFDE42` | Same as yellow — overdue badges |
| `--danger`  | `#F87171` | Red — errors, destructive actions |

### Semantic mapping (memorise this)

> **Yellow = what I'm doing right now**
> **Cyan = what the AI thinks about it**
> **Blue = what I can click**
> **Navy = the chrome holding it together**

---

## Typography

Three Google Fonts, loaded in `index.css`:

| Token | Family | Use | Example |
|---|---|---|---|
| `--font-head` | Space Grotesk (500/600/700) | Headlines, page titles, card titles | `AI Weekly Review` |
| `--font-body` | Plus Jakarta Sans (400/500/600/700) | Body copy, buttons, labels | Paragraph text |
| `--font-mono` | JetBrains Mono (400/500) | Numbers, timestamps, agent IDs, meta pills, eyebrows | `09:30 AM · 2.0h` |

Base body is `14px / 1.6`. Headings use `line-height: 1.25`.

### Type rhythm

| Use | Size | Weight | Family |
|---|---|---|---|
| Page title | 20–26px | 600 | head |
| Section title | 13–15px | 600 | head |
| Card title | 14px | 500-600 | head |
| Body | 14px | 400 | body |
| Small body | 13px | 400 | body |
| Meta / eyebrow | 10–11px | 500-700, `letter-spacing: 0.08–0.16em`, UPPERCASE | mono |
| Numeric stat | 18–24px | 600-700 | head or mono |

**Rules of thumb:**
- Letter-spacing on uppercase mono: `0.08em` minimum, `0.16em` for true eyebrows.
- Never use body font for numbers in stat pills — use mono.
- Never uppercase body copy. Only meta / eyebrows / badges.

---

## Spacing, radius, shadows, motion

### Radius

| Token | Value | Use |
|---|---|---|
| `--r-xs`   | 4px  | Small badges, priority bars |
| `--r-sm`   | 6px  | Icon buttons, chips, pills |
| `--r-md`   | 10px | Inputs, cards inside cards, nav items |
| `--r-lg`   | 14px | Primary cards, AI blocks |
| `--r-xl`   | 20px | Hero containers (rarely) |
| `--r-full` | 9999px | Pills, avatars |

### Shadows

| Token | Effect |
|---|---|
| `--shadow-sm`     | Subtle lift for rows on hover |
| `--shadow-md`     | Elevated cards |
| `--shadow-yellow` | Yellow glow — active CTA hover |
| `--shadow-cyan`   | Cyan glow — AI hover / generation |
| `--shadow-blue`   | Blue glow — interactive hover |

### Motion

| Token | Duration | Use |
|---|---|---|
| `--t-fast` | 0.12s ease | Colour, border, opacity |
| `--t-mid`  | 0.20s ease | Transform, shadow, layout |

**Rules:**
- No transition longer than 300ms on interactive state changes.
- Hover lift is exactly `translateY(-1px)`. No 2px. No scale.
- Pulse animations use 1.6–2.2s periods. Never below 1s (too jittery).

---

## Component patterns

### Cards

```css
.card {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 16px;
}
.card-hover:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-blue);
  transform: translateY(-1px);
}
```

### Buttons

Four variants:
- `.btn-primary` — yellow background, dark text (main CTA)
- `.btn-secondary` — blue-dim background, blue text (secondary actions)
- `.btn-ghost` — transparent + border (tertiary, toolbar)
- `.btn-danger` — danger-dim + danger text

Padding: `7px 14px` for standard, `9px 16px` for form submits.

### Badges / pills

Pattern: `{color}-dim` background + `{color}` text, mono font, uppercase,
`letter-spacing: 0.02em`, `border-radius: var(--r-full)`.

```css
.badge-yellow { background: var(--yellow-dim); color: var(--yellow); }
.badge-cyan   { background: var(--cyan-dim);   color: var(--cyan);   }
```

### AI block (whenever AI output appears)

```css
.ai-block {
  background: linear-gradient(135deg,
    rgba(83, 203, 243, 0.06) 0%,
    rgba(84, 120, 255, 0.04) 100%);
  border: 1px solid rgba(83, 203, 243, 0.20);
  border-radius: var(--r-lg);
  padding: 16px;
}
.ai-label {
  font: 10px/1 var(--font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--cyan);
}
```

Always precede AI content with an `.ai-label` (e.g. `✦ AI COACH · PREVIEW`)
or a Phosphor `Sparkle` icon in cyan.

### Inputs

- Background `--bg-2`, border `--border`, radius `--r-md`.
- Focus ring: `border-color: var(--blue)` + `box-shadow: 0 0 0 3px var(--blue-dim)`.

### Form fields

```html
<div class="form-field">
  <label>PROJECT NAME</label>
  <input type="text" />
</div>
```

Labels are uppercase mono-ish (11px, 700, `letter-spacing: 0.06em`).

---

## Layout

### App shell

```
┌──────┬────────────────────────────────────────┐
│ Nav  │              Main area                 │
│ 56px │         (flex, overflow:hidden)        │
│ navy │                                        │
└──────┴────────────────────────────────────────┘
```

- NavBar: fixed 56px width, navy background, vertical icon stack.
- Main: fills remaining space, manages own scrolling per page.

### Two-column sub-layouts

Projects page and Today page both use the same pattern: **220–320px sidebar
+ fluid main column**. Sidebar lives on `--bg-1`, main is on `--bg`.

### NavBar icon rules

- 56×56 navy column, 20px Phosphor icons.
- Active item: yellow square background (`--yellow`), dark icon.
- Inactive: 40% white, hover lifts to 80%.
- Logo "F" in yellow at the top, Sign-out icon at the bottom.

---

## Iconography

- Library: **@phosphor-icons/react** only. Do not mix with Heroicons, Lucide, etc.
- Default weight: `regular` (line). Use `fill` for the active yellow states and
  the Sparkle / Lightning brand moments.
- Sizes: 10 (chips), 12 (buttons), 14 (inline meta), 16 (section titles),
  18 (page titles), 20 (nav).

Semantic icons we've standardised on:

| Concept | Icon |
|---|---|
| Today / focus | `Lightning` (fill, yellow) |
| Plan | `CalendarBlank` |
| Projects | `FolderOpen` |
| Review | `ChartBar` |
| Weekly AI | `Brain` |
| AI / generated | `Sparkle` (fill, cyan) |
| Regenerate | `ArrowClockwise` |
| Agent done | `Check` (bold, on success-green chip) |
| Agent running | `CircleNotch` (spinning) |

---

## Animations (named & reusable)

Kept in `index.css` and `components/*.css`:

- `pulse-yellow` — 2.2s — running timer button
- `pulse-cyan` — 1.8s — generating AI CTA
- `pulse-cyan-dot` — 1.5s — narrative-generating dot
- `chip-pulse` — 1.6s — running agent chip
- `chip-spin` — 1s linear — CircleNotch inside running chip
- `skeleton-shimmer` — 1.6s — placeholder lines during generation
- `pulse-active` (TodayPage) — current block highlight

**Rule:** if you add a new `@keyframes`, give it a verb-noun name
(`pulse-yellow`, `fade-up`) and document it here.

---

## Dark mode only

There is **no light theme**. Do not ship one. If a future requirement
demands it, build a `[data-theme="light"]` override of the tokens — never
re-author colours inline.

---

## Adding a new UI element — checklist

Before you write CSS for something new, ask:

1. Can I reuse `.card`, `.btn-*`, `.badge-*`, `.ai-block`? → do that first.
2. Which of the five colours best fits the meaning? (yellow/cyan/blue/navy/status)
3. Is it interactive? → it needs a hover state (border lift + glow or translate).
4. Does it display a number / timestamp? → mono font, no exceptions.
5. Does it represent AI output? → wrap in `.ai-block` or mark with Sparkle + cyan.
6. Am I inventing a new colour / radius / shadow token? → push back; probably not needed.
7. Is the animation longer than 300ms for a hover? → shorten it.
8. Did I add a `data-testid`? (required for any interactive element)

---

## File map

| File | Owns |
|---|---|
| `frontend/src/index.css` | All design tokens + global component classes (`.btn`, `.card`, `.badge`, `.ai-block`, NavBar, sidebar, scrollbar) |
| `frontend/src/pages/*.css` | Page-specific layout + local overrides |
| `frontend/src/components/*.css` | Component-local styles (scoped by class prefix) |

Naming: component CSS classes use `component-element--modifier` (BEM-lite).
Example: `.agent-chip--running`, `.task-card-v2-head`, `.review-ai-card`.

---

## Page inventory (v2 shell)

| Route | Page | Signature elements |
|---|---|---|
| `/` | Today | Live timeline, now-indicator, AI coach preview card |
| `/plan` | Plan | Drag-drop timeline, unscheduled pool sidebar |
| `/projects` | Projects | Sidebar project list, task cards with priority bar |
| `/review` | Review | AI daily summary card, planned-vs-actual, weekly bar chart |
| `/weekly` | Weekly AI Review | Pipeline indicator, narrative card, radar scores, trend chart, history list |

---

## Tokens to avoid / anti-patterns

- ❌ `color: white` — use `var(--text-1)`
- ❌ `color: #888` — use `var(--text-2)` or `--text-3`
- ❌ `background: #111` — use `var(--bg)` / `--bg-1`
- ❌ New hex values inside component CSS — add to `index.css` or reuse
- ❌ `box-shadow: 0 0 30px gold` — use `var(--shadow-yellow)`
- ❌ `border: 1px solid #444` — use `var(--border)` (it's blue on purpose)
- ❌ Tailwind classes — we deliberately don't use it; custom CSS + tokens only
- ❌ Light-mode media queries — dark only, see above

---

## Reference palette card (copy into tickets / Figma)

```
BRAND         ACCENTS          NEUTRALS
━━━━━━━━━━    ━━━━━━━━━━      ━━━━━━━━━━
#FFDE42  🟡   #34D399 ✅       #080C1A bg
#53CBF3  🔵   #F87171 ❌       #0D1224 bg-1
#5478FF  🟣                    #131829 bg-2
#111FA2  🔷                    #F0F4FF text-1
                                #8B9BC8 text-2
                                #4A5580 text-3
```

---

*Last updated: 2026-04-20 with the v2 product shell (5-page IA, agent
pipeline indicator, mock-shell preview).*
