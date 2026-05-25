# HTML Title and Icon Update Design

**Date:** 2026-05-25  
**Status:** Approved  
**Type:** Frontend Enhancement

## Overview

Update the default HTML title and favicon to reflect the Financial News Agent brand identity, replacing generic placeholder content with professional branding that matches the application's editorial design system.

## Problem Statement

The current HTML setup uses generic defaults:
- Title: "frontend" (non-descriptive)
- Favicon: Purple lightning bolt (Vite's default icon)

These placeholders don't represent the application's purpose or brand, creating a poor first impression in browser tabs and bookmarks.

## Design Goals

1. **Brand Consistency**: Favicon should match the header logo-mark design
2. **Professional Identity**: Clear, descriptive page title
3. **Visual Cohesion**: Use the established salmon color palette
4. **Technical Quality**: High-resolution SVG for crisp display at all sizes

## Design Specification

### 1. Page Title

**Current:**
```html
<title>frontend</title>
```

**New:**
```html
<title>Financial News Agent</title>
```

**Rationale:** Descriptive, professional, and immediately communicates the application's purpose.

### 2. Favicon Design

**Visual Design:**
- **Content**: "FN" letters (matching header logo-mark)
- **Typography**: Libre Baskerville, 700 weight, 20px font size
- **Letter Spacing**: -0.5px
- **Text Color**: White (#ffffff)
- **Background**: Linear gradient 135deg
  - Start: `#ff8b7b` (--color-salmon)
  - End: `#e6705f` (--color-salmon-dark)
- **Dimensions**: 48x48px
- **Border Radius**: 2px
- **Format**: SVG

**Design Rationale:**
- **FN over FNA**: Matches the existing header logo-mark exactly, creating perfect visual consistency between the browser tab and the application header
- **Salmon Gradient**: Uses the signature color from the editorial design system
- **Square with Subtle Radius**: Professional, modern appearance that works well at small sizes
- **SVG Format**: Ensures crisp rendering at any resolution (retina displays, different zoom levels)

### 3. Implementation Files

**Files to Modify:**
1. `frontend/index.html` - Update `<title>` tag (line 7)
2. `frontend/public/favicon.svg` - Replace with new FN icon

**Files to Update (Build Artifacts):**
- `frontend/dist/index.html` - Will be regenerated on build
- `frontend/dist/favicon.svg` - Will be copied on build
- `dist/static/index.html` - Will be regenerated on build
- `dist/static/favicon.svg` - Will be copied on build

## Technical Considerations

### SVG Structure

The favicon SVG should be self-contained with:
- Embedded gradient definition
- Proper viewBox for scaling
- Accessible markup (title element)
- Optimized path data

### Browser Compatibility

SVG favicons are supported in:
- Chrome/Edge 80+
- Firefox 41+
- Safari 9+
- Opera 67+

Fallback: Modern browsers that don't support SVG favicons will typically fall back to a default icon, which is acceptable given the broad support.

### Build Process

The Vite build process will:
1. Copy `public/favicon.svg` to `dist/favicon.svg`
2. Reference it correctly in the built `index.html`
3. No additional configuration needed

## Design Alternatives Considered

**Alternative A: FNA (three letters)**
- Pros: Complete brand acronym
- Cons: Crowded at small sizes, doesn't match header logo

**Alternative B: Single F**
- Pros: Maximum clarity at small sizes
- Cons: Less distinctive, lower brand recognition

**Selected: FN (two letters)**
- Pros: Perfect match with header logo-mark, strong brand consistency, readable at all sizes
- Cons: None significant

## Success Criteria

1. ✅ Browser tab shows "Financial News Agent" title
2. ✅ Favicon displays FN letters with salmon gradient
3. ✅ Visual consistency with header logo-mark
4. ✅ Crisp rendering at all browser zoom levels
5. ✅ No build errors or warnings

## Future Enhancements

- Add additional favicon sizes (16x16, 32x32 PNG) for older browsers
- Add Apple Touch Icon for iOS home screen
- Add manifest.json for PWA support with app icons
