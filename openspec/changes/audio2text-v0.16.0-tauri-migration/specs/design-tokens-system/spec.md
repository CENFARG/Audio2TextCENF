# Design Tokens System Specification

## Purpose

CSS custom properties (50 tokens) implementing Pablo's Dark Goldenrod theme for the Audio2Text Tauri app. These tokens are the design contract consumed by Tailwind v4 `@theme` and inherited by shadcn-svelte components.

## Requirements

### Requirement: Token Source of Truth

A `tokens.json` file SHALL serve as the single source of truth for all design values. An automated step SHALL generate `tokens.css` from it.

- `tokens.json` SHALL contain: colors (bg, text, accent, status, surface, border, overlay), typography (family, size, weight), spacing (4px base scale), border-radius, box-shadow, transition, and z-index.
- `tokens.css` SHALL expose every value as a `--dt-*` CSS custom property.

#### Scenario: Token CSS variable generation

- GIVEN `tokens.json` exists with `{ "colors": { "bg": { "primary": "#1a1b1e" } } }`
- WHEN `tokens.css` is generated
- THEN it MUST contain `--dt-color-bg-primary: #1a1b1e`
- AND every token from `tokens.json` SHALL have a corresponding `--dt-*` variable

### Requirement: Color System — Dark Goldenrod Theme

The color palette SHALL define a dark theme with light theme tokens reserved for v0.16.1. Dark is the default and only active theme in this version:

- **Background**: primary `#1a1b1e`, secondary `#25262b`, tertiary `#2c2e33`
- **Surface**: card `#1e1f23`, elevated `#25262b`, overlay `rgba(0,0,0,0.7)`
- **Text**: primary `#c1c2c5`, secondary `#909296`, muted `#5c5f66`, inverse `#ffffff`
- **Accent**: goldenrod `#DAA520`, hover `#E8B830`, muted `rgba(218,165,32,0.15)`
- **Status**: success `#51cf66`, warning `#fcc419`, danger `#ff6b6b`, info `#339af0`
- **Border**: default `#373a40`, focus `#DAA520`
- **Recording LED**: recording `#ff0000`, paused `#fcc419`, idle `#6b7280`

#### Scenario: Accent color applied to active tab

- GIVEN a Tab component uses `var(--dt-color-accent)`
- WHEN the tab is selected
- THEN its text color SHALL be `#DAA520`
- AND an `rgba(218,165,32,0.15)` background SHALL fill behind the label at 15% opacity

#### Scenario: Status colors on UpdateView

- GIVEN the UpdateView receives `has_update: true`
- WHEN the status text renders
- THEN it SHALL use `var(--dt-color-status-success)` = `#51cf66`
- AND IF the update check fails SHALL render in `var(--dt-color-status-danger)` = `#ff6b6b`

### Requirement: Typography Scale

Six font sizes and four weights SHALL be defined.

- Sizes: xs `0.75rem` (12px), sm `0.875rem` (14px), base `1rem` (16px), lg `1.125rem` (18px), xl `1.5rem` (24px), xxl `2rem` (32px).
- Weights: normal `400`, medium `500`, semibold `600`, bold `700`.
- Font families: `system-ui, -apple-system, sans-serif` for UI; `"Cascadia Code", "Fira Code", monospace` for code.

#### Scenario: Typography in TranscriptionPanel

- GIVEN the TranscriptionPanel displays live transcription text
- WHEN text is rendered
- THEN the font SHALL be `system-ui, -apple-system, sans-serif` at size `var(--dt-font-size-base)`
- AND SHALL have weight `var(--dt-font-weight-normal)`

### Requirement: Tailwind v4 Integration

The `tokens.css` SHALL be imported in the app entry point. Tailwind v4 `@theme` directive SHALL reference the `--dt-*` variables.

- Tailwind colors: `bg-primary`, `bg-secondary`, `text-primary`, `accent`, `success`, `danger`, etc.
- Tailwind spacing: `dt-xs` through `dt-xxl` mapped to the 4px scale.
- Tailwind font sizes: `dt-xs` through `dt-xxl`.

#### Scenario: Tailwind utility applies token

- GIVEN a shadcn-svelte `Button` component uses Tailwind classes
- WHEN `bg-accent text-white` is applied
- THEN the background MUST evaluate to `#DAA520`
- AND the text color MUST be `#ffffff`

### Requirement: shadcn-svelte Theme Inheritance

shadcn-svelte CSS variables SHALL inherit from the design tokens. The `--primary` CSS var SHALL equal `--dt-color-accent`.

#### Scenario: shadcn Button renders with accent

- GIVEN a shadcn-svelte `Button` variant `"default"`
- WHEN it renders
- THEN `--primary` background SHALL be `#DAA520`
- AND `--primary-foreground` text SHALL be `#ffffff`
