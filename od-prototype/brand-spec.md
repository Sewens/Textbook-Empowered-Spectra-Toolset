# JupyterLab-style brand spec

Source: `reference/variables.css` downloaded from `@jupyterlab/theme-light-extension`.

Observed anchors:
- Layout surfaces use white, near-white grey, and hairline grey borders: `#fff`, `#eee`, `#e0e0e0`, `#bdbdbd`.
- Primary brand/focus color comes from Material blue: `#1976d2`, with deep blue `#0d47a1` and pale blue `#e3f2fd`.
- UI typography is small, dense, and system-native: base UI `13px`, content `14px`, scale factor `1.2`.
- Radii are minimal: `--jp-border-radius: 2px`; borders are `1px`.

CSS tokens for this project:

```css
:root {
  --bg: oklch(97.8% 0.003 250);
  --surface: oklch(100% 0 0);
  --fg: oklch(24% 0.004 250);
  --muted: oklch(51% 0.006 250);
  --border: oklch(89% 0.004 250);
  --accent: oklch(56% 0.17 255);

  --font-display: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif;
  --font-body: 'Segoe UI Variable Text', 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'Cascadia Mono', 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
```

Layout posture rules:
- Use a top application route bar with compact 13px UI labels and visible active focus.
- Keep borders hairline and structural; avoid soft cards, heavy shadows, and large radii.
- Use blue sparingly for active routes, focus rings, selected tabs, and one primary action per screen.
- Treat `main_frame` as a workbench: left project tree, central active document/tool, right inspector or metadata panel.
- Prefer dense scientific modules: spectrum panes, corpus tables, extraction queues, provenance chips, and notebook-like status rows.
