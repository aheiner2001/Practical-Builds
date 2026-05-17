# Cursor prompt — personal weight tracker (single HTML file)

## Project overview

Build a single self-contained `index.html` file that functions as a mobile-optimized personal health tracker. It must work offline with no backend, no database, and no external API calls. All data is persisted in `localStorage`. The file will be hosted on GitHub Pages.

---

## Technical constraints

- Single file: all HTML, CSS, and JavaScript in one `index.html`
- No frameworks, no build tools, no npm. Vanilla JS only.
- One external dependency allowed: Chart.js loaded from CDN for the weight chart
  - `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- All data stored in `localStorage` under a namespace prefix `wt_` (e.g. `wt_entries`, `wt_workouts`, `wt_food`)
- Mobile-first CSS: max-width 480px centered, viewport meta tag set, font-size base 16px, touch-friendly tap targets (min 44px height)
- No cookies, no external fonts, no analytics, no tracking

---

## Hardcoded constants (do not make these configurable on first load)

```js
const START_WEIGHT = 220;        // lbs
const START_DATE   = '2024-12-27'; // ISO format
const GOAL_WEIGHT  = null;       // user sets this in the app
```

---

## Data models (stored as JSON arrays in localStorage)

### Weight entries — `wt_entries`
```js
[
  {
    date: 'YYYY-MM-DD',   // one entry per calendar day max
    weight: 214.5         // lbs, float
  }
]
```

### Food log — `wt_food`
```js
[
  {
    date: 'YYYY-MM-DD',
    calories: 1850,        // integer, nullable if not tracked
    notes: 'Chicken, rice, salad...'  // freeform string, nullable
  }
]
```

### Workouts — `wt_workouts`
```js
[
  {
    id: 'uuid-or-timestamp',
    date: 'YYYY-MM-DD',
    type: 'strength' | 'cardio' | 'flexibility' | 'sport' | 'other',
    sets: [
      { exercise: 'Bench press', sets: 3, reps: 10, weight: 135 }
    ],
    notes: ''             // freeform, nullable
  }
]
```

### Settings — `wt_settings`
```js
{
  goalWeight: 185,      // lbs, user-set
  heightInches: 70      // for BMI calculation
}
```

---

## Navigation — tab bar

Three tabs at the top of the page, always visible:

1. **Dashboard** — overview and stats
2. **Log** — daily entry (weight + food)
3. **Workouts** — log and history

Active tab highlighted. Switching tabs shows/hides the corresponding section (no page reload). Default tab on load: Dashboard.

---

## Tab 1: Dashboard

### Stat cards (2-column grid)
- Current weight — most recent entry's weight in lbs
- Starting weight — hardcoded 220 lbs
- Total lost — difference between start and current (show as "− X lbs" in green if losing)
- Goal weight — from settings; show "— " if not set
- Lbs to goal — current minus goal; show "— " if no goal set
- BMI — calculated from current weight + height from settings. Show "— " if height not set. Include a small label with BMI category (Underweight / Normal / Overweight / Obese)

### Running averages (below stat cards)
- 7-day average — mean weight of last 7 calendar days with an entry
- 14-day average — mean weight of last 14 calendar days with an entry
- Weekly change — difference between this week's average and last week's average. Show arrow up/down and color red/green accordingly.

### Personal records
- Lowest recorded weight — minimum weight ever logged, with date
- Current streak — consecutive calendar days with a log entry (weight OR food OR workout counts)

### Sunday summary card
- Every Sunday, automatically generate and display a summary card at the top of the Dashboard (above stat cards).
- Card contains: week date range, average weight for the week, total workouts logged, weekly weight change vs prior week
- Store the most recent Sunday summary in `localStorage` under `wt_sunday_summary` and display it until the next Sunday rolls over.

### Weight chart
- Full-width line chart using Chart.js
- X-axis: dates from START_DATE to today
- Y-axis: weight in lbs — auto-scaled with a small padding above and below min/max
- Data points: one per logged entry
- Overlay a trend line (simple linear regression calculated in JS over all data points) as a second dataset — dashed line, different color
- Chart is non-interactive (no zoom/pan needed)
- Label: "Weight over time"

### Goal progress bar
- Only shown if goal weight is set in settings
- Bar fills from 0% (start weight) to 100% (goal weight) based on current weight
- Show percentage and lbs remaining

---

## Tab 2: Log (daily entry)

### Weight entry
- Date picker defaulting to today (read-only if today already has an entry — show the existing value instead)
- Weight input (number, step 0.1, min 50, max 500) in lbs
- Submit button: "Save weight"
- If today already has an entry, show it with an "Edit" button instead of the form
- Rule: only one weight entry per calendar day

### Food log entry
- Same date as the weight entry section (tied to today)
- Calories field — number input, optional
- Notes textarea — freeform, optional (placeholder: "What did you eat today?")
- Submit button: "Save food log"
- Show today's existing food entry below the form if it exists, with an "Edit" button

---

## Tab 3: Workouts

### Log a workout
- Date picker defaulting to today
- Type selector: Strength / Cardio / Flexibility / Sport / Other (pill-style toggle or select)
- Sets & reps builder (for Strength type):
  - Dynamic list of set rows: each row has [Exercise name | Sets | Reps | Weight (lbs)]
  - "Add exercise" button appends a new row
  - "Remove" button on each row
  - Hide this section entirely when type is not Strength
- Notes textarea — optional, shown for all workout types
- Submit button: "Save workout"

### Workout history
- Scrollable list of all past workouts, newest first
- Each entry shows: date, type badge, exercise list (for strength) or notes snippet (for cardio/other)
- "Delete" button on each entry (with a confirm prompt)

---

## Monthly summary view (inside Dashboard, below chart)

- Collapsible section: "Monthly breakdown"
- One row per calendar month from START_DATE to current month
- Columns: Month, Avg weight (lbs), # weigh-ins, # workouts, Weight change vs prior month
- Sorted newest first
- Collapsed by default; clicking the header expands it

---

## Data import

- A small "Import CSV" button in the Dashboard footer area
- Opens a file picker that accepts `.csv` files
- CSV format expected (for weight entries):
  ```
  date,weight
  2024-12-27,220
  2024-12-28,219.5
  ```
- On import: parse each row, skip duplicates (by date), merge with existing `wt_entries`, save, re-render
- Show a toast/alert after import: "Imported X new entries, skipped Y duplicates"

---

## CSV export

- "Export CSV" button in the Dashboard footer area
- Exports all weight entries as a downloadable `.csv` file
- Filename: `weight-log-YYYY-MM-DD.csv`
- Columns: `date,weight`
- Trigger via `<a download>` with a blob URL — no server needed

---

## Settings panel

- Accessible via a gear icon button in the top-right corner of the page (always visible)
- Slides in as an overlay panel from the right (or opens inline below the header — whichever is simpler)
- Fields:
  - Goal weight (lbs) — number input
  - Height (inches) — number input (used for BMI)
- Save button writes to `wt_settings` in localStorage and re-renders dashboard stats
- Close/dismiss button

---

## UI & styling guidelines

- Color scheme: clean white background, dark text. Use a single accent color (suggest a medium blue, e.g. `#2563eb`) for buttons, active tab, chart line, progress bar.
- Trend line on chart: dashed gray or light purple
- Cards: white background, subtle border (`1px solid #e5e7eb`), border-radius 12px, padding 16px
- Stat card values: large font (24px), bold. Labels: 12px, muted gray.
- Tab bar: sticky at top, white background, border-bottom. Active tab: accent color underline and text color.
- Toast notifications: slide in from bottom, auto-dismiss after 3 seconds
- All forms: input height min 44px, font-size 16px (prevents iOS zoom on focus)
- Weekly change badge: green with down-arrow if losing, red with up-arrow if gaining
- Responsive: looks good from 320px to 480px width. Center the layout on wider screens with `max-width: 480px; margin: 0 auto`.

