# H12 Accessibility & Usability Report — HEMS-Link

- **Skip Navigation:** All 9 screens + Style Guide include a keyboard-accessible `<a class="skip-link" href="#main-content">` link.
- **Landmarks & Headings:** Semantic `<header role="banner">`, `<nav aria-label="Primary navigation">`, `<main id="main-content">`, and `<footer role="contentinfo">`.
- **Keyboard Focus:** High-contrast `:focus-visible` ring (`--focus-ring`) on all interactive keycap buttons, selects, and links.
- **No Color-Only Status:** Every status badge pairs an icon symbol (`●`, `▲`, `◆`, `■`) with explicit text.
- **Reduced Motion:** `@media (prefers-reduced-motion: reduce)` disables transitions and animations.
- **Accessible Data Alternatives:** Analytics charts are paired with a semantic `<table>` (`Algorithm Comparison`).
- **Multilingual Support (i18n):** Live `EN` / `HI` / `KN` switcher in the top bar.

