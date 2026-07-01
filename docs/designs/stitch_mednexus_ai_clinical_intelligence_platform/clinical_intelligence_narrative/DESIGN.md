---
name: Nexus Intelligence
colors:
  surface: '#0e1417'
  surface-dim: '#0e1417'
  surface-bright: '#333a3d'
  surface-container-lowest: '#090f12'
  surface-container-low: '#161d1f'
  surface-container: '#1a2123'
  surface-container-high: '#242b2e'
  surface-container-highest: '#2f3639'
  on-surface: '#dde3e7'
  on-surface-variant: '#bbc9cf'
  inverse-surface: '#dde3e7'
  inverse-on-surface: '#2b3134'
  outline: '#859399'
  outline-variant: '#3c494e'
  surface-tint: '#4cd6ff'
  primary: '#a4e6ff'
  on-primary: '#003543'
  primary-container: '#00d1ff'
  on-primary-container: '#00566a'
  inverse-primary: '#00677f'
  secondary: '#d1bcff'
  on-secondary: '#3c0090'
  secondary-container: '#7000ff'
  on-secondary-container: '#ddcdff'
  tertiary: '#ffd59c'
  on-tertiary: '#442b00'
  tertiary-container: '#feb127'
  on-tertiary-container: '#6b4700'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b7eaff'
  primary-fixed-dim: '#4cd6ff'
  on-primary-fixed: '#001f28'
  on-primary-fixed-variant: '#004e60'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d1bcff'
  on-secondary-fixed: '#23005b'
  on-secondary-fixed-variant: '#5700c9'
  tertiary-fixed: '#ffddb1'
  tertiary-fixed-dim: '#ffba49'
  on-tertiary-fixed: '#291800'
  on-tertiary-fixed-variant: '#624000'
  background: '#0e1417'
  on-background: '#dde3e7'
  surface-variant: '#2f3639'
  surface-base: '#0e1417'
  surface-glass: rgba(26, 33, 35, 0.7)
  border-low-opacity: rgba(60, 73, 78, 0.5)
  success-glow: '#feb127'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  gutter: 24px
  container-max: 1440px
---

## Brand & Style
The brand identity is centered on **Clinical Intelligence**—a fusion of high-stakes medical precision and advanced neural computation. The aesthetic is a sophisticated evolution of **Glassmorphism** and **Corporate Modern**, designed to feel authoritative yet technologically forward-thinking.

The interface targets medical professionals who require rapid, high-confidence data synthesis. The visual language utilizes deep oceanic tones, vibrant cyan accents, and translucent surfaces to evoke a sense of "digital depth" and "real-time processing." Every element is designed to minimize cognitive load while emphasizing the system's "active" nature through subtle pulses and glowing states.

## Colors
The palette is built on a "Deep Sea" dark mode foundation. 

- **Primary (#00d1ff):** The "Clinical Cyan" used for data highlights, primary actions, and brand identity. It represents precision and clarity.
- **Secondary (#7000ff):** Used sparingly for AI-specific logic pathways and specialized "Neural" nodes.
- **Tertiary (#feb127):** An "Amber Alert" tone used for system status, trend indicators, and active stream pulses.
- **Neutral/Surface:** The background is a solid `#0e1417`, while containers utilize a layered approach ranging from `#090f12` (lowest) to `#333a3d` (brightest highlight).

## Typography
The system uses **Inter** for all UI interactions to ensure maximum legibility and a neutral, professional tone. 

- **Hierarchy:** Dramatic scale shifts between `display-lg` (for brand/welcome) and `label-caps` (for metadata) create clear scanning paths.
- **Monospacing:** **JetBrains Mono** is reserved strictly for technical data, entity counts, timestamps, and ID strings, signaling "raw system output" to the user.
- **Micro-Copy:** Uppercase labels with increased letter spacing are used for navigation and table headers to provide a distinct structural rhythm.

## Layout & Spacing
The layout employs a **12-column fluid grid** with a fixed sidebar (64 units / 256px). 

- **Margins & Gutters:** A standard 24px gutter is used between cards. Screen margins on desktop are 24px, increasing to 32px or 48px for internal content sections.
- **Bento Structure:** Content is organized into "Bento Boxes"—discrete cards with high-density information grouped logically. 
- **Navigation:** A persistent left sidebar handles primary architectural navigation, while a secondary top bar provides contextual search and quick actions.
- **Mobile Reflow:** On mobile devices, the 12-column grid collapses to a single column, and the sidebar transitions to a hidden hamburger menu or bottom navigation bar.

## Elevation & Depth
Depth is created through **Glassmorphism** rather than traditional shadows.

- **The Base:** The `surface-base` (`#0e1417`) serves as the canvas.
- **Glass Cards:** Primary containers use `rgba(26, 33, 35, 0.7)` with a `12px` backdrop-blur and a `1px` border of `rgba(60, 73, 78, 0.5)`.
- **Interactions:** Hover states are indicated by a subtle cyan glow (`0 0 20px rgba(0, 209, 255, 0.05)`) and a brightening of the border color.
- **Tonal Tiers:** Use `surface-container-low` for inputs and `surface-container-high` for hovered list items to differentiate interactivity without increasing visual "height."

## Shapes
The shape language is "Soft Professional." 

- **Base Corner Radius:** `0.25rem` (4px) for small elements like tags or micro-inputs.
- **Standard Radius (lg):** `0.5rem` (8px) for buttons, navigation items, and list containers.
- **Container Radius (xl):** `0.75rem` (12px) for major cards, charts, and modal dialogs.
- **Pill (full):** Reserved strictly for avatars and specific status indicators.

## Components
- **Buttons:** Primary buttons use the `primary-container` background with high-contrast text. They should include a subtle `active:scale-95` transition for tactile feedback.
- **Glass Cards:** Must include the 12px backdrop blur. Use them for statistics, charts, and news feeds.
- **Sidebar Items:** Use a 2px horizontal transition on hover (`translateX(4px)`) to provide a sleek, modern feel.
- **Input Fields:** Search inputs should have a subtle ring glow on focus using the primary color at 50% opacity.
- **Tables:** Use `divide-y` with low-opacity borders (`outline-variant/30`). Table headers should always use `label-caps`.
- **Status Indicators:** Small 6px circles with a `pulse` animation should be used for "Live" or "Processing" states.