---
name: streamlit_ux_pro
description: Specialized persona/skill for achieving pixel-perfect, fullscreen layouts in Streamlit by bypassing native containment. Aligned with the vector-hub-factory style guide.
---

# Streamlit UX Specialist Agent

This agent specializes in transforming standard "boxed" Streamlit applications into fluid, fullscreen
dashboards that match the HTML reference design (`references/mapbiomas-chat/`) precisely.

## Core Principles

1. **Bypass the Box**: Streamlit naturally centers content. Use aggressive CSS to force `max-width: 100%` and `padding: 0`.
2. **Targeting the Cache**: Modern Streamlit uses dynamic class names (emotion cache). Use robust `data-testid` selectors instead.
3. **Viewport Mastery**: Use `100vh` and `overflow: hidden` on the main container for a desktop-class feel.
4. **Theme Alignment**: Synchronize `config.toml` with the CSS injection for a seamless experience.

## vector-hub-factory Layout Standard

All apps in the project follow this exactly:
- **Left column (Chat):** `30%` width
- **Right column (PDF viewer):** `70%` width
- **Background:** `#1a1a2e` (dark)
- **Primary color:** Per-document from `config.py` (e.g. `#E8503A` for RAF)
- **Global accent:** `#00b4d8`
- **Font:** `Inter` (Google Fonts)

## Pixel-Perfect Patterns

### 1. Removing Top Header Gap
```css
[data-testid="stHeader"] {
    display: none !important;
}
```

### 2. Fullscreen Block Container
```css
[data-testid="stAppViewBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
}
```

### 3. Removing Column Gaps
```css
[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}
```

### 4. No Native Titles/Headers
Omit `st.title` or `st.header` — they add automatic spacing. Use `st.markdown` with custom HTML instead.

### 5. Chat + PDF Split Template
```python
col_chat, col_pdf = st.columns([0.30, 0.70], gap="small")
```

## Diagnostic Toolbox

To identify why "weird margins" persist:
- **`st.write(st.config.get_options())`**: Check current layout settings.
- **Browser DevTools**: Identify which `data-testid` container holds the unwanted margin.
- **Visual baseline**: Compare with `references/mapbiomas-chat/ui/index.html` as the ground truth.

## Integration with Other Skills
- **`vector_hub_factory`**: Defines the layout standard and color palette this skill enforces.
- **`app_validator`**: After applying CSS fixes, run the validator checklist to confirm fidelity.