---

## Logic notes

- Linear regression for trend line: implement a basic `linearRegression(points)` function that returns `{slope, intercept}` and generates a predicted y for each x date value.
- BMI formula: `(weight_lbs / (height_inches ** 2)) * 703`
- Running averages: look back over the last N *calendar days* (not just N entries) — if fewer than N entries exist in that window, average what's available.
- Streak: count backwards from today; break on first calendar day with no entry of any kind.
- Sunday summary: generate on first Dashboard load of a Sunday if no summary exists for the current week. Cache in `wt_sunday_summary = { weekOf: 'YYYY-MM-DD', ...data }`. Re-generate if `weekOf` is not the most recent Sunday.

---

## File structure

Everything in a single `index.html`. Suggested internal structure:

```
<head>   — meta, viewport, title, Chart.js CDN, <style> block
<body>
  <header>     — app title + settings gear icon
  <nav>        — 3-tab bar
  <main>
    <section id="dashboard">  ...
    <section id="log">        ...
    <section id="workouts">   ...
  </main>
  <div id="settings-panel">  ...
  <div id="toast">           ...
  <script>   — all JS inline
```

---

## What to build first (suggested order for Cursor)

1. HTML structure + CSS (tabs, cards, layout, mobile styles)
2. localStorage helpers (get/set/clear for each data key)
3. Dashboard stat cards (hardcoded values first, then wired to data)
4. Weight entry form + validation (one-per-day rule)
5. Chart.js weight chart + trend line
6. Food log form
7. Workout log form (with dynamic sets/reps builder)
8. Workout history list
9. Monthly breakdown table
10. Sunday summary card logic
11. Settings panel
12. Import CSV + Export CSV
13. Toast notifications
14. Final polish (streak, personal records, goal progress bar)