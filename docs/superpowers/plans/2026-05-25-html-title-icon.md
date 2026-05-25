# HTML Title and Icon Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update HTML title from "frontend" to "Financial News Agent" and replace Vite default favicon with branded FN letter icon matching header logo.

**Architecture:** Simple asset replacement - update HTML title tag and create new SVG favicon with salmon gradient background and white FN letters matching the existing header logo-mark design.

**Tech Stack:** HTML, SVG, Vite build system

---

## File Structure

**Files to Modify:**
- `frontend/index.html` - Update title tag
- `frontend/public/favicon.svg` - Replace with new FN icon

**Build Artifacts (auto-generated):**
- `frontend/dist/index.html` - Regenerated on build
- `frontend/dist/favicon.svg` - Copied on build

---

### Task 1: Update HTML Title

**Files:**
- Modify: `frontend/index.html:7`

- [ ] **Step 1: Update title tag**

Open `frontend/index.html` and change line 7:

```html
<title>Financial News Agent</title>
```

- [ ] **Step 2: Verify the change**

Run: `cat frontend/index.html | grep -A 1 "<title>"`

Expected output:
```
    <title>Financial News Agent</title>
```

- [ ] **Step 3: Commit the change**

```bash
git add frontend/index.html
git commit -m "feat: update HTML title to 'Financial News Agent'"
```

---

### Task 2: Create FN Favicon

**Files:**
- Modify: `frontend/public/favicon.svg`

- [ ] **Step 1: Create new favicon SVG**

Replace the content of `frontend/public/favicon.svg` with:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <title>Financial News Agent</title>
  <defs>
    <linearGradient id="salmon-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ff8b7b;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#e6705f;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="48" height="48" rx="2" fill="url(#salmon-gradient)" />
  <text x="24" y="32" font-family="'Libre Baskerville', Georgia, serif" font-size="20" font-weight="700" fill="#ffffff" text-anchor="middle" letter-spacing="-0.5">FN</text>
</svg>
```

- [ ] **Step 2: Verify the SVG file**

Run: `cat frontend/public/favicon.svg | head -5`

Expected: Should show the SVG opening tags with gradient definition

- [ ] **Step 3: Test in browser (dev server)**

Run: `cd frontend && npm run dev`

Open browser to the dev server URL and check:
1. Browser tab title shows "Financial News Agent"
2. Favicon shows FN letters with salmon/coral gradient background

- [ ] **Step 4: Stop dev server**

Press Ctrl+C to stop the dev server

- [ ] **Step 5: Commit the change**

```bash
git add frontend/public/favicon.svg
git commit -m "feat: replace favicon with branded FN icon

- Salmon gradient background (#ff8b7b → #e6705f)
- White FN letters matching header logo-mark
- 48x48px SVG with 2px border radius"
```

---

### Task 3: Build and Verify Production Assets

**Files:**
- Verify: `frontend/dist/index.html`
- Verify: `frontend/dist/favicon.svg`

- [ ] **Step 1: Build frontend**

Run: `cd frontend && npm run build`

Expected: Build completes successfully with no errors

- [ ] **Step 2: Verify dist files exist**

Run: `ls -la frontend/dist/index.html frontend/dist/favicon.svg`

Expected: Both files exist with recent timestamps

- [ ] **Step 3: Verify title in built HTML**

Run: `grep "<title>" frontend/dist/index.html`

Expected output:
```
    <title>Financial News Agent</title>
```

- [ ] **Step 4: Verify favicon reference**

Run: `grep "favicon.svg" frontend/dist/index.html`

Expected: Should show the link tag referencing `/favicon.svg`

- [ ] **Step 5: Preview production build**

Run: `cd frontend && npm run preview`

Open browser to the preview URL and verify:
1. Tab title shows "Financial News Agent"
2. Favicon displays correctly

- [ ] **Step 6: Stop preview server**

Press Ctrl+C to stop the preview server

- [ ] **Step 7: Commit build artifacts (if tracked)**

If dist files are tracked in git:
```bash
git add frontend/dist/index.html frontend/dist/favicon.svg
git commit -m "build: update dist with new title and favicon"
```

If dist is gitignored, skip this step.

---

## Self-Review Checklist

**Spec Coverage:**
- ✅ Page title updated to "Financial News Agent"
- ✅ Favicon replaced with FN letter icon
- ✅ Salmon gradient background (#ff8b7b → #e6705f)
- ✅ White text color
- ✅ Libre Baskerville font
- ✅ 48x48px dimensions
- ✅ 2px border radius
- ✅ SVG format
- ✅ Build process verified

**Placeholder Check:**
- ✅ No TBD or TODO items
- ✅ All file paths are exact
- ✅ All code blocks are complete
- ✅ All commands have expected output

**Type Consistency:**
- ✅ File paths consistent across tasks
- ✅ Color values match spec (#ff8b7b, #e6705f, #ffffff)
- ✅ Dimensions consistent (48x48px)

---

## Success Criteria

After completing all tasks:

1. ✅ Browser tab shows "Financial News Agent" title
2. ✅ Favicon displays FN letters with salmon gradient
3. ✅ Visual consistency with header logo-mark
4. ✅ Dev server shows changes correctly
5. ✅ Production build includes changes
6. ✅ No build errors or warnings
