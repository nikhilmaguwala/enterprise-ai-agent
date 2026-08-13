---
name: ResolveAI Design System
colors:
  surface: '#f8f9ff'
  surface-dim: '#d1dbec'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eef4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dfe9fa'
  surface-container-highest: '#d9e3f4'
  on-surface: '#121c28'
  on-surface-variant: '#45464f'
  inverse-surface: '#27313e'
  inverse-on-surface: '#eaf1ff'
  outline: '#767680'
  outline-variant: '#c6c5d0'
  surface-tint: '#4f5c8e'
  primary: '#000f3f'
  on-primary: '#ffffff'
  primary-container: '#172554'
  on-primary-container: '#808dc2'
  inverse-primary: '#b7c4fd'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#1c0047'
  on-tertiary: '#ffffff'
  tertiary-container: '#35007a'
  on-tertiary-container: '#a375ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b7c4fd'
  on-primary-fixed: '#071747'
  on-primary-fixed-variant: '#374475'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#eaddff'
  tertiary-fixed-dim: '#d2bbff'
  on-tertiary-fixed: '#25005a'
  on-tertiary-fixed-variant: '#5a00c6'
  background: '#f8f9ff'
  on-background: '#121c28'
  surface-variant: '#d9e3f4'
typography:
  display:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  tabular-nums:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  gutter: 24px
  margin: 32px
  max_width: 1440px
---

## Brand & Style
The design system is rooted in **Corporate Modernism** with a focus on operational clarity and "observable AI." The aesthetic is high-fidelity, precise, and utilitarian, aiming to evoke a sense of deep technical competence and security. It avoids the whimsical trends of consumer tech in favor of a stable, enterprise-ready interface that feels like a professional tool rather than a novelty.

The visual language prioritizes information density without clutter. It uses a "low-noise" philosophy: every line, color, and spacing choice must serve a functional purpose. The "Intelligent" aspect is conveyed through crisp edges, generous whitespace, and a sophisticated use of typography to denote hierarchy in complex data environments.

## Colors
The palette is dominated by deep blues and clean neutrals to establish an "Enterprise-ready" foundation. 
- **Navy (#172554)** is reserved for high-level structural elements (sidebars, primary headers) to provide a grounded anchor.
- **Blue (#2563EB)** serves as the primary action color, used for buttons, active states, and selection indicators.
- **Purple (#7C3AED)** is the "Intelligence" accent, specifically used to highlight AI-generated content, automated suggestions, or specialized machine-learning metrics, separating human input from machine output.
- **Neutrals** are strictly tiered: `#F8FAFC` for the canvas, `#FFFFFF` for interactive cards, and `#F1F5F9` for secondary UI chrome like table headers or inset panels.

## Typography
This design system utilizes **Geist** for its technical precision and exceptional legibility in data-dense environments. 

Key Rules:
1. **Tabular Numerals:** All data tables, timestamps, and confidence scores must use the `tabular-nums` variant to ensure vertical alignment of digits.
2. **Hierarchy:** Headlines use a semi-bold weight (600) with slight negative letter spacing to feel "tight" and professional.
3. **Labels:** Small labels (`label-sm`) use an uppercase transform and increased letter spacing to differentiate from body text in dense forms.
4. **AI Indicators:** Text representing AI thought processes should use `body-sm` with a secondary text color to maintain a distinction from primary user actions.

## Layout & Spacing
The system follows a strict **8px linear scale**. Layouts are structured on a 12-column grid for desktop with a 24px gutter. 

**Mobile Adaption:**
- Under **768px**, the 12-column grid collapses to a 4-column layout. 
- Margins reduce from 32px to 16px. 
- All horizontal scrolling components (like data tables) must be contained within a vertical stack or provide a clear "View All" transition.

**Density:**
For the "Observable AI" dashboard, use `md` (16px) spacing for internal card padding and `sm` (8px) for related group elements to maintain a high information density suitable for enterprise monitoring.

## Elevation & Depth
Depth is achieved through **Tonal Layering** and **Structural Outlines** rather than heavy shadows.

1.  **Canvas Layer:** The base background is `#F8FAFC`.
2.  **Surface Layer:** Cards and main content areas use `#FFFFFF` with a 1px border (`#E2E8F0`).
3.  **Elevation (Shadows):** Use shadows sparingly. When necessary (e.g., dropdowns or modals), use a highly diffused, low-opacity shadow: `0px 4px 12px rgba(17, 24, 39, 0.05)`.
4.  **Active Depth:** Interactive elements like buttons should feel "flat" on the surface, using a subtle 1px inset border on hover rather than an elevation lift.

## Shapes
The shape language is controlled and systematic.
- **Cards:** Use `12px` (standard) or `16px` (large dashboard containers) to provide a soft but professional frame for data.
- **Buttons:** Use a tighter `8px` radius to maintain a sense of precision.
- **Inputs:** A `6px` radius ensures form fields look sharp and align better with the 8px spacing grid.
- **Status Pills:** Use fully rounded (pill-shaped) borders for status indicators (e.g., "Active", "Resolved") to distinguish them from interactive buttons.

## Components
- **Buttons:** Primary buttons use `#2563EB` with white text. Secondary buttons use a white background with a `#E2E8F0` border and `#111827` text. Use `Lucide` outline icons sized to 18px within buttons.
- **AI Action Chips:** Components that trigger or display AI logic should use a subtle purple background (`#F5F3FF`) with `#7C3AED` text and a "Sparkle" icon.
- **Inputs:** Use a 1px border (`#E2E8F0`). On focus, transition the border color to `#2563EB` with a 2px outer glow of the same color at 10% opacity.
- **Data Tables:** Headers must be `#F1F5F9` with `label-sm` typography. Rows should have a subtle hover state (`#F8FAFC`). No vertical grid lines; use horizontal dividers only.
- **Status Indicators:** Use a solid 8px circle icon next to text for status. `Success = #15803D`, `Warning = #B45309`, `Error = #B91C1C`.
- **Cards:** All cards must include a header section with a bottom border if they contain mixed content types (e.g., a graph and a list).