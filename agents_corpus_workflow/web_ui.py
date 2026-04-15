from __future__ import annotations

import json


def render_index_html(overview: dict, enable_admin_actions: bool = False) -> str:
    overview_json = json.dumps(overview, ensure_ascii=False)
    admin_json = json.dumps(enable_admin_actions)
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agents Production Studio</title>
  <style>
    :root {
      --bg: #f3ede3;
      --bg-deep: #efe5d6;
      --surface: rgba(255, 252, 247, 0.92);
      --surface-strong: rgba(255, 255, 255, 0.98);
      --surface-soft: rgba(255, 248, 239, 0.84);
      --ink: #16211d;
      --muted: #5b655f;
      --line: rgba(22, 33, 29, 0.10);
      --line-strong: rgba(22, 33, 29, 0.16);
      --accent: #0d6c58;
      --accent-strong: #094b3e;
      --accent-soft: rgba(13, 108, 88, 0.10);
      --warm: #b76e35;
      --warm-soft: rgba(183, 110, 53, 0.12);
      --danger: #a1422c;
      --danger-soft: rgba(161, 66, 44, 0.10);
      --sidebar-bg: rgba(252, 248, 241, 0.94);
      --sidebar-line: rgba(22, 33, 29, 0.08);
      --sidebar-text: #173028;
      --sidebar-muted: #65756d;
      --shadow: 0 18px 42px rgba(15, 23, 20, 0.08);
      --shadow-strong: 0 26px 68px rgba(15, 23, 20, 0.14);
      --button-shadow: 0 16px 28px rgba(15, 23, 20, 0.08);
      --button-shadow-strong: 0 20px 34px rgba(13, 108, 88, 0.18);
      --radius-xl: 30px;
      --radius-lg: 22px;
      --radius-md: 16px;
      --radius-sm: 12px;
      --sidebar-width: 282px;
      --sidebar-collapsed: 112px;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(183, 110, 53, 0.14), transparent 28%),
        radial-gradient(circle at 82% 10%, rgba(13, 108, 88, 0.12), transparent 20%),
        linear-gradient(180deg, #f9f5ef 0%, #f4ede3 48%, #f8f4ee 100%);
      font-family: "Avenir Next", "Segoe UI Variable", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
      min-height: 100vh;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(22, 33, 29, 0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(22, 33, 29, 0.018) 1px, transparent 1px);
      background-size: 28px 28px;
      mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.42), transparent 88%);
    }
    code, pre, textarea, input, select, button {
      font-family: inherit;
    }
    pre, code {
      font-family: "IBM Plex Mono", "SFMono-Regular", "JetBrains Mono", monospace;
    }
    .app-shell {
      position: relative;
      z-index: 1;
      min-height: 100vh;
      display: grid;
      grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
      align-items: start;
      transition: grid-template-columns 0.24s ease;
    }
    .app-shell.sidebar-collapsed {
      grid-template-columns: var(--sidebar-collapsed) minmax(0, 1fr);
    }
    .sidebar {
      grid-column: 1;
      position: sticky;
      --sidebar-pad-x: 16px;
      --sidebar-pad-y: 18px;
      --sidebar-controls-space: 104px;
      top: 0;
      height: 100vh;
      width: 100%;
      min-width: 0;
      padding: var(--sidebar-pad-y) var(--sidebar-pad-x) var(--sidebar-controls-space);
      background:
        radial-gradient(circle at top right, rgba(13,108,88,0.08), transparent 24%),
        linear-gradient(180deg, rgba(255,252,247,0.96), rgba(246,240,232,0.96));
      border-right: 1px solid var(--sidebar-line);
      box-shadow: 10px 0 34px rgba(15, 23, 20, 0.05);
      display: grid;
      grid-template-rows: auto auto 1fr auto;
      gap: 18px;
      overflow: hidden;
      z-index: 10;
    }
    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(8, 14, 12, 0.40);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.18s ease;
      z-index: 8;
    }
    .sidebar-top {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 12px;
    }
    .sidebar-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .brand-mark {
      width: 44px;
      height: 44px;
      border-radius: 15px;
      display: grid;
      place-items: center;
      background: linear-gradient(145deg, rgba(13,108,88,1), rgba(9,75,62,0.96));
      color: #fff;
      font-weight: 800;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
      flex: 0 0 auto;
    }
    .brand-copy,
    .sidebar-note,
    .menu-copy,
    .sidebar-footer {
      transition: opacity 0.18s ease, transform 0.18s ease;
    }
    .brand-copy strong {
      display: block;
      color: var(--sidebar-text);
      font-size: 14px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .brand-copy span {
      display: block;
      margin-top: 4px;
      color: var(--sidebar-muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .sidebar-toggle,
    .close-btn {
      width: 44px;
      height: 44px;
      border: 1px solid rgba(22,33,29,0.10);
      border-radius: 14px;
      background: rgba(255,255,255,0.86);
      color: var(--sidebar-text);
      cursor: pointer;
      font-size: 16px;
      font-weight: 700;
      box-shadow: 0 10px 20px rgba(15, 23, 20, 0.06);
      transition: background 0.16s ease, transform 0.16s ease, border-color 0.16s ease;
    }
    .sidebar-toggle:hover,
    .close-btn:hover {
      background: rgba(255,255,255,0.98);
      border-color: rgba(13,108,88,0.18);
      transform: translateY(-1px);
    }
    .sidebar-controls {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      position: absolute;
      left: var(--sidebar-pad-x);
      right: var(--sidebar-pad-x);
      bottom: var(--sidebar-pad-y);
      padding-top: 0;
      border-top: none;
    }
    .sidebar-toggle-wrap {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px;
      border-radius: 18px;
      background: rgba(255,255,255,0.72);
      border: 1px solid rgba(22,33,29,0.08);
      box-shadow: 0 14px 24px rgba(15, 23, 20, 0.06);
    }
    .sidebar-toggle-copy {
      min-width: 0;
      color: var(--sidebar-muted);
      line-height: 1.4;
    }
    .sidebar-toggle-copy strong {
      display: block;
      color: var(--sidebar-text);
      font-size: 13px;
    }
    .sidebar-toggle-copy span {
      display: block;
      margin-top: 2px;
      font-size: 11px;
    }
    .sidebar-note {
      padding: 14px;
      border-radius: 18px;
      border: 1px solid rgba(22,33,29,0.08);
      background: rgba(255,255,255,0.66);
      color: var(--sidebar-muted);
      font-size: 12px;
      line-height: 1.7;
    }
    .sidebar-note strong {
      display: block;
      margin-bottom: 6px;
      color: var(--sidebar-text);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .menu {
      display: grid;
      align-content: start;
      gap: 10px;
      min-height: 0;
      overflow-y: auto;
      padding-right: 4px;
    }
    .menu-button {
      width: 100%;
      padding: 12px;
      border: 1px solid transparent;
      border-radius: 18px;
      background: transparent;
      color: var(--sidebar-muted);
      display: grid;
      grid-template-columns: 44px minmax(0, 1fr);
      gap: 12px;
      align-items: center;
      text-align: left;
      cursor: pointer;
      transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
      position: relative;
      overflow: hidden;
    }
    .menu-button[data-label]::after {
      content: attr(data-label);
      position: absolute;
      left: calc(100% + 14px);
      top: 50%;
      transform: translateY(-50%) translateX(-4px);
      opacity: 0;
      pointer-events: none;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(17, 28, 25, 0.96);
      color: rgba(246, 242, 235, 0.96);
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 14px 28px rgba(8, 14, 12, 0.22);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      white-space: nowrap;
      transition: opacity 0.16s ease, transform 0.16s ease;
      z-index: 20;
    }
    .menu-button::before {
      content: "";
      position: absolute;
      left: 0;
      top: 10px;
      bottom: 10px;
      width: 0;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(212, 245, 235, 0.74));
      transition: width 0.18s ease;
    }
    .menu-button:hover {
      background: rgba(255,255,255,0.78);
      border-color: rgba(22,33,29,0.08);
      transform: translateY(-1px);
    }
    .menu-button.active {
      background: linear-gradient(180deg, rgba(13,108,88,0.16), rgba(13,108,88,0.06));
      border-color: rgba(13,108,88,0.24);
      color: var(--accent-strong);
      transform: translateX(2px);
    }
    .menu-button.active::before {
      width: 4px;
    }
    .menu-icon {
      width: 44px;
      height: 44px;
      border-radius: 15px;
      background: rgba(13,108,88,0.06);
      border: 1px solid rgba(13,108,88,0.10);
      display: grid;
      place-items: center;
      color: var(--accent-strong);
      font-size: 14px;
      font-weight: 700;
      position: relative;
      z-index: 1;
    }
    .menu-icon svg,
    .sidebar-toggle svg,
    .topbar-nav-btn svg {
      width: 18px;
      height: 18px;
      stroke: currentColor;
      fill: none;
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
      vector-effect: non-scaling-stroke;
    }
    .menu-copy strong {
      display: block;
      color: inherit;
      font-size: 14px;
    }
    .menu-copy span {
      display: block;
      margin-top: 4px;
      color: inherit;
      opacity: 0.75;
      font-size: 12px;
      line-height: 1.5;
    }
    .sidebar-footer {
      padding: 14px;
      border-top: 1px solid rgba(22,33,29,0.08);
      color: var(--sidebar-muted);
      font-size: 12px;
      line-height: 1.7;
    }
    .sidebar-footer strong {
      display: block;
      margin-bottom: 6px;
      color: var(--sidebar-text);
      font-size: 12px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .app-shell.sidebar-collapsed .brand-copy,
    .app-shell.sidebar-collapsed .sidebar-note,
    .app-shell.sidebar-collapsed .sidebar-footer {
      opacity: 0;
      transform: translateX(-12px);
      pointer-events: none;
    }
    .app-shell.sidebar-collapsed .brand-copy {
      display: none;
    }
    .app-shell.sidebar-collapsed .sidebar-note,
    .app-shell.sidebar-collapsed .sidebar-footer {
      display: none;
    }
    .app-shell.sidebar-collapsed .sidebar {
      --sidebar-pad-x: 16px;
    }
    .app-shell.sidebar-collapsed .sidebar-top {
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      gap: 14px;
    }
    .app-shell.sidebar-collapsed .sidebar-brand {
      justify-content: center;
    }
    .app-shell.sidebar-collapsed .sidebar-controls {
      justify-content: flex-start;
    }
    .app-shell.sidebar-collapsed .sidebar-toggle-wrap {
      width: auto;
      justify-content: flex-start;
      padding: 10px 8px;
      border-radius: 20px;
    }
    .app-shell.sidebar-collapsed .sidebar-toggle-copy {
      display: none;
    }
    .app-shell.sidebar-collapsed .menu {
      gap: 12px;
    }
    .app-shell.sidebar-collapsed .menu-button {
      grid-template-columns: 1fr;
      justify-items: center;
      gap: 8px;
      min-height: 86px;
      padding: 12px 8px 10px;
      text-align: center;
      border-radius: 20px;
    }
    .app-shell.sidebar-collapsed .menu-button::after {
      display: none;
    }
    .app-shell.sidebar-collapsed .menu-button.active {
      transform: none;
    }
    .app-shell.sidebar-collapsed .menu-copy {
      opacity: 1;
      transform: none;
      pointer-events: auto;
      text-align: center;
    }
    .app-shell.sidebar-collapsed .menu-copy strong {
      font-size: 12px;
      line-height: 1.25;
      white-space: normal;
    }
    .app-shell.sidebar-collapsed .menu-copy span {
      display: none;
    }
    .main {
      grid-column: 2;
      min-width: 0;
      padding: 22px 24px 30px;
    }
    .topbar {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 20px;
    }
    .topbar-start {
      display: flex;
      align-items: flex-start;
      gap: 14px;
      min-width: 0;
      flex: 1 1 auto;
    }
    .topbar-nav-btn {
      display: none;
      width: 46px;
      height: 46px;
      padding: 0;
      border: 1px solid rgba(22,33,29,0.10);
      border-radius: 15px;
      background: rgba(255,255,255,0.88);
      color: var(--sidebar-text);
      box-shadow: 0 12px 24px rgba(15, 23, 20, 0.06);
      cursor: pointer;
      align-items: center;
      justify-content: center;
      transition: background 0.16s ease, transform 0.16s ease, border-color 0.16s ease;
      flex: 0 0 auto;
    }
    .topbar-nav-btn:hover {
      background: rgba(255,255,255,0.98);
      border-color: rgba(13,108,88,0.18);
      transform: translateY(-1px);
    }
    .topbar-copy {
      min-width: 0;
    }
    .topbar-copy h1 {
      margin: 0;
      font-size: clamp(30px, 3vw, 42px);
      line-height: 1.04;
      letter-spacing: -0.03em;
    }
    .topbar-copy p {
      margin: 10px 0 0;
      max-width: 760px;
      color: var(--muted);
      line-height: 1.7;
    }
    .topbar-actions {
      display: flex;
      flex-wrap: nowrap;
      justify-content: flex-end;
      gap: 10px;
      align-items: stretch;
      flex: 0 1 auto;
      min-width: 0;
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--warm-soft);
      color: var(--warm);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .panel,
    .surface-card,
    .field,
    .builder-card,
    .summary-card,
    .drawer-section {
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
    }
    .panel {
      border-radius: var(--radius-xl);
      padding: 26px;
    }
    .screen {
      display: none;
    }
    .screen.active {
      display: block;
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.8fr);
      gap: 18px;
      margin-bottom: 18px;
    }
    .hero-copy p {
      margin: 0;
      color: var(--muted);
      line-height: 1.8;
      max-width: 760px;
    }
    .hero-copy h2 {
      margin: 0 0 12px;
      font-size: clamp(28px, 3vw, 40px);
      line-height: 1.06;
      letter-spacing: -0.03em;
    }
    .hero-actions,
    .hero-pills,
    .chip-wrap,
    .drawer-actions,
    .result-actions,
    .toolbar-actions,
    .summary-list,
    .result-meta,
    .detail-grid,
    .meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .hero-pills {
      margin-top: 18px;
    }
    .hero-side {
      border-radius: var(--radius-lg);
      padding: 22px;
      background:
        radial-gradient(circle at top right, rgba(13,108,88,0.12), transparent 28%),
        linear-gradient(180deg, rgba(255,255,255,0.76), rgba(255,249,242,0.88));
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }
    .hero-side h3,
    .section-head h2,
    .drawer-head h3,
    .result-shell h2,
    .step-card h3 {
      margin: 0;
      font-size: 22px;
      letter-spacing: -0.02em;
    }
    .hero-side p,
    .section-head p,
    .panel-text,
    .drawer-summary,
    .step-note,
    .summary-item span,
    .field-help {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
    }
    .section-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 18px;
    }
    .workspace-shell {
      display: grid;
      grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.65fr);
      gap: 18px;
    }
    .progress-column {
      display: grid;
      gap: 18px;
      align-content: start;
    }
    .progress-card,
    .template-card,
    .result-side,
    .library-toolbar,
    .drawer {
      border-radius: var(--radius-lg);
    }
    .progress-card {
      padding: 22px;
    }
    .step-list {
      display: grid;
      gap: 10px;
      margin-top: 16px;
    }
    .step-button {
      width: 100%;
      padding: 14px 16px;
      border: 1px solid transparent;
      border-radius: 16px;
      background: rgba(255,255,255,0.46);
      color: var(--ink);
      text-align: left;
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
    }
    .step-button:hover {
      transform: translateY(-1px);
      border-color: var(--line-strong);
      background: rgba(255,255,255,0.78);
    }
    .step-button.active {
      border-color: rgba(13,108,88,0.32);
      background: linear-gradient(180deg, rgba(13,108,88,0.12), rgba(13,108,88,0.04));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
    }
    .step-button strong {
      display: block;
      font-size: 14px;
    }
    .step-button span {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }
    .template-card {
      padding: 22px;
      background:
        radial-gradient(circle at top right, rgba(183,110,53,0.10), transparent 30%),
        linear-gradient(180deg, rgba(255,252,247,0.92), rgba(255,247,237,0.88));
    }
    .template-card ul,
    .hero-side ul,
    .result-side ul,
    .drawer ul {
      margin: 14px 0 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.7;
    }
    .form-card {
      padding: 26px;
      border-radius: var(--radius-xl);
    }
    .status {
      margin-bottom: 18px;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--accent-soft);
      color: var(--accent-strong);
      font-size: 14px;
      line-height: 1.7;
      border: 1px solid rgba(13,108,88,0.16);
    }
    .status.error {
      background: var(--danger-soft);
      color: var(--danger);
      border-color: rgba(161,66,44,0.20);
    }
    .progress-status[hidden] {
      display: none;
    }
    .progress-status {
      margin-bottom: 18px;
      padding: 16px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,243,236,0.92));
      border: 1px solid rgba(22,33,29,0.10);
      box-shadow: 0 16px 28px rgba(15, 23, 20, 0.06);
      display: grid;
      gap: 12px;
    }
    .progress-status.done {
      border-color: rgba(13,108,88,0.18);
      background: linear-gradient(180deg, rgba(248,255,252,0.96), rgba(241,248,244,0.94));
    }
    .progress-status.error {
      border-color: rgba(161,66,44,0.18);
      background: linear-gradient(180deg, rgba(255,250,248,0.96), rgba(250,241,238,0.94));
    }
    .progress-status.error .progress-bar-fill {
      background: linear-gradient(90deg, rgba(161,66,44,0.92), rgba(183,110,53,0.80));
    }
    .progress-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .progress-head strong {
      font-size: 14px;
      color: var(--ink);
    }
    .progress-head span {
      font-size: 12px;
      color: var(--muted);
    }
    .progress-bar {
      width: 100%;
      height: 10px;
      border-radius: 999px;
      background: rgba(22,33,29,0.08);
      overflow: hidden;
    }
    .progress-bar-fill {
      height: 100%;
      width: 0%;
      border-radius: inherit;
      background: linear-gradient(90deg, rgba(13,108,88,0.92), rgba(183,110,53,0.78));
      transition: width 0.28s ease;
    }
    .progress-detail {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      font-size: 13px;
    }
    .question-shell,
    .plan-shell {
      display: grid;
      gap: 16px;
    }
    .question-summary-pills,
    .plan-summary-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .question-list {
      display: grid;
      gap: 14px;
    }
    .question-card {
      padding: 18px;
      border-radius: 20px;
      border: 1px solid rgba(22,33,29,0.08);
      background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(249,244,236,0.88));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.72);
      display: grid;
      gap: 14px;
      scroll-margin-top: 120px;
      scroll-margin-bottom: 120px;
    }
    .question-card.invalid {
      border-color: rgba(161,66,44,0.26);
      box-shadow: 0 0 0 4px rgba(161,66,44,0.08), inset 0 1px 0 rgba(255,255,255,0.72);
    }
    .question-card.ignored {
      opacity: 0.68;
      background: linear-gradient(180deg, rgba(245, 241, 235, 0.92), rgba(238, 233, 225, 0.86));
      border-style: dashed;
      border-color: rgba(22,33,29,0.12);
      box-shadow: none;
    }
    .question-card.ignored.invalid {
      box-shadow: none;
    }
    .question-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    .question-head h4 {
      margin: 0;
      font-size: 17px;
      letter-spacing: -0.01em;
    }
    .question-kicker {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--warm);
    }
    .question-description {
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.7;
    }
    .question-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 30px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid rgba(13,108,88,0.16);
      background: rgba(13,108,88,0.10);
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
      flex: 0 0 auto;
    }
    .question-badge.optional {
      border-color: rgba(22,33,29,0.08);
      background: rgba(255,255,255,0.78);
      color: var(--muted);
    }
    .question-options {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }
    .question-option {
      width: 100%;
      padding: 13px 14px;
      border-radius: 16px;
      border: 1px solid rgba(22,33,29,0.10);
      background: rgba(255,255,255,0.88);
      color: var(--ink);
      text-align: left;
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
      display: grid;
      gap: 6px;
      box-shadow: 0 10px 18px rgba(15, 23, 20, 0.04);
    }
    .question-option:hover {
      transform: translateY(-1px);
      border-color: rgba(13,108,88,0.18);
      background: rgba(255,255,255,0.98);
    }
    .question-option.active {
      border-color: rgba(13,108,88,0.24);
      background: linear-gradient(180deg, rgba(13,108,88,0.14), rgba(13,108,88,0.06));
      color: var(--accent-strong);
      box-shadow: 0 14px 24px rgba(13, 108, 88, 0.08);
    }
    .question-option strong {
      font-size: 13px;
    }
    .question-option small {
      font-size: 12px;
      color: inherit;
      opacity: 0.76;
      line-height: 1.5;
    }
    .question-error {
      color: var(--danger);
    }
    .question-mode-note,
    .question-suggestion-card {
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid rgba(13,108,88,0.14);
      background: linear-gradient(180deg, rgba(248,255,252,0.94), rgba(242,248,244,0.90));
      display: grid;
      gap: 10px;
    }
    .question-mode-note strong,
    .question-suggestion-card strong {
      font-size: 13px;
      color: var(--accent-strong);
    }
    .question-mode-note p,
    .question-suggestion-card p {
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
      font-size: 13px;
    }
    .question-suggestion-list {
      margin: 0;
      padding-left: 18px;
      color: var(--ink);
      line-height: 1.7;
      font-size: 13px;
    }
    .question-suggestion-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .question-suggestion-actions .button-secondary,
    .question-suggestion-actions .button-quiet {
      min-height: 38px;
      padding: 8px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 700;
    }
    .question-custom-entry {
      display: grid;
      gap: 10px;
    }
    .question-custom-entry.inline {
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
    }
    .question-custom-entry[hidden] {
      display: none;
    }
    .question-custom-entry .button-secondary,
    .question-custom-entry .button-quiet {
      min-height: 44px;
      padding: 10px 14px;
      border-radius: 14px;
    }
    .question-input[disabled],
    .question-select[disabled],
    textarea[disabled] {
      cursor: not-allowed;
      opacity: 0.72;
      background: rgba(244, 239, 233, 0.92);
    }
    .question-inline-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .question-inline-actions .button-link,
    .question-inline-actions .button-quiet {
      min-height: 38px;
      padding: 8px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 700;
    }
    .plan-summary {
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid rgba(22,33,29,0.08);
      background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(250,245,238,0.90));
      display: grid;
      gap: 10px;
    }
    .plan-summary h4 {
      margin: 0;
      font-size: 15px;
    }
    .plan-summary ul {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.7;
    }
    .plan-preview {
      max-height: 56vh;
    }
    .result-plan-card {
      margin-top: 18px;
      padding: 24px;
      border-radius: var(--radius-xl);
    }
    .form-step {
      display: none;
    }
    .form-step.active {
      display: block;
    }
    .step-card {
      display: grid;
      gap: 18px;
    }
    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .field {
      padding: 16px;
      border-radius: 18px;
    }
    .field.full {
      grid-column: 1 / -1;
    }
    label {
      display: block;
      margin-bottom: 10px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    input,
    select,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 13px 14px;
      background: rgba(255,255,255,0.92);
      color: var(--ink);
      font-size: 14px;
      outline: none;
      transition: border-color 0.16s ease, box-shadow 0.16s ease;
    }
    input:focus,
    select:focus,
    textarea:focus {
      border-color: rgba(13,108,88,0.34);
      box-shadow: 0 0 0 4px rgba(13,108,88,0.10);
    }
    textarea {
      min-height: 128px;
      resize: vertical;
      line-height: 1.7;
    }
    .other-input {
      display: none;
      margin-top: 10px;
    }
    .other-input.visible {
      display: block;
    }
    .selection-group {
      display: grid;
      gap: 14px;
    }
    .option-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .option-chip,
    .selected-tag {
      min-height: 42px;
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(22,33,29,0.10);
      background: rgba(255,255,255,0.86);
      color: var(--ink);
      font-size: 13px;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
      box-shadow: 0 10px 20px rgba(15, 23, 20, 0.05);
    }
    .option-chip:hover,
    .selected-tag:hover {
      transform: translateY(-1px);
      border-color: rgba(13,108,88,0.18);
      background: rgba(255,255,255,0.98);
    }
    .option-chip.active {
      background: linear-gradient(180deg, rgba(13,108,88,0.14), rgba(13,108,88,0.06));
      border-color: rgba(13,108,88,0.24);
      color: var(--accent-strong);
      box-shadow: 0 14px 24px rgba(13, 108, 88, 0.08);
    }
    .option-chip.freeform {
      border-style: dashed;
      color: var(--warm);
      background: rgba(183,110,53,0.08);
    }
    .custom-entry {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
    }
    .selected-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      min-height: 10px;
    }
    .selected-tag {
      cursor: default;
      background: rgba(13,108,88,0.08);
      border-color: rgba(13,108,88,0.18);
      color: var(--accent-strong);
      box-shadow: none;
    }
    .selected-tag button {
      width: 22px;
      height: 22px;
      border: none;
      border-radius: 999px;
      background: rgba(13,108,88,0.12);
      color: inherit;
      cursor: pointer;
      font: inherit;
      line-height: 1;
      padding: 0;
      display: inline-grid;
      place-items: center;
    }
    .summary-card {
      padding: 18px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,248,239,0.88));
    }
    .summary-card h4,
    .drawer-section h4,
    .result-side h3 {
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: 0.01em;
    }
    .summary-list {
      display: grid;
      gap: 10px;
    }
    .summary-item {
      display: grid;
      gap: 6px;
    }
    .summary-item strong {
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .form-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 22px;
      padding: 16px 18px;
      border: 1px solid rgba(22,33,29,0.10);
      border-radius: 18px;
      background: rgba(255,252,247,0.94);
      backdrop-filter: blur(16px);
      box-shadow: 0 18px 30px rgba(15, 23, 20, 0.08);
      position: sticky;
      bottom: 12px;
      z-index: 6;
    }
    .button-primary,
    .button-secondary,
    .button-quiet,
    .button-link {
      position: relative;
      overflow: hidden;
      min-height: 46px;
      border: 1px solid transparent;
      border-radius: 16px;
      padding: 12px 18px;
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      text-decoration: none;
      transition: transform 0.16s ease, background 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, color 0.16s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      white-space: nowrap;
      box-shadow: var(--button-shadow);
    }
    .button-primary {
      background: linear-gradient(145deg, rgba(13,108,88,1), rgba(9,75,62,0.94));
      color: #fff;
      border-color: rgba(8, 63, 51, 0.32);
      box-shadow: var(--button-shadow-strong);
    }
    .button-primary::after {
      content: "";
      position: absolute;
      inset: 1px;
      border-radius: 15px;
      background: linear-gradient(180deg, rgba(255,255,255,0.12), transparent 42%);
      pointer-events: none;
    }
    .button-secondary {
      background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,240,231,0.92));
      color: var(--ink);
      border-color: rgba(22, 33, 29, 0.12);
      box-shadow: 0 12px 24px rgba(15, 23, 20, 0.07);
    }
    .button-quiet,
    .button-link {
      background: rgba(255, 252, 247, 0.56);
      color: var(--accent-strong);
      border-color: rgba(13, 108, 88, 0.14);
      box-shadow: none;
    }
    .button-primary:hover,
    .button-secondary:hover,
    .button-quiet:hover,
    .button-link:hover {
      transform: translateY(-2px);
    }
    .button-primary:hover {
      box-shadow: 0 24px 38px rgba(13, 108, 88, 0.22);
    }
    .button-secondary:hover {
      box-shadow: 0 18px 30px rgba(15, 23, 20, 0.10);
      border-color: rgba(22, 33, 29, 0.18);
    }
    .button-quiet:hover,
    .button-link:hover {
      background: rgba(13, 108, 88, 0.08);
      border-color: rgba(13, 108, 88, 0.22);
    }
    .button-primary:disabled,
    .button-secondary:disabled,
    .button-quiet:disabled {
      opacity: 0.55;
      pointer-events: none;
      transform: none;
    }
    .button-primary:active,
    .button-secondary:active,
    .button-quiet:active,
    .button-link:active {
      transform: translateY(0);
    }
    .pill,
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 34px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.78);
      font-size: 12px;
      color: var(--muted);
    }
    .pill strong,
    .chip strong {
      color: var(--ink);
      font-size: 12px;
    }
    .chip.alt {
      background: var(--accent-soft);
      border-color: rgba(13,108,88,0.18);
      color: var(--accent-strong);
    }
    .toolbar {
      display: grid;
      grid-template-columns: 2fr repeat(3, minmax(140px, 1fr)) auto;
      gap: 12px;
      margin-bottom: 14px;
    }
    .library-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .library-card {
      padding: 20px;
      border-radius: 22px;
      border: 1px solid var(--line);
      background:
        radial-gradient(circle at top right, rgba(13,108,88,0.08), transparent 26%),
        linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,247,238,0.90));
      box-shadow: var(--shadow);
      display: grid;
      gap: 14px;
    }
    .library-card h3 {
      margin: 0;
      font-size: 20px;
      letter-spacing: -0.02em;
    }
    .library-card p {
      margin: 0;
      color: var(--muted);
      line-height: 1.72;
    }
    .library-actions,
    .card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .card-meta {
      color: var(--muted);
      font-size: 12px;
    }
    .result-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(300px, 0.8fr);
      gap: 18px;
    }
    .result-shell,
    .result-side {
      padding: 24px;
    }
    .section-inline {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .segment-switch {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px;
      border-radius: 16px;
      background: rgba(255,255,255,0.84);
      border: 1px solid rgba(22,33,29,0.08);
      box-shadow: 0 10px 20px rgba(15, 23, 20, 0.04);
    }
    .segment-switch button {
      min-height: 36px;
      padding: 8px 12px;
      border: 1px solid transparent;
      border-radius: 12px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font-size: 13px;
      font-weight: 700;
      transition: background 0.16s ease, color 0.16s ease, border-color 0.16s ease;
    }
    .segment-switch button.active {
      background: linear-gradient(180deg, rgba(13,108,88,0.14), rgba(13,108,88,0.06));
      border-color: rgba(13,108,88,0.18);
      color: var(--accent-strong);
    }
    .segment-switch button:disabled {
      opacity: 0.45;
      cursor: default;
    }
    .stage-note {
      margin: 14px 0 0;
      color: var(--muted);
      line-height: 1.7;
    }
    .markdown-box,
    .drawer-markdown {
      margin: 0;
      padding: 0;
      border-radius: 18px;
      border: 1px solid rgba(20, 30, 26, 0.08);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.98), rgba(251,248,242,0.96));
      color: #24312c;
      white-space: normal;
      line-height: 1.7;
      overflow: auto;
      max-height: 68vh;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.70);
    }
    .code-lines {
      display: block;
      min-width: 100%;
    }
    .code-line {
      display: grid;
      grid-template-columns: 72px minmax(0, 1fr);
      align-items: stretch;
      min-width: 100%;
      border-bottom: 1px solid rgba(22,33,29,0.06);
    }
    .code-line:nth-child(odd) {
      background: rgba(255,255,255,0.50);
    }
    .code-line:last-child {
      border-bottom: none;
    }
    .code-line-no {
      position: sticky;
      left: 0;
      z-index: 1;
      padding: 10px 12px 10px 18px;
      border-right: 1px solid rgba(22,33,29,0.08);
      background: linear-gradient(180deg, rgba(243,236,224,0.96), rgba(239,231,217,0.96));
      color: rgba(91,101,95,0.90);
      text-align: right;
      user-select: none;
    }
    .code-line-text {
      display: block;
      padding: 10px 18px;
      white-space: pre-wrap;
      word-break: break-word;
      color: #20312a;
    }
    .reference-list {
      display: grid;
      gap: 12px;
    }
    .reference-item {
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid rgba(22,33,29,0.08);
      background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(249,245,238,0.86));
      display: grid;
      gap: 6px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.70);
    }
    .reference-item strong {
      font-size: 13px;
      color: var(--ink);
    }
    .reference-item code {
      display: block;
      font-size: 12px;
      color: #7c5436;
      word-break: break-word;
      white-space: pre-wrap;
    }
    .reference-item span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.6;
    }
    .empty-state {
      padding: 24px;
      border-radius: 18px;
      border: 1px dashed var(--line-strong);
      background: rgba(255,255,255,0.54);
      color: var(--muted);
      text-align: center;
      line-height: 1.7;
    }
    .pill-button {
      appearance: none;
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
    }
    .pill-button:hover {
      transform: translateY(-1px);
      border-color: rgba(13,108,88,0.22);
      background: rgba(255,255,255,0.94);
    }
    .topbar-card,
    .model-status-button {
      min-height: 56px;
      padding: 10px 14px;
      border-radius: 18px;
      border: 1px solid rgba(22,33,29,0.10);
      background:
        radial-gradient(circle at top right, rgba(13,108,88,0.08), transparent 24%),
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,243,236,0.92));
      box-shadow: 0 16px 28px rgba(15, 23, 20, 0.08);
    }
    .model-status-button {
      min-width: 0;
      width: min(336px, 100%);
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      text-align: left;
      color: var(--ink);
    }
    .topbar-card {
      min-width: 0;
      display: grid;
      align-content: center;
      gap: 4px;
    }
    .topbar-summary-card {
      width: 208px;
      flex: 0 0 208px;
      gap: 10px;
      padding-top: 12px;
      padding-bottom: 12px;
    }
    .topbar-summary-head {
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .topbar-summary-list {
      display: grid;
      gap: 8px;
    }
    .topbar-summary-item {
      display: grid;
      gap: 2px;
    }
    .topbar-summary-item + .topbar-summary-item {
      padding-top: 8px;
      border-top: 1px solid rgba(22,33,29,0.08);
    }
    .model-status-button.is-disabled {
      background:
        radial-gradient(circle at top right, rgba(161,66,44,0.08), transparent 24%),
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,243,236,0.92));
    }
    .topbar-card strong {
      color: var(--ink);
      font-size: 13px;
      line-height: 1.35;
    }
    .topbar-card span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .model-status-main {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .model-status-dot {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(13,108,88,0.12);
      flex: 0 0 auto;
    }
    .model-status-button.is-disabled .model-status-dot {
      background: var(--danger);
      box-shadow: 0 0 0 6px rgba(161,66,44,0.10);
    }
    .model-status-copy {
      display: grid;
      gap: 3px;
      min-width: 0;
    }
    .model-status-copy strong {
      color: var(--ink);
      font-size: 13px;
    }
    .model-status-copy span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 220px;
    }
    .model-status-cta {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(13,108,88,0.10);
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
      flex: 0 0 auto;
    }
    .model-status-button.is-disabled .model-status-cta {
      background: rgba(161,66,44,0.10);
      color: var(--danger);
    }
    .model-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(8, 14, 12, 0.44);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.18s ease;
      z-index: 20;
    }
    .model-modal {
      position: fixed;
      inset: 0;
      padding: 28px;
      display: grid;
      place-items: center;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.18s ease;
      z-index: 21;
    }
    .model-modal.open,
    .model-modal-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }
    .model-modal-shell {
      width: min(1120px, calc(100vw - 36px));
      max-height: calc(100vh - 36px);
      overflow: auto;
      border-radius: 28px;
      padding: 24px;
    }
    .model-modal-body {
      display: grid;
      gap: 18px;
    }
    .model-section {
      padding: 20px;
      border-radius: 22px;
      border: 1px solid rgba(22,33,29,0.08);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.90), rgba(248,243,236,0.84));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.72);
    }
    .model-section-head {
      margin-bottom: 16px;
      align-items: center;
    }
    .model-section-head h3 {
      margin: 0;
      font-size: 18px;
      letter-spacing: -0.02em;
    }
    .model-flow-note {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.7;
    }
    .model-overview-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .overview-stat {
      padding: 0 0 0 16px;
      border-left: 1px solid rgba(22,33,29,0.08);
      display: grid;
      gap: 6px;
    }
    .overview-stat:first-child {
      padding-left: 0;
      border-left: none;
    }
    .overview-stat strong {
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .overview-stat span {
      font-size: 15px;
      color: var(--ink);
      line-height: 1.5;
    }
    .model-toggle-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      align-items: stretch;
      margin-top: 18px;
    }
    .model-command-group,
    .admin-token-card {
      display: grid;
      align-content: start;
      gap: 14px;
      min-height: 100%;
      padding: 18px 20px;
      border-radius: 20px;
      border: 1px solid rgba(22,33,29,0.06);
      background: rgba(255,255,255,0.66);
      box-shadow: none;
    }
    .model-command-group h3,
    .admin-token-card h3 {
      margin: 0 0 8px;
      font-size: 16px;
      letter-spacing: -0.01em;
    }
    .model-command-group p,
    .admin-token-card p {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
    }
    .model-command-copy {
      display: grid;
      align-content: start;
      gap: 8px;
      min-height: 74px;
    }
    .mode-card-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .mode-card {
      width: 100%;
      padding: 16px;
      border-radius: 18px;
      border: 1px solid rgba(22,33,29,0.10);
      background: rgba(255,255,255,0.72);
      text-align: left;
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.74);
    }
    .mode-card:hover {
      transform: translateY(-1px);
      border-color: rgba(13,108,88,0.20);
      background: rgba(255,255,255,0.94);
    }
    .mode-card.active {
      border-color: rgba(13,108,88,0.28);
      background: linear-gradient(180deg, rgba(13,108,88,0.14), rgba(13,108,88,0.06));
      box-shadow: 0 14px 28px rgba(13,108,88,0.10);
    }
    .mode-card.negative.active {
      border-color: rgba(161,66,44,0.26);
      background: linear-gradient(180deg, rgba(161,66,44,0.12), rgba(161,66,44,0.05));
      box-shadow: 0 14px 28px rgba(161,66,44,0.08);
    }
    .mode-card strong {
      display: block;
      font-size: 15px;
      color: var(--ink);
    }
    .mode-card em {
      display: inline-flex;
      align-items: center;
      margin-bottom: 8px;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(13,108,88,0.10);
      color: var(--accent-strong);
      font-style: normal;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .mode-card.negative em {
      background: rgba(161,66,44,0.10);
      color: var(--danger);
    }
    .mode-card span {
      display: block;
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.6;
    }
    .admin-token-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      min-height: 74px;
    }
    .token-visibility-btn {
      min-width: 96px;
      flex: 0 0 auto;
    }
    .field-inline-label {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      color: var(--ink);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .field-inline-label code {
      font-size: 11px;
      color: var(--accent-strong);
    }
    .admin-token-card {
      background:
        radial-gradient(circle at top right, rgba(13,108,88,0.12), transparent 26%),
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,242,235,0.92));
    }
    .admin-token-card input {
      border-width: 1.5px;
      background: rgba(255,255,255,0.96);
    }
    .admin-token-card input:focus {
      border-color: rgba(13,108,88,0.36);
      box-shadow: 0 0 0 4px rgba(13,108,88,0.10);
    }
    .admin-token-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      margin-top: 14px;
    }
    .token-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(183,110,53,0.12);
      color: var(--warm);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .token-focus-note {
      margin-top: 10px;
      font-size: 12px;
      color: var(--muted);
    }
    .token-inline-status {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: -2px;
    }
    .model-config-section #model-source-panel,
    .model-config-section #model-config-fields .field,
    .model-validation-block,
    .model-runtime-block,
    .model-runtime-side,
    .model-runtime-side .drawer-section {
      padding: 0;
      border: none;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      backdrop-filter: none;
    }
    .model-config-section #model-source-panel {
      margin-bottom: 16px;
    }
    .model-config-grid {
      gap: 18px;
    }
    .model-config-grid .field {
      padding-top: 2px;
    }
    .model-config-grid .field.full {
      padding-top: 6px;
      border-top: 1px solid rgba(22,33,29,0.08);
    }
    .model-validation-block {
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid rgba(22,33,29,0.08);
    }
    .model-validation-block h4,
    .model-runtime-side .drawer-section h4 {
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: -0.01em;
    }
    .model-runtime-layout {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      align-items: start;
    }
    .model-runtime-block h3 {
      margin: 0 0 14px;
    }
    .model-runtime-side {
      display: grid;
      gap: 14px;
    }
    .model-runtime-side .drawer-section + .drawer-section {
      padding-top: 14px;
      border-top: 1px solid rgba(22,33,29,0.08);
    }
    .drawer-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(8, 14, 12, 0.38);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.18s ease;
      z-index: 18;
    }
    .drawer {
      position: fixed;
      top: 0;
      right: 0;
      width: min(720px, 100vw);
      height: 100vh;
      padding: 24px;
      background:
        radial-gradient(circle at top right, rgba(183,110,53,0.10), transparent 24%),
        linear-gradient(180deg, rgba(255,253,249,0.98), rgba(252,246,238,0.97));
      box-shadow: var(--shadow-strong);
      transform: translateX(104%);
      transition: transform 0.22s ease;
      z-index: 19;
      display: grid;
      grid-template-rows: auto auto auto 1fr;
      gap: 16px;
      overflow: hidden;
    }
    .drawer.open {
      transform: translateX(0);
    }
    .drawer-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }
    .drawer-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    .drawer-head p {
      margin: 10px 0 0;
    }
    .drawer-body {
      min-height: 0;
      overflow: auto;
      padding-right: 2px;
      display: grid;
      gap: 14px;
    }
    .drawer-section {
      padding: 18px;
      border-radius: 18px;
    }
    .detail-list {
      display: grid;
      gap: 10px;
    }
    .detail-item {
      display: grid;
      gap: 4px;
    }
    .detail-item strong {
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .meta-row {
      gap: 8px;
    }
    .footer-note {
      margin-top: 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.7;
      text-align: right;
    }
    @media (max-width: 1180px) {
      .hero,
      .workspace-shell,
      .result-layout {
        grid-template-columns: 1fr;
      }
      .library-grid {
        grid-template-columns: 1fr;
      }
      .toolbar {
        grid-template-columns: 1fr 1fr;
      }
      .toolbar .field:first-child {
        grid-column: 1 / -1;
      }
    }
    @media (max-width: 960px) {
      .app-shell {
        grid-template-columns: 1fr;
      }
      .sidebar {
        position: fixed;
        left: 0;
        width: min(84vw, var(--sidebar-width));
        max-width: 320px;
        transform: translateX(0);
        z-index: 12;
      }
      .app-shell.sidebar-collapsed .sidebar {
        transform: translateX(-100%);
      }
      .app-shell.sidebar-collapsed {
        grid-template-columns: 1fr;
      }
      .app-shell:not(.sidebar-collapsed) .sidebar-backdrop {
        opacity: 1;
        pointer-events: auto;
      }
      .main {
        grid-column: 1;
        padding: 18px;
      }
      .topbar {
        flex-direction: column;
      }
      .topbar-start {
        width: 100%;
      }
      .sidebar-controls {
        display: none;
      }
      .topbar-nav-btn {
        display: inline-flex;
      }
      .topbar-actions {
        justify-content: flex-start;
        flex-wrap: wrap;
      }
      .topbar-card,
      .model-status-button {
        width: 100%;
        min-width: 0;
      }
      .topbar-summary-card {
        flex-basis: auto;
      }
    }
    @media (max-width: 720px) {
      .panel,
      .form-card,
      .result-shell,
      .result-side {
        padding: 20px;
      }
      .field-grid,
      .toolbar,
      .custom-entry {
        grid-template-columns: 1fr;
      }
      .form-actions {
        flex-direction: column;
        align-items: stretch;
      }
      .drawer {
        padding: 18px;
      }
      .model-modal {
        padding: 14px;
      }
      .model-modal-shell {
        width: 100%;
        max-height: calc(100vh - 16px);
        padding: 18px;
      }
      .model-toggle-row {
        grid-template-columns: 1fr;
      }
      .model-overview-strip,
      .mode-card-grid,
      .admin-token-row {
        grid-template-columns: 1fr;
      }
      .admin-token-head {
        display: grid;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell" id="app-shell">
    <div class="sidebar-backdrop" id="sidebar-backdrop"></div>
    <aside class="sidebar">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <div class="brand-mark">A</div>
          <div class="brand-copy">
            <strong>Agents Studio</strong>
            <span>Production flow for creating task-specific AGENTS.md documents.</span>
          </div>
        </div>
      </div>
      <div class="sidebar-note">
        <strong>Production</strong>
        只保留创建链路、系统生成案例和最终结果，避免把后台分析信息暴露到生产界面。
      </div>
      <nav class="menu" id="menu"></nav>
      <div class="sidebar-footer" id="sidebar-footer"></div>
      <div class="sidebar-controls">
        <div class="sidebar-toggle-wrap">
          <button type="button" class="sidebar-toggle" id="sidebar-toggle" aria-expanded="true"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2.5"></rect><path d="M9 4.5v15"></path><path d="m14.5 12 3-3"></path><path d="m14.5 12 3 3"></path></svg></button>
          <div class="sidebar-toggle-copy">
            <strong>导航栏</strong>
            <span>收起或展开侧边菜单</span>
          </div>
        </div>
      </div>
    </aside>

    <main class="main">
      <div class="topbar">
        <div class="topbar-start">
          <button type="button" class="topbar-nav-btn" id="topbar-nav-btn" aria-expanded="false" aria-label="展开导航"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16"></path><path d="M4 12h16"></path><path d="M4 18h16"></path></svg></button>
          <div class="topbar-copy">
            <div class="eyebrow">Production Flow</div>
            <h1>更短的创建路径，更清晰的案例回看。</h1>
            <p>你只需要告诉系统当前要做什么、面向谁、运行在哪里，以及有哪些约束。系统会生成与当前任务更贴近的 AGENTS.md，并把结果沉淀到系统创建案例库中。</p>
          </div>
        </div>
        <div class="topbar-actions" id="topbar-actions"></div>
      </div>

      <section class="screen active" data-screen="workspace">
        <section class="hero">
          <div class="panel hero-copy">
            <div class="eyebrow">Create</div>
            <h2>按向导输入必要信息，直接生成可用的 AGENTS.md</h2>
            <p>你只需要描述当前目标、使用场景、技术偏好和关键约束。系统会生成更贴近任务的 AGENTS.md，并把结果整理成可回看的系统案例。</p>
            <div class="hero-pills" id="hero-pills"></div>
            <div class="hero-actions" style="margin-top: 18px;">
              <button type="button" class="button-primary" id="open-library-btn">查看案例库</button>
              <button type="button" class="button-secondary" id="jump-result-btn">查看最新结果</button>
            </div>
          </div>
          <div class="hero-side">
            <h3>当前页面做什么</h3>
            <ul>
              <li>用模板式向导收集最少但关键的任务输入。</li>
              <li>把系统生成产物整理成案例卡片，而不是展示工程路径和分析结果。</li>
              <li>支持查看详情、复用输入和一键复制最终文档。</li>
            </ul>
          </div>
        </section>

        <section class="workspace-shell">
          <aside class="progress-column">
            <div class="panel progress-card">
              <div class="eyebrow">Wizard</div>
              <h3>创建步骤</h3>
              <p class="panel-text">保留单一进度区。你可以点击步骤直接切换，最后一步统一确认并生成。</p>
              <div class="step-list" id="step-list"></div>
            </div>
            <div class="panel template-card">
              <div class="eyebrow">Template</div>
              <h3 id="template-title">HTTP 服务 / Web 应用</h3>
              <p id="template-summary" class="panel-text">适合浏览器访问、交互式服务和可直接上线的结果页面。</p>
              <ul id="template-highlights"></ul>
              <div class="hero-actions" style="margin-top: 16px;">
                <button type="button" class="button-secondary" id="apply-template-btn">应用模板建议</button>
              </div>
            </div>
          </aside>

          <section class="panel form-card">
            <div class="status" id="status">页面默认面向生产使用。生成链路只复用现有能力目录和系统沉淀结果。</div>
            <div class="progress-status" id="progress-status" hidden>
              <div class="progress-head">
                <strong id="progress-title">生成进行中</strong>
                <span id="progress-elapsed">0 秒</span>
              </div>
              <div class="progress-bar">
                <div class="progress-bar-fill" id="progress-bar-fill"></div>
              </div>
              <p class="progress-detail" id="progress-detail">正在准备处理阶段…</p>
            </div>
            <form id="workflow-form">
              <section class="form-step active" data-step="0">
                <div class="step-card">
                  <div class="section-head">
                    <div>
                      <div class="eyebrow">Step 1</div>
                      <h2>选择目标模板并描述任务</h2>
                      <p>先明确这次输出最接近哪种目标类型，再用一段清晰的任务描述告诉系统你真正要完成什么。</p>
                    </div>
                  </div>
                  <div class="field-grid">
                    <div class="field">
                      <label for="template_select">目标模板</label>
                      <select id="template_select"></select>
                      <input id="template_other" class="other-input" placeholder="请输入自定义模板类型">
                      <p class="field-help">优先选择最接近的目标类型，最后一项保留手动输入。</p>
                    </div>
                    <div class="field">
                      <label for="industry_select">行业 / 领域</label>
                      <select id="industry_select"></select>
                      <input id="industry_other" class="other-input" placeholder="请输入自定义行业">
                    </div>
                    <div class="field full">
                      <label for="task_description">任务描述</label>
                      <textarea id="task_description" placeholder="例如：生成一个可上线的 HTTP 服务，通过浏览器完成向导式输入，只展示系统创建案例，并支持查看详情与一键复制。"></textarea>
                      <p class="field-help">建议包含目标、成功标准、交付物和明显边界。任务写得越具体，输出越稳定。</p>
                    </div>
                  </div>
                </div>
              </section>

              <section class="form-step" data-step="1">
                <div class="step-card">
                  <div class="section-head">
                    <div>
                      <div class="eyebrow">Step 2</div>
                      <h2>补充使用场景和运行边界</h2>
                      <p>这一步决定系统如何组织执行要求、环境假设和默认优先级。</p>
                    </div>
                  </div>
                  <div class="field-grid">
                    <div class="field">
                      <label for="target_user_select">目标用户</label>
                      <select id="target_user_select"></select>
                      <input id="target_user_other" class="other-input" placeholder="请输入自定义目标用户">
                    </div>
                    <div class="field">
                      <label for="output_language_select">输出语言</label>
                      <select id="output_language_select"></select>
                      <input id="output_language_other" class="other-input" placeholder="请输入自定义输出语言">
                    </div>
                    <div class="field">
                      <label>运行环境</label>
                      <div class="selection-group">
                        <div class="option-grid" id="environment-options"></div>
                        <div class="custom-entry">
                          <input id="environment-custom-input" placeholder="添加自定义环境，例如：一台远程 Linux、专用 GPU 节点、内网环境">
                          <button type="button" class="button-secondary" id="add-environment-btn">添加</button>
                        </div>
                        <div class="selected-list" id="environment-selected"></div>
                      </div>
                      <p class="field-help">支持组合选择，例如“本地 + 远程 + Docker”。如预置选项不够，再补充自定义环境。</p>
                    </div>
                    <div class="field">
                      <label for="risk_tolerance_select">风险容忍度</label>
                      <select id="risk_tolerance_select"></select>
                      <input id="risk_tolerance_other" class="other-input" placeholder="请输入自定义风险等级">
                    </div>
                  </div>
                </div>
              </section>

              <section class="form-step" data-step="2">
                <div class="step-card">
                  <div class="section-head">
                    <div>
                      <div class="eyebrow">Step 3</div>
                      <h2>确认偏好、约束与请求摘要</h2>
                      <p>这一步只保留任务偏好和汇总摘要。默认模型由独立“模型”页面统一管理，不再混在创建流程里。</p>
                    </div>
                  </div>
                  <div class="field-grid">
                    <div class="field full">
                      <label>偏好技术栈</label>
                      <div class="selection-group">
                        <div class="option-grid" id="stack-options"></div>
                        <div class="custom-entry">
                          <input id="stack-custom-input" placeholder="添加自定义技术栈，例如：celery / kafka / vue">
                          <button type="button" class="button-secondary" id="add-stack-btn">添加</button>
                        </div>
                        <div class="selected-list" id="stack-selected"></div>
                      </div>
                    </div>
                    <div class="field full">
                      <label>约束条件</label>
                      <div class="selection-group">
                        <div class="option-grid" id="constraint-options"></div>
                        <div class="custom-entry">
                          <input id="constraint-custom-input" placeholder="添加自定义约束，例如：必须支持灰度发布 / 必须兼容现有 API">
                          <button type="button" class="button-secondary" id="add-constraint-btn">添加</button>
                        </div>
                        <div class="selected-list" id="constraint-selected"></div>
                      </div>
                    </div>
                    <div class="field full">
                      <label for="creative_notes">自由发挥 / 补充说明</label>
                      <textarea id="creative_notes" placeholder="这里写无法归类到固定选项里的补充说明，例如：希望整体更偏官网质感、减少管理信息、强调业务表达。"></textarea>
                      <p class="field-help">这部分会作为额外补充信息参与生成，但不会强行占用固定选项。</p>
                    </div>
                    <div class="field full">
                      <div class="summary-card">
                        <h4>请求摘要</h4>
                        <div class="summary-list" id="draft-summary"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <section class="form-step" data-step="3">
                <div class="step-card">
                  <div class="section-head">
                    <div>
                      <div class="eyebrow">Step 4</div>
                      <h2>补充任务问答</h2>
                      <p>这一阶段严格参考 `agent_first_hand/docs/init.md` 与 `task.agent.md`。系统会先读取前面 3 步已经填写的模板、任务、环境、约束与偏好，再只补问剩余关键信息，最后生成计划稿。</p>
                    </div>
                  </div>
                  <div class="question-shell">
                    <div class="question-summary-pills" id="question-summary-pills"></div>
                    <div class="question-list" id="questionnaire-list">
                      <div class="empty-state">完成前 3 步后，点击“开始问答”，这里会出现补充问题。</div>
                    </div>
                  </div>
                </div>
              </section>

              <section class="form-step" data-step="4">
                <div class="step-card">
                  <div class="section-head">
                    <div>
                      <div class="eyebrow">Step 5</div>
                      <h2>预览 PLAN.md 并继续生成</h2>
                      <p>当问答足够完整后，系统会先生成一份 PLAN.md。该计划稿会作为后续 AGENTS.md 草稿与最终稿优化的输入基础。</p>
                    </div>
                  </div>
                  <div class="plan-shell">
                    <div class="plan-summary-pills" id="plan-summary-pills"></div>
                    <div class="plan-summary">
                      <h4>当前处理说明</h4>
                      <p class="panel-text" id="plan-auto-note">完成问答并通过校验后，这里会展示 PLAN.md 预览，并自动继续生成 AGENTS.md。</p>
                    </div>
                    <pre class="markdown-box plan-preview" id="plan-markdown">PLAN.md 尚未准备好。完成问答后，这里会显示计划预览。</pre>
                  </div>
                </div>
              </section>
            </form>

            <div class="form-actions">
              <div class="toolbar-actions">
                <button type="button" class="button-quiet" id="prev-step-btn">上一步</button>
                <button type="button" class="button-secondary" id="next-step-btn">下一步</button>
              </div>
              <button type="button" class="button-primary" id="generate-btn">生成 AGENTS.md</button>
            </div>
          </section>
        </section>
      </section>

      <section class="screen" data-screen="library">
        <section class="panel">
          <div class="section-head">
            <div>
              <div class="eyebrow">Library</div>
              <h2>系统创建案例库</h2>
              <p>这里只展示本系统生成的案例卡片。默认优先显示最近 8 条，每条都附带简介、任务摘要和可复用输入。</p>
            </div>
            <div class="pill"><strong id="library-total-pill">0</strong> 个案例</div>
          </div>
          <div class="toolbar">
            <div class="field">
              <label for="library-search">搜索案例</label>
              <input id="library-search" placeholder="按标题、简介、任务、行业、环境或技术栈搜索">
            </div>
            <div class="field">
              <label for="library-industry-filter">行业</label>
              <select id="library-industry-filter"></select>
            </div>
            <div class="field">
              <label for="library-template-filter">模板</label>
              <select id="library-template-filter"></select>
            </div>
            <div class="field">
              <label for="library-language-filter">语言</label>
              <select id="library-language-filter"></select>
            </div>
            <div class="field">
              <label>&nbsp;</label>
              <button type="button" class="button-secondary" id="library-clear-btn" style="width:100%;">清空筛选</button>
            </div>
          </div>
          <p class="panel-text" id="library-summary"></p>
          <div class="library-grid" id="library-grid"></div>
        </section>
      </section>

      <section class="screen" data-screen="result">
        <div class="result-layout">
          <section class="panel result-shell">
            <div class="section-head">
              <div>
                <div class="eyebrow">Latest Result</div>
                <h2 id="result-title">尚未生成结果</h2>
                <p id="result-summary" class="panel-text">完成向导输入后，系统会在这里展示最新生成的 AGENTS.md。</p>
              </div>
              <div class="result-actions">
                <button type="button" class="button-quiet" id="result-back-btn">继续编辑</button>
                <a class="button-secondary" id="result-download-btn" href="#" download style="pointer-events:none; opacity:0.55;">下载 .md</a>
                <button type="button" class="button-primary" id="result-copy-btn">一键复制</button>
              </div>
            </div>
            <div class="section-inline" style="margin-bottom: 14px;">
              <div class="segment-switch">
                <button type="button" id="result-view-final-btn">最终稿</button>
                <button type="button" id="result-view-draft-btn">草稿</button>
              </div>
            </div>
            <p class="stage-note" id="result-stage-note">生成完成后，这里会根据状态展示最终稿或草稿。</p>
            <pre class="markdown-box" id="result-markdown">尚未生成。填写工作台并点击“生成 AGENTS.md”。</pre>
          </section>

          <aside class="panel result-side">
            <div class="eyebrow">Summary</div>
            <h3>生成摘要</h3>
            <div class="result-meta chip-wrap" id="result-meta"></div>
            <div class="drawer-section" style="margin-top: 16px;">
              <h4>生成状态</h4>
              <div class="detail-list" id="result-stage-summary"></div>
            </div>
            <div class="drawer-section" style="margin-top: 16px;">
              <h4>待确认项</h4>
              <ul id="result-questions"></ul>
            </div>
            <div class="drawer-section" style="margin-top: 16px;">
              <h4>Reference Files</h4>
              <div class="reference-list" id="result-references"></div>
            </div>
            <div class="drawer-section" style="margin-top: 16px;">
              <h4>说明</h4>
              <p class="panel-text">新生成的结果会自动写入系统创建案例库，可继续查看详情、复用输入或一键复制完整文档。</p>
            </div>
          </aside>
        </div>

        <section class="panel result-plan-card" id="result-plan-card">
          <div class="section-head">
            <div>
              <div class="eyebrow">PLAN</div>
              <h2>PLAN.md 计划稿</h2>
              <p id="result-plan-summary" class="panel-text">当前结果如果包含计划稿，会在这里显示生成前的执行计划。</p>
            </div>
          </div>
          <pre class="markdown-box plan-preview" id="result-plan-markdown">当前结果还没有可展示的 PLAN.md。</pre>
        </section>
      </section>

      <div class="footer-note" id="footer-note"></div>
    </main>
  </div>

  <div class="model-modal-backdrop" id="model-modal-backdrop"></div>
  <section class="model-modal" id="model-modal" aria-hidden="true">
    <div class="model-modal-shell panel">
      <div class="section-head">
        <div>
          <div class="eyebrow">Model Control</div>
          <h2>模型优化开关与配置</h2>
          <p class="panel-text">关闭时不涉及任何模型配置；开启时会先尝试读取系统默认模型，如需覆盖再切换到自定义接口。</p>
        </div>
        <div class="result-actions">
          <button type="button" class="button-secondary" id="model-validate-btn">验证配置</button>
          <button type="button" class="button-primary" id="model-save-btn">应用当前设置</button>
          <button type="button" class="close-btn" id="model-modal-close-btn" aria-label="关闭模型配置">×</button>
        </div>
      </div>
      <div class="model-modal-body">
        <div class="status" id="model-settings-status">正在读取当前模型配置…</div>
        <div class="model-flow-note" id="model-flow-note">按顺序完成：先选择状态，再输入管理员令牌，最后应用当前设置。</div>

        <section class="model-section model-primary-section">
          <div class="model-overview-strip" id="model-overview-strip"></div>
          <div class="model-toggle-row">
            <div class="model-command-group">
              <div class="model-command-copy">
                <h3>模型优化状态</h3>
                <p>先明确这次是“开启模型优化”还是“禁用模型优化”。开启后会优先尝试系统默认模型。</p>
              </div>
              <input id="model-enabled-toggle" type="checkbox" hidden>
              <div class="mode-card-grid">
                <button type="button" class="mode-card" id="model-enable-btn">
                  <em>推荐</em>
                  <strong>开启模型优化</strong>
                  <span>优先读取系统默认模型；如默认模型不可用，再切换到自定义模型接口。</span>
                </button>
                <button type="button" class="mode-card negative" id="model-disable-btn">
                  <em>关闭</em>
                  <strong>禁用模型优化</strong>
                  <span>完全跳过模型相关处理，不再涉及模型配置、验证和调用。</span>
                </button>
              </div>
            </div>
            <div class="admin-token-card" id="model-admin-token-card">
              <div class="admin-token-head">
                <div>
                  <h3>管理员令牌</h3>
                  <p>执行“开启 / 禁用 / 保存”之前，需要先在这里输入管理员令牌。</p>
                </div>
                <button type="button" class="button-quiet token-visibility-btn" id="model-token-visibility-btn">显示令牌</button>
              </div>
              <label class="field-inline-label" for="model_admin_token">写操作口令 <code>AGENTS_ADMIN_TOKEN</code></label>
              <div class="admin-token-row">
                <input id="model_admin_token" type="password" placeholder="在这里输入 AGENTS_ADMIN_TOKEN">
                <span class="token-badge">必填后才能执行</span>
              </div>
              <div class="token-inline-status" id="model-token-inline-status"></div>
              <div class="token-focus-note">未配置管理员令牌时，此弹窗为只读。报出权限错误时，页面会自动把焦点移到这个输入框。</div>
            </div>
          </div>
        </section>

        <section class="model-section model-config-section" id="model-config-section">
          <div class="section-inline model-section-head">
            <div>
              <h3>模型接入配置</h3>
              <p class="field-help">只在开启模型优化时生效。默认优先尝试系统默认模型，如需覆盖再切换到自定义接口。</p>
            </div>
            <button type="button" class="button-quiet" id="model-refresh-btn">重新读取当前配置</button>
          </div>
          <div class="field full" id="model-source-panel">
            <label>开启后优先来源</label>
            <div class="segment-switch" id="model-source-switch">
              <button type="button" data-model-source="default">系统默认模型</button>
              <button type="button" data-model-source="custom">自定义模型接口</button>
            </div>
            <select id="model_mode_select" hidden></select>
            <p class="field-help" id="model-runtime-note">模型提供商配置指引会显示在这里。</p>
          </div>
          <div class="field-grid model-config-grid" id="model-config-fields">
            <div class="field">
              <label for="model_provider_select">供应商 / 接口标识</label>
              <select id="model_provider_select"></select>
              <input id="model_provider_other" class="other-input" placeholder="请输入自定义供应商名称">
              <p class="field-help">这里只用于展示与记录。真正请求会使用下方填写的 Base URL、模型名和 API Key。</p>
            </div>
            <div class="field">
              <label for="model_wire_api_select">接口协议</label>
              <select id="model_wire_api_select"></select>
              <p class="field-help">优先使用供应商明确支持的协议；如支持 Responses API，可选 `responses`。</p>
            </div>
            <div class="field">
              <label for="model_base_url">Base URL</label>
              <input id="model_base_url" placeholder="例如：https://api.openai.com/v1">
            </div>
            <div class="field">
              <label for="model_name">模型名</label>
              <input id="model_name" placeholder="例如：gpt-5.4 / deepseek-chat / qwen-max">
            </div>
            <div class="field full">
              <label for="model_api_key">API Key</label>
              <input id="model_api_key" type="password" placeholder="请输入用于服务默认模型的 API Key">
              <p class="field-help">安全起见，已保存的密钥不会回显；修改或重新验证配置时，需要重新输入。</p>
            </div>
          </div>
          <div class="model-validation-block">
            <h4>最近一次验证</h4>
            <div class="summary-list" id="model-validation-summary"></div>
          </div>
        </section>

        <section class="model-section model-runtime-section">
          <div class="section-inline model-section-head">
            <div>
              <h3>运行时与保存状态</h3>
              <p class="field-help">这里汇总当前生效状态、系统默认模型和已保存配置，便于判断服务到底会怎么运行。</p>
            </div>
          </div>
          <div class="result-layout model-runtime-layout">
            <section class="result-shell model-runtime-block">
              <div class="eyebrow">Runtime</div>
              <h3>当前生效状态</h3>
              <div class="detail-list" id="model-current-runtime"></div>
            </section>
            <aside class="result-side model-runtime-side">
              <div class="drawer-section">
                <h4>系统默认模型</h4>
                <div class="detail-list" id="model-system-runtime"></div>
              </div>
              <div class="drawer-section">
                <h4>已保存默认配置</h4>
                <div class="detail-list" id="model-saved-runtime"></div>
              </div>
              <div class="drawer-section">
                <h4>写操作说明</h4>
                <p class="panel-text" id="model-admin-note">读取中…</p>
              </div>
            </aside>
          </div>
        </section>
      </div>
    </div>
  </section>

  <div class="drawer-backdrop" id="drawer-backdrop"></div>
  <aside class="drawer" id="library-drawer" aria-hidden="true">
    <div class="drawer-head">
      <div>
        <div class="eyebrow" id="drawer-eyebrow">Case Detail</div>
        <h3 id="drawer-title">选择一个案例查看详情</h3>
        <p class="drawer-summary" id="drawer-summary">系统创建的任务简介、输入摘要和生成文档会在这里展开。</p>
      </div>
      <button type="button" class="close-btn" id="drawer-close-btn">×</button>
    </div>
    <div class="drawer-actions">
      <button type="button" class="button-primary" id="drawer-copy-btn">一键复制</button>
      <a class="button-secondary" id="drawer-download-btn" href="#" download>下载</a>
      <button type="button" class="button-quiet" id="drawer-reuse-btn">复用输入</button>
    </div>
    <div class="chip-wrap" id="drawer-meta"></div>
    <div class="drawer-body">
      <section class="drawer-section">
        <h4>任务简介</h4>
        <p class="panel-text" id="drawer-task"></p>
      </section>
      <section class="drawer-section">
        <h4>输入摘要</h4>
        <div class="detail-list" id="drawer-request"></div>
      </section>
      <section class="drawer-section">
        <h4>生成状态</h4>
        <div class="detail-list" id="drawer-stage"></div>
      </section>
      <section class="drawer-section">
        <h4>Reference Files</h4>
        <div class="reference-list" id="drawer-references"></div>
      </section>
      <section class="drawer-section" id="drawer-plan-section">
        <h4>PLAN.md</h4>
        <p class="field-help" id="drawer-plan-note">如果该案例包含计划稿，会在这里展示。</p>
        <pre class="drawer-markdown plan-preview" id="drawer-plan-markdown">当前案例没有保存 PLAN.md。</pre>
      </section>
      <section class="drawer-section">
        <div class="section-inline">
          <h4 style="margin-bottom: 0;">生成文档</h4>
          <div class="segment-switch">
            <button type="button" id="drawer-view-final-btn">最终稿</button>
            <button type="button" id="drawer-view-draft-btn">草稿</button>
          </div>
        </div>
        <p class="field-help" id="drawer-stage-note" style="margin-top: 10px;"></p>
        <pre class="drawer-markdown" id="drawer-markdown"></pre>
      </section>
    </div>
  </aside>

  <script>
    const initialOverview = __OVERVIEW_JSON__;
    const adminEnabled = __ADMIN_JSON__;
    const TEMPLATE_META = {
      http_service: {
        label: 'HTTP 服务 / Web 应用',
        intro: '适合浏览器访问、交互式服务、结果页展示和上线交付。',
        highlights: ['优先组织浏览器交互、HTTP 服务和结果输出路径。', '适合需要向导式输入、案例沉淀和浏览器回看的任务。'],
        defaults: {
          targetUser: 'general',
          environment: 'browser_service',
          stack: ['python', 'fastapi'],
          constraints: ['记录所有关键过程并带时间戳', '不得跳过验证']
        }
      },
      cli_tool: {
        label: 'CLI / 工具链',
        intro: '适合命令行工具、脚本工作流和本地执行链路。',
        highlights: ['优先组织命令入口、脚本接口和执行验证。', '适合强调本地环境、批处理和可追溯执行日志的任务。'],
        defaults: {
          targetUser: 'solo_builder',
          environment: 'local_only',
          stack: ['python', 'shell'],
          constraints: ['记录所有关键过程并带时间戳', '保留可回退方案']
        }
      },
      automation_workflow: {
        label: '自动化工作流',
        intro: '适合多步骤处理、批处理策略和需要时间戳复盘的任务。',
        highlights: ['优先组织批处理映射、失败处理和执行记录。', '适合模型调用、数据清洗和长流程编排。'],
        defaults: {
          targetUser: 'internal_team',
          environment: 'mixed',
          stack: ['python'],
          constraints: ['记录所有关键过程并带时间戳', '优先复用已有全量打标结果']
        }
      },
      data_processing: {
        label: '数据分析 / 处理',
        intro: '适合标注、清洗、汇总、验证和报告输出。',
        highlights: ['优先组织输入样本、处理规则、汇总结果和验收。', '适合关注准确性、覆盖率和结构化结果的任务。'],
        defaults: {
          targetUser: 'analyst',
          environment: 'local_plus_remote',
          stack: ['python', 'postgresql'],
          constraints: ['记录所有关键过程并带时间戳', '不得跳过验证']
        }
      },
      api_integration: {
        label: 'API / 集成服务',
        intro: '适合接口编排、外部模型或第三方服务集成。',
        highlights: ['优先组织接口边界、供应商可替换和失败降级。', '适合强调批处理、请求映射和供应商替换能力的任务。'],
        defaults: {
          targetUser: 'internal_team',
          environment: 'docker',
          stack: ['python', 'fastapi', 'redis'],
          constraints: ['记录所有关键过程并带时间戳', '保留可回退方案']
        }
      },
      custom: {
        label: '自定义任务',
        intro: '无法归入固定模板时使用，自定义输入会优先于模板推断。',
        highlights: ['系统会优先相信你的显式描述，而不是通用模板。', '建议在任务描述中明确交付物、环境和验收标准。'],
        defaults: {
          targetUser: 'general',
          environment: 'mixed',
          stack: [],
          constraints: ['记录所有关键过程并带时间戳']
        }
      }
    };
    const OPTIONS = {
      template: ['http_service', 'cli_tool', 'automation_workflow', 'data_processing', 'api_integration', 'other'],
      industry: ['devtools', 'ai_ml', 'finance', 'ecommerce', 'communications', 'cybersecurity', 'media_content', 'productivity', 'research', 'government', 'other'],
      targetUser: ['general', 'solo_builder', 'internal_team', 'open_source_maintainer', 'analyst', 'other'],
      outputLanguage: ['zh', 'en', 'bilingual', 'other'],
      riskTolerance: ['low', 'medium', 'high', 'other'],
      modelMode: ['default', 'custom', 'disabled'],
      modelProvider: ['openai', 'azure_openai', 'openrouter', 'deepseek', 'dashscope', 'siliconflow', 'volcengine', 'other'],
      modelWireApi: ['chat_completions', 'responses'],
      environment: ['browser_service', 'local_only', 'local_plus_remote', 'docker', 'kubernetes', 'mixed', 'other'],
      stack: ['python', 'fastapi', 'react', 'typescript', 'javascript', 'docker', 'postgresql', 'redis', 'shell', 'other'],
      constraint: ['记录所有关键过程并带时间戳', '优先复用已有全量打标结果', '不得跳过验证', '输出必须包含绝对路径', '保留可回退方案', '供应商必须可替换', 'other']
    };
    const LABELS = {
      template: {
        http_service: 'HTTP 服务 / Web 应用',
        cli_tool: 'CLI / 工具链',
        automation_workflow: '自动化工作流',
        data_processing: '数据分析 / 处理',
        api_integration: 'API / 集成服务',
        other: '其他（手动输入）'
      },
      industry: {
        devtools: '开发工具 / Devtools',
        ai_ml: 'AI / 机器学习',
        finance: '金融',
        ecommerce: '电商',
        communications: '通信 / 协作',
        cybersecurity: '网络安全',
        media_content: '内容 / 媒体',
        productivity: '效率工具',
        research: '研究',
        government: '政务 / 公共服务',
        other: '其他（手动输入）'
      },
      targetUser: {
        general: '通用外部用户',
        solo_builder: '个人开发者',
        internal_team: '团队内部用户',
        open_source_maintainer: '开源维护者',
        analyst: '分析师',
        other: '其他（手动输入）'
      },
      outputLanguage: {
        zh: '中文',
        en: '英文',
        bilingual: '双语',
        other: '其他（手动输入）'
      },
      riskTolerance: {
        low: '低',
        medium: '中',
        high: '高',
        other: '其他（手动输入）'
      },
      modelMode: {
        default: '系统默认模型',
        custom: '自定义模型接口',
        disabled: '禁用模型增强功能'
      },
      modelProvider: {
        openai: 'OpenAI',
        azure_openai: 'Azure OpenAI',
        openrouter: 'OpenRouter',
        deepseek: 'DeepSeek',
        dashscope: 'DashScope / 通义千问',
        siliconflow: 'SiliconFlow',
        volcengine: '火山方舟',
        other: '其他（手动输入）'
      },
      modelWireApi: {
        chat_completions: 'chat_completions',
        responses: 'responses'
      },
      environment: {
        browser_service: '浏览器 + HTTP 服务',
        local_only: '仅本地',
        local_plus_remote: '本地 + 远程',
        docker: 'Docker',
        kubernetes: 'Kubernetes',
        mixed: '混合环境',
        other: '其他（手动输入）'
      }
    };
    const MENU_CONFIG = [
      { id: 'workspace', title: '创建', description: '向导式输入任务信息' },
      { id: 'library', title: '案例', description: '系统创建案例库' },
      { id: 'result', title: '结果', description: '最新生成文档' }
    ];
    const STEP_CONFIG = [
      { title: '模板与目标', description: '选择模板并描述任务' },
      { title: '场景与环境', description: '补充用户、语言和运行边界' },
      { title: '偏好与确认', description: '技术栈、约束和基础摘要' },
      { title: '补充问答', description: '继续收集任务必需信息' },
      { title: 'PLAN 预览', description: '预览计划稿并生成 AGENTS' }
    ];
    const FREEFORM_NOTE_PREFIX = '补充说明: ';
    const DEFERRED_ANSWER_PREFIX = '待确认：';
    const CUSTOM_OPTION_VALUE = '__custom__';

    const state = {
      activeScreen: 'workspace',
      currentStep: 0,
      overview: initialOverview || {},
      modelSettings: null,
      modelModalOpen: false,
      modelSourceMode: 'default',
      modelValidationToken: '',
      modelValidatedSignature: '',
      modelValidationResult: null,
      modelOperationPending: false,
      library: (initialOverview && initialOverview.library_preview) || [],
      libraryDetails: {},
      drawerItem: null,
      lastResult: null,
      resultViewMode: 'final',
      drawerViewMode: 'final',
      currentRequestId: '',
      progressTimer: 0,
      progressPending: false,
      progressStartedAt: 0,
      progressSnapshot: null,
      intakeSession: null,
      intakeAnswers: {},
      ignoredQuestions: {},
      questionDrafts: {},
      intakeBaseSignature: '',
      planAutoTimer: 0,
      generationPending: false,
      generatedSessionId: '',
      selectedValues: {
        environment: [],
        stack: [],
        constraint: []
      }
    };

    const appShell = document.getElementById('app-shell');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const topbarNavBtn = document.getElementById('topbar-nav-btn');
    const menu = document.getElementById('menu');
    const stepList = document.getElementById('step-list');
    const statusEl = document.getElementById('status');
    const progressStatus = document.getElementById('progress-status');
    const progressTitle = document.getElementById('progress-title');
    const progressElapsed = document.getElementById('progress-elapsed');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressDetail = document.getElementById('progress-detail');
    const draftSummary = document.getElementById('draft-summary');
    const topbarActions = document.getElementById('topbar-actions');
    const heroPills = document.getElementById('hero-pills');
    const footerNote = document.getElementById('footer-note');
    const sidebarFooter = document.getElementById('sidebar-footer');
    const modelModalBackdrop = document.getElementById('model-modal-backdrop');
    const modelModal = document.getElementById('model-modal');
    const modelModalCloseBtn = document.getElementById('model-modal-close-btn');
    const formSteps = Array.from(document.querySelectorAll('.form-step'));
    const screens = Array.from(document.querySelectorAll('.screen'));
    const prevStepBtn = document.getElementById('prev-step-btn');
    const nextStepBtn = document.getElementById('next-step-btn');
    const generateBtn = document.getElementById('generate-btn');
    const addStackBtn = document.getElementById('add-stack-btn');
    const addConstraintBtn = document.getElementById('add-constraint-btn');
    const addEnvironmentBtn = document.getElementById('add-environment-btn');
    const stackOptions = document.getElementById('stack-options');
    const constraintOptions = document.getElementById('constraint-options');
    const environmentOptions = document.getElementById('environment-options');
    const stackSelected = document.getElementById('stack-selected');
    const constraintSelected = document.getElementById('constraint-selected');
    const environmentSelected = document.getElementById('environment-selected');
    const stackCustomInput = document.getElementById('stack-custom-input');
    const constraintCustomInput = document.getElementById('constraint-custom-input');
    const environmentCustomInput = document.getElementById('environment-custom-input');
    const creativeNotesInput = document.getElementById('creative_notes');
    const modelEnabledToggle = document.getElementById('model-enabled-toggle');
    const modelEnableBtn = document.getElementById('model-enable-btn');
    const modelDisableBtn = document.getElementById('model-disable-btn');
    const modelSourceSwitch = document.getElementById('model-source-switch');
    const modelSourcePanel = document.getElementById('model-source-panel');
    const modelFlowNote = document.getElementById('model-flow-note');
    const modelConfigSection = document.getElementById('model-config-section');
    const modelSettingsStatus = document.getElementById('model-settings-status');
    const modelOverviewStrip = document.getElementById('model-overview-strip');
    const modelRuntimeNote = document.getElementById('model-runtime-note');
    const modelConfigFields = document.getElementById('model-config-fields');
    const modelValidationSummary = document.getElementById('model-validation-summary');
    const modelCurrentRuntime = document.getElementById('model-current-runtime');
    const modelSystemRuntime = document.getElementById('model-system-runtime');
    const modelSavedRuntime = document.getElementById('model-saved-runtime');
    const modelAdminNote = document.getElementById('model-admin-note');
    const modelAdminTokenCard = document.getElementById('model-admin-token-card');
    const modelAdminTokenInput = document.getElementById('model_admin_token');
    const modelTokenInlineStatus = document.getElementById('model-token-inline-status');
    const modelTokenVisibilityBtn = document.getElementById('model-token-visibility-btn');
    const modelValidateBtn = document.getElementById('model-validate-btn');
    const modelSaveBtn = document.getElementById('model-save-btn');
    const modelRefreshBtn = document.getElementById('model-refresh-btn');
    const openLibraryBtn = document.getElementById('open-library-btn');
    const jumpResultBtn = document.getElementById('jump-result-btn');
    const applyTemplateBtn = document.getElementById('apply-template-btn');
    const templateTitle = document.getElementById('template-title');
    const templateSummary = document.getElementById('template-summary');
    const templateHighlights = document.getElementById('template-highlights');
    const libraryGrid = document.getElementById('library-grid');
    const librarySummary = document.getElementById('library-summary');
    const libraryTotalPill = document.getElementById('library-total-pill');
    const librarySearch = document.getElementById('library-search');
    const libraryIndustryFilter = document.getElementById('library-industry-filter');
    const libraryTemplateFilter = document.getElementById('library-template-filter');
    const libraryLanguageFilter = document.getElementById('library-language-filter');
    const libraryClearBtn = document.getElementById('library-clear-btn');
    const drawerBackdrop = document.getElementById('drawer-backdrop');
    const libraryDrawer = document.getElementById('library-drawer');
    const drawerCloseBtn = document.getElementById('drawer-close-btn');
    const drawerTitle = document.getElementById('drawer-title');
    const drawerSummary = document.getElementById('drawer-summary');
    const drawerEyebrow = document.getElementById('drawer-eyebrow');
    const drawerMeta = document.getElementById('drawer-meta');
    const drawerTask = document.getElementById('drawer-task');
    const drawerRequest = document.getElementById('drawer-request');
    const drawerStage = document.getElementById('drawer-stage');
    const drawerReferences = document.getElementById('drawer-references');
    const drawerStageNote = document.getElementById('drawer-stage-note');
    const drawerMarkdown = document.getElementById('drawer-markdown');
    const drawerCopyBtn = document.getElementById('drawer-copy-btn');
    const drawerDownloadBtn = document.getElementById('drawer-download-btn');
    const drawerReuseBtn = document.getElementById('drawer-reuse-btn');
    const drawerViewFinalBtn = document.getElementById('drawer-view-final-btn');
    const drawerViewDraftBtn = document.getElementById('drawer-view-draft-btn');
    const resultTitle = document.getElementById('result-title');
    const resultSummary = document.getElementById('result-summary');
    const resultMeta = document.getElementById('result-meta');
    const resultStageSummary = document.getElementById('result-stage-summary');
    const resultReferences = document.getElementById('result-references');
    const resultStageNote = document.getElementById('result-stage-note');
    const resultQuestions = document.getElementById('result-questions');
    const resultMarkdown = document.getElementById('result-markdown');
    const resultBackBtn = document.getElementById('result-back-btn');
    const resultDownloadBtn = document.getElementById('result-download-btn');
    const resultCopyBtn = document.getElementById('result-copy-btn');
    const resultViewFinalBtn = document.getElementById('result-view-final-btn');
    const resultViewDraftBtn = document.getElementById('result-view-draft-btn');
    const questionSummaryPills = document.getElementById('question-summary-pills');
    const questionnaireList = document.getElementById('questionnaire-list');
    const planSummaryPills = document.getElementById('plan-summary-pills');
    const planAutoNote = document.getElementById('plan-auto-note');
    const planMarkdown = document.getElementById('plan-markdown');
    const resultPlanCard = document.getElementById('result-plan-card');
    const resultPlanSummary = document.getElementById('result-plan-summary');
    const resultPlanMarkdown = document.getElementById('result-plan-markdown');
    const drawerPlanSection = document.getElementById('drawer-plan-section');
    const drawerPlanNote = document.getElementById('drawer-plan-note');
    const drawerPlanMarkdown = document.getElementById('drawer-plan-markdown');

    resultViewFinalBtn.disabled = true;
    resultViewDraftBtn.disabled = true;
    drawerViewFinalBtn.disabled = true;
    drawerViewDraftBtn.disabled = true;

    function escapeHtml(value) {
      return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function basename(path) {
      const normalized = String(path || '').split('/');
      return normalized[normalized.length - 1] || '';
    }

    function safeReferenceLabel(path) {
      const text = String(path || '').trim();
      if (!text) {
        return '';
      }
      const normalized = text.replace(/\\\\/g, '/');
      const parts = normalized.split('/').filter(Boolean);
      const base = parts.length ? parts[parts.length - 1] : normalized;
      if (base.includes('__')) {
        const nameParts = base.split('__').filter(Boolean);
        if (nameParts.length >= 3) {
          return `${nameParts[0]}/${nameParts[1]}/${nameParts.slice(2).join('__')}`;
        }
      }
      if (parts.length >= 3 && /\\.md$/i.test(base)) {
        return parts.slice(-3).join('/');
      }
      return base || normalized;
    }

    function looksLikeReferencePath(value) {
      const text = String(value || '').trim();
      if (!text) {
        return false;
      }
      const normalized = text.replace(/\\\\/g, '/');
      return normalized.startsWith('/')
        || /^[A-Za-z]:\//.test(normalized)
        || /\\.md$/i.test(normalized)
        || normalized.includes('__')
        || normalized.split('/').filter(Boolean).length >= 3;
    }

    function sanitizeReferenceMarkdown(value) {
      const text = String(value || '').replace(/\\r\\n/g, '\\n');
      if (!text || (text.indexOf('Reference Files') === -1 && text.indexOf('参考文件') === -1)) {
        return text;
      }
      const lines = text.split('\\n');
      let inReferenceSection = false;
      return lines.map(line => {
        const trimmed = line.trim();
        if (/^##\\s+(Reference Files|参考文件)\\s*$/i.test(trimmed)) {
          inReferenceSection = true;
          return line;
        }
        if (inReferenceSection && /^##\\s+/.test(trimmed)) {
          inReferenceSection = false;
        }
        if (!inReferenceSection || !trimmed.startsWith('-')) {
          return line;
        }
        return line.replace(/`([^`]+)`/g, (match, inner) => looksLikeReferencePath(inner) ? `\`${safeReferenceLabel(inner)}\`` : match);
      }).join('\\n');
    }

    function renderMarkdownWithLineNumbers(target, value) {
      const text = sanitizeReferenceMarkdown(value);
      const lines = String(text || '').replace(/\\r\\n/g, '\\n').split('\\n');
      target.innerHTML = `<code class="code-lines">${lines.map((line, index) => {
        const content = escapeHtml(line);
        return `<span class="code-line"><span class="code-line-no">${index + 1}</span><span class="code-line-text">${content || '&nbsp;'}</span></span>`;
      }).join('')}</code>`;
      target.scrollTop = 0;
    }

    function truncateText(value, maxLength = 120) {
      const text = String(value || '').trim().replace(/\\s+/g, ' ');
      if (text.length <= maxLength) {
        return text;
      }
      return `${text.slice(0, Math.max(0, maxLength - 1)).trim()}…`;
    }

    function formatTimestamp(value) {
      const text = String(value || '').trim();
      if (!text) {
        return '未知时间';
      }
      const runMatch = text.match(/^(\\d{4})(\\d{2})(\\d{2})(\\d{2})(\\d{2})(\\d{2})(?:_(\\d+))?$/);
      if (runMatch) {
        const suffix = runMatch[7] ? ` #${runMatch[7]}` : '';
        return `${runMatch[1]}-${runMatch[2]}-${runMatch[3]} ${runMatch[4]}:${runMatch[5]}:${runMatch[6]}${suffix}`;
      }
      return text.replace('T', ' ').replace(/\\+\\d{2}:\\d{2}$/, '');
    }

    function templateLabel(value) {
      return LABELS.template[value] || value || '未指定模板';
    }

    function labelFor(mapName, value) {
      const labels = LABELS[mapName] || {};
      return labels[value] || value || '未填写';
    }

    function splitEnvironmentValue(value) {
      if (Array.isArray(value)) {
        return value.map(item => String(item || '').trim()).filter(Boolean);
      }
      return String(value || '')
        .split(/[,;\\n+]+/g)
        .map(item => item.trim())
        .filter(Boolean);
    }

    function environmentDisplayValue(value) {
      const values = splitEnvironmentValue(value);
      if (!values.length) {
        return '未填写';
      }
      return values.map(item => LABELS.environment[item] || item).join(' + ');
    }

    function defaultModelRuntime() {
      return (state.overview && state.overview.default_model_runtime) || {};
    }

    function providerGuideMeta(value) {
      const guides = {
        openai: {
          title: 'OpenAI',
          example: 'https://api.openai.com/v1',
          note: '官方接口通常优先支持 Responses API，也兼容常见的 OpenAI 风格调用。'
        },
        azure_openai: {
          title: 'Azure OpenAI',
          example: 'https://{resource}.openai.azure.com/openai/v1',
          note: '需要确认你当前部署的 API 版本与 URL 格式；建议先用最小请求验证连通性。'
        },
        openrouter: {
          title: 'OpenRouter',
          example: 'https://openrouter.ai/api/v1',
          note: '适合快速切换不同上游模型，推荐保持模型名与供应商文档一致。'
        },
        deepseek: {
          title: 'DeepSeek',
          example: 'https://api.deepseek.com/v1',
          note: '常见场景使用 OpenAI 兼容接口即可，优先确认目标模型名与协议支持。'
        },
        dashscope: {
          title: 'DashScope / 通义千问',
          example: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
          note: '建议使用其兼容模式地址，并确认所选模型是否支持当前协议。'
        },
        siliconflow: {
          title: 'SiliconFlow',
          example: 'https://api.siliconflow.cn/v1',
          note: '适合接入多家模型，保持 provider label 与 base URL 分离可以方便后续替换。'
        },
        volcengine: {
          title: '火山方舟',
          example: 'https://ark.cn-beijing.volces.com/api/v3',
          note: '不同模型可能对应不同 endpoint 或 project，接入前先确认网关地址。'
        },
        other: {
          title: '自定义兼容接口',
          example: 'https://your-provider.example.com/v1',
          note: '只要兼容 OpenAI 风格协议，就可以接入；建议保持供应商可替换。'
        }
      };
      return guides[value] || guides.other;
    }

    function collectModelConfig() {
      const mode = document.getElementById('model_mode_select').value || 'default';
      if (mode === 'disabled') {
        return { mode: 'disabled' };
      }
      if (mode === 'default') {
        return { mode: 'default' };
      }
      const providerValue = document.getElementById('model_provider_select').value || 'other';
      return {
        mode: 'custom',
        provider_label: providerValue === 'other'
          ? document.getElementById('model_provider_other').value.trim()
          : labelFor('modelProvider', providerValue),
        base_url: document.getElementById('model_base_url').value.trim(),
        model: document.getElementById('model_name').value.trim(),
        api_key: document.getElementById('model_api_key').value.trim(),
        wire_api: document.getElementById('model_wire_api_select').value || 'chat_completions'
      };
    }

    function modelModeLabel(mode) {
      return LABELS.modelMode[mode] || mode || '未指定';
    }

    function currentModelConfigSignature() {
      return JSON.stringify(collectModelConfig());
    }

    function modelHasUsableSystemDefault() {
      const runtime = state.modelSettings && state.modelSettings.system_default_runtime
        ? state.modelSettings.system_default_runtime
        : {};
      return !!runtime.enabled;
    }

    function syncModelSourceButtons() {
      const mode = document.getElementById('model_mode_select').value || 'default';
      const source = mode === 'custom' ? 'custom' : 'default';
      state.modelSourceMode = source;
      Array.from(modelSourceSwitch.querySelectorAll('[data-model-source]')).forEach(button => {
        button.classList.toggle('active', button.getAttribute('data-model-source') === source);
      });
    }

    function syncModelModeButtons() {
      const mode = document.getElementById('model_mode_select').value || 'default';
      modelEnableBtn.classList.toggle('active', mode !== 'disabled');
      modelDisableBtn.classList.toggle('active', mode === 'disabled');
      modelEnableBtn.disabled = state.modelOperationPending;
      modelDisableBtn.disabled = state.modelOperationPending;
    }

    function syncModelTokenVisibilityButton() {
      const visible = modelAdminTokenInput.type === 'text';
      modelTokenVisibilityBtn.textContent = visible ? '隐藏令牌' : '显示令牌';
      modelTokenVisibilityBtn.setAttribute('aria-pressed', visible ? 'true' : 'false');
    }

    function setModelMode(mode, { clearValidation = false } = {}) {
      document.getElementById('model_mode_select').value = mode;
      modelEnabledToggle.checked = mode !== 'disabled';
      if (clearValidation) {
        clearModelValidationState();
      }
      syncModelSourceButtons();
      syncModelModeButtons();
      updateModelConfigVisibility();
    }

    function modelRuntimeDescription(runtime) {
      const info = runtime || {};
      if (!Object.keys(info).length) {
        return '未记录模型运行时';
      }
      const mode = String(info.mode || 'default');
      const providerLabel = String(info.provider_label || '').trim();
      const model = String(info.model || '').trim();
      if (mode === 'disabled') {
        return providerLabel || '禁用模型增强功能';
      }
      if (mode === 'custom') {
        return [providerLabel || '自定义 OpenAI 兼容接口', model].filter(Boolean).join(' / ') || '自定义模型接口';
      }
      if (info.enabled) {
        return [providerLabel || '服务默认模型', model].filter(Boolean).join(' / ');
      }
      return providerLabel || '未配置默认模型';
    }

    function setModelSettingsStatus(text, isError = false) {
      let message = String(text || '');
      if (message.includes('管理员令牌')) {
        message = `${message} 请在上方“管理员令牌”输入框填写后重试。`;
        window.setTimeout(() => {
          modelAdminTokenCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
          modelAdminTokenInput.focus();
          modelAdminTokenInput.select();
        }, 40);
      }
      modelSettingsStatus.textContent = message;
      modelSettingsStatus.className = isError ? 'status error' : 'status';
    }

    function clearModelValidationState() {
      state.modelValidationToken = '';
      state.modelValidatedSignature = '';
      state.modelValidationResult = null;
    }

    function detailListMarkup(rows, emptyText) {
      const items = (rows || []).filter(item => Array.isArray(item) && item.length >= 2 && String(item[1] || '').trim());
      if (!items.length) {
        return `<div class="empty-state">${escapeHtml(emptyText || '暂无信息')}</div>`;
      }
      return items.map(([label, value]) => `
        <div class="detail-item">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
    }

    function renderModelOverviewStrip() {
      const settings = state.modelSettings || {};
      const runtime = settings.effective_default_runtime || {};
      const systemRuntime = settings.system_default_runtime || {};
      const mode = document.getElementById('model_mode_select').value || 'default';
      const summaryMode = mode === 'disabled'
        ? '禁用模型优化'
        : (mode === 'default' ? '开启并优先使用系统默认模型' : '开启并使用自定义模型接口');
      const runtimeText = mode === 'disabled'
        ? '当前不会调用任何模型'
        : (mode === 'default'
            ? (systemRuntime.enabled ? modelRuntimeDescription(systemRuntime) : '未检测到系统默认模型')
            : (document.getElementById('model_name').value.trim() || '等待填写自定义模型'));
      const adminConfigured = !!settings.admin_configured;
      const tokenFilled = !!modelAdminTokenInput.value.trim();
      const permissionText = adminConfigured
        ? (tokenFilled ? '管理员令牌已填写，可执行写操作' : '等待输入管理员令牌')
        : '服务端未配置管理员令牌';
      modelOverviewStrip.innerHTML = [
        ['当前准备应用', summaryMode],
        ['当前目标运行时', runtimeText || modelRuntimeDescription(runtime)],
        ['写操作权限', permissionText]
      ].map(([label, value]) => `
        <div class="overview-stat">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
    }

    function updateTokenEntryState() {
      const settings = state.modelSettings || {};
      const adminConfigured = !!settings.admin_configured;
      const tokenFilled = !!modelAdminTokenInput.value.trim();
      const chips = [];
      if (!adminConfigured) {
        chips.push('<span class="chip">服务端未配置管理员令牌</span>');
      } else if (tokenFilled) {
        chips.push('<span class="chip alt">管理员令牌已填写</span>');
      } else {
        chips.push('<span class="chip">请先输入管理员令牌</span>');
      }
      chips.push(`<span class="chip">${escapeHtml(tokenFilled ? '可尝试执行写操作' : '输入后才会解锁验证与保存')}</span>`);
      modelTokenInlineStatus.innerHTML = chips.join('');
    }

    function renderModelValidationSummary() {
      if (!state.modelValidationResult) {
        const mode = document.getElementById('model_mode_select').value || 'default';
        const message = mode === 'custom'
          ? '填写完配置后，先点击“验证配置”，通过后才能保存为服务默认模型。'
          : (mode === 'default'
              ? '系统默认模型模式不需要单独验证；开启时会先尝试读取系统默认模型。'
              : '关闭状态下不会涉及模型校验。');
        modelValidationSummary.innerHTML = `
          <div class="summary-item">
            <strong>状态</strong>
            <span>${escapeHtml(mode === 'custom' ? '尚未验证' : '无需验证')}</span>
          </div>
          <div class="summary-item">
            <strong>说明</strong>
            <span>${escapeHtml(message)}</span>
          </div>
        `;
        return;
      }
      const runtime = state.modelValidationResult.model_runtime || {};
      modelValidationSummary.innerHTML = [
        ['状态', '验证通过'],
        ['验证时间', formatTimestamp(state.modelValidationResult.validated_at || '')],
        ['运行时', modelRuntimeDescription(runtime)],
        ['有效期', `${Number(state.modelValidationResult.expires_in_seconds || 0)} 秒`]
      ].map(([label, value]) => `
        <div class="summary-item">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
    }

    function renderModelSettingsSidebar() {
      const settings = state.modelSettings || {};
      const runtime = settings.effective_default_runtime || defaultModelRuntime();
      const systemRuntime = settings.system_default_runtime || {};
      const saved = settings.saved_default_model || {};
      modelCurrentRuntime.innerHTML = detailListMarkup(
        [
          ['当前状态', settings.status_text || (runtime.enabled ? '已启用模型优化' : '禁用模型增强功能')],
          ['当前运行时', modelRuntimeDescription(runtime)],
          ['模型来源', String(runtime.source || '').trim() || '未记录'],
          ['接口协议', String(runtime.wire_api || '').trim() || '未记录'],
        ],
        '当前没有可展示的运行时信息。'
      );
      modelSystemRuntime.innerHTML = detailListMarkup(
        [
          ['检测结果', systemRuntime.enabled ? '已检测到系统默认模型' : '未检测到系统默认模型'],
          ['系统默认运行时', modelRuntimeDescription(systemRuntime)],
          ['来源', String(systemRuntime.source || '').trim() || '未记录'],
          ['接口协议', String(systemRuntime.wire_api || '').trim() || '未记录'],
        ],
        '当前没有检测到系统默认模型。'
      );
      modelSavedRuntime.innerHTML = saved && Object.keys(saved).length
        ? detailListMarkup(
            [
              ['保存状态', saved.enabled ? '已保存' : '已关闭但保留配置'],
              ['模式', modelModeLabel(saved.mode || 'default')],
              ['供应商', saved.provider_label || (saved.mode === 'default' ? '系统默认模型' : '未填写')],
              ['模型名', saved.model || (saved.mode === 'default' ? (systemRuntime.model || '跟随系统默认模型') : '未填写')],
              ['接口协议', saved.wire_api || (saved.mode === 'default' ? (systemRuntime.wire_api || '跟随系统默认模型') : '未填写')],
              ['最近保存', saved.updated_at ? formatTimestamp(saved.updated_at) : ''],
              ['最近验证', saved.last_validated_at ? formatTimestamp(saved.last_validated_at) : ''],
            ],
            '暂无已保存默认配置。'
          )
        : '<div class="empty-state">当前没有持久化默认模型配置，系统将继续使用环境变量或 Codex 默认配置。</div>';
      modelAdminNote.textContent = settings.admin_configured
        ? '服务端已启用管理员令牌校验。输入正确令牌后，才可以切换开关、启用系统默认模型或保存自定义模型。'
        : '服务端未配置 AGENTS_ADMIN_TOKEN，当前弹窗为只读模式。';
      renderModelOverviewStrip();
      updateTokenEntryState();
    }

    function syncModelActionButtons() {
      const mode = document.getElementById('model_mode_select').value || 'default';
      const adminConfigured = !!(state.modelSettings && state.modelSettings.admin_configured);
      const tokenFilled = !!modelAdminTokenInput.value.trim();
      const validationMatchesCurrent = !!state.modelValidationToken && state.modelValidatedSignature === currentModelConfigSignature();
      modelValidateBtn.disabled = state.modelOperationPending || !adminConfigured || !tokenFilled || mode !== 'custom';
      modelSaveBtn.disabled = state.modelOperationPending
        || !adminConfigured
        || !tokenFilled
        || (mode === 'custom' && !validationMatchesCurrent)
        || (mode === 'default' && !modelHasUsableSystemDefault());
      modelRefreshBtn.disabled = state.modelOperationPending;
      syncModelModeButtons();
      modelSaveBtn.textContent = mode === 'disabled'
        ? '保存为关闭状态'
        : (mode === 'default' ? '启用系统默认模型' : '保存并启用自定义模型');
      renderModelOverviewStrip();
      updateTokenEntryState();
    }

    function updateModelConfigVisibility() {
      const mode = document.getElementById('model_mode_select').value || 'default';
      modelEnabledToggle.checked = mode !== 'disabled';
      modelConfigSection.hidden = mode === 'disabled';
      modelSourcePanel.hidden = mode === 'disabled';
      modelConfigFields.hidden = mode !== 'custom';
      modelValidateBtn.hidden = mode !== 'custom';
      syncModelSourceButtons();
      const provider = document.getElementById('model_provider_select').value || 'other';
      const guide = providerGuideMeta(provider);
      const systemRuntime = state.modelSettings && state.modelSettings.system_default_runtime
        ? state.modelSettings.system_default_runtime
        : defaultModelRuntime();
      const flowText = mode === 'disabled'
        ? '当前已禁用模型优化，模型接入配置已收起。若之后需要启用，再切换状态并补充配置。'
        : (mode === 'custom'
            ? '当前处于自定义模型接口模式：先补全接入配置，验证通过后再应用当前设置。'
            : '当前处于系统默认模型模式：先确认状态与管理员令牌，再应用当前设置。');
      const message = mode === 'custom'
        ? `${guide.title} 接入建议：Base URL 可参考 ${guide.example}。${guide.note}`
        : (mode === 'default'
            ? (systemRuntime.enabled
                ? `当前会优先尝试系统默认模型：${modelRuntimeDescription(systemRuntime)}。如需覆盖，可切换到“${modelModeLabel('custom')}”。`
                : '当前未检测到可用的系统默认模型。若要开启模型优化，请切换到“自定义模型接口”。')
            : '当前服务将统一使用“禁用模型增强功能”，不会再涉及任何模型配置。');
      modelFlowNote.textContent = flowText;
      modelRuntimeNote.innerHTML = `<p class="field-help">${escapeHtml(message)}</p>`;
      renderModelValidationSummary();
      renderModelSettingsSidebar();
      syncModelActionButtons();
    }

    function validateModelConfig(showError = true) {
      const config = collectModelConfig();
      if (config.mode === 'disabled') {
        if (showError) {
          setModelSettingsStatus('当前处于禁用模式，无需验证配置。');
        }
        return false;
      }
      if (config.mode === 'default') {
        if (!modelHasUsableSystemDefault()) {
          if (showError) {
            setModelSettingsStatus('当前未检测到系统默认模型，请改用自定义模型接口。', true);
          }
          return false;
        }
        return true;
      }
      const missing = [];
      if (!config.base_url) missing.push('Base URL');
      if (!config.model) missing.push('模型名');
      if (!config.api_key) missing.push('API Key');
      if (missing.length) {
        if (showError) {
          setModelSettingsStatus(`请先补齐：${missing.join('、')}。`, true);
        }
        return false;
      }
      return true;
    }

    function generationStatusLabel(status) {
      if (status === 'finalized') {
        return '已模型优化';
      }
      if (status === 'fallback_to_draft') {
        return '草稿回退';
      }
      return '草稿输出';
    }

    function generationStageNote(item, mode) {
      const status = String(item && item.finalization_status || '');
      const error = String(item && item.finalization_error || '').trim();
      if (mode === 'final' && item && item.final_markdown) {
        return '当前展示第二阶段大模型优化后的最终稿。';
      }
      if (status === 'fallback_to_draft') {
        return error ? `第二阶段优化失败，当前展示第一阶段草稿。原因：${error}` : '第二阶段优化失败，当前展示第一阶段草稿。';
      }
      return '当前展示第一阶段草稿。';
    }

    function preferredViewMode(item) {
      return item && item.final_markdown ? 'final' : 'draft';
    }

    function markdownForMode(item, mode) {
      if (!item) {
        return '';
      }
      if (mode === 'final' && item.final_markdown) {
        return sanitizeReferenceMarkdown(item.final_markdown);
      }
      if (item.draft_markdown) {
        return sanitizeReferenceMarkdown(item.draft_markdown);
      }
      return sanitizeReferenceMarkdown(item.display_markdown || item.agents_markdown || '');
    }

    function outputPathForMode(item, mode) {
      if (!item) {
        return '';
      }
      if (mode === 'final' && item.final_output_path) {
        return item.final_output_path;
      }
      if (item.draft_output_path) {
        return item.draft_output_path;
      }
      return item.display_output_path || item.output_path || '';
    }

    function renderReferenceList(target, items) {
      const referenceItems = Array.isArray(items) ? items.filter(item => item && item.path) : [];
      if (!referenceItems.length) {
        target.innerHTML = '<div class="empty-state">当前没有可展示的参考文件。</div>';
        return;
      }
      target.innerHTML = referenceItems.map(item => `
        <article class="reference-item">
          <strong>${escapeHtml(item.title || 'Reference')}</strong>
          <code>${escapeHtml(safeReferenceLabel(item.path || ''))}</code>
          <span>${escapeHtml(item.reason || '来自命中的能力模式参考。')}</span>
        </article>
      `).join('');
    }

    function progressStageLabel(stage) {
      const labels = {
        queued: '请求已提交',
        prepare_session: '准备问答会话',
        plan_ready: 'PLAN 已就绪',
        prepare_catalog: '准备能力目录',
        generate_draft: '阶段 1/2 生成草稿',
        draft_ready: '草稿已完成',
        optimize_final: '阶段 2/2 优化最终稿',
        validate_final: '校验最终稿',
        final_ready: '最终稿已完成',
        final_fallback: '回退到草稿',
        write_artifacts: '写入结果',
        completed: '生成完成',
        error: '生成失败'
      };
      return labels[String(stage || '').trim()] || '生成进行中';
    }

    function updateProgressElapsed() {
      if (!state.progressStartedAt) {
        progressElapsed.textContent = '0 秒';
        return;
      }
      const seconds = Math.max(0, Math.floor((Date.now() - state.progressStartedAt) / 1000));
      progressElapsed.textContent = `${seconds} 秒`;
    }

    function applyProgressSnapshot(snapshot) {
      const next = snapshot || {};
      state.progressSnapshot = next;
      progressStatus.hidden = false;
      progressStatus.classList.toggle('error', next.status === 'error');
      progressStatus.classList.toggle('done', !!next.done && next.status === 'ok');
      progressTitle.textContent = progressStageLabel(next.stage);
      progressBarFill.style.width = `${Math.max(0, Math.min(Number(next.percent || 0), 100))}%`;
      progressDetail.textContent = next.error
        ? `${next.message || '生成失败'}：${next.error}`
        : (next.message || '正在处理…');
      updateProgressElapsed();
    }

    function stopProgressPolling() {
      if (state.progressTimer) {
        window.clearInterval(state.progressTimer);
        state.progressTimer = 0;
      }
      state.progressPending = false;
    }

    async function pollProgressOnce(requestId) {
      if (!requestId || state.progressPending) {
        return;
      }
      state.progressPending = true;
      try {
        const response = await fetch(`/progress/${encodeURIComponent(requestId)}`);
        if (!response.ok) {
          return;
        }
        const payload = await response.json();
        if (payload.status === 'ok' && payload.result) {
          applyProgressSnapshot(payload.result);
          if (payload.result.done) {
            stopProgressPolling();
          }
        }
      } catch (error) {
        // Keep the last visible progress state; the main request will surface errors.
      } finally {
        state.progressPending = false;
      }
    }

    function startProgressTracking(requestId) {
      stopProgressPolling();
      state.currentRequestId = requestId;
      state.progressStartedAt = Date.now();
      applyProgressSnapshot({
        stage: 'queued',
        message: '请求已提交，正在准备处理阶段…',
        percent: 4,
        status: 'running',
        done: false
      });
      void pollProgressOnce(requestId);
      state.progressTimer = window.setInterval(() => {
        updateProgressElapsed();
        void pollProgressOnce(requestId);
      }, 1000);
    }

    function finishProgress(status, message) {
      const current = state.progressSnapshot || {};
      const normalizedStatus = status === 'error' ? 'error' : 'ok';
      applyProgressSnapshot({
        ...current,
        stage: normalizedStatus === 'error' ? 'error' : 'completed',
        message: message || current.message || '生成完成',
        percent: normalizedStatus === 'error' ? Math.max(8, Number(current.percent || 0)) : 100,
        status: normalizedStatus,
        done: true
      });
      stopProgressPolling();
    }

    function setStatus(text, isError = false) {
      statusEl.textContent = text;
      statusEl.className = isError ? 'status error' : 'status';
    }

    function fillSelect(selectId, values, labels) {
      const select = document.getElementById(selectId);
      select.innerHTML = '';
      values.forEach(value => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = labels && labels[value] ? labels[value] : value;
        select.appendChild(option);
      });
    }

    function refillSelect(selectId, values, labels, fallbackValue = '') {
      const select = document.getElementById(selectId);
      const currentValue = select.value;
      fillSelect(selectId, values, labels);
      if (values.includes(currentValue)) {
        select.value = currentValue;
        return;
      }
      if (fallbackValue && values.includes(fallbackValue)) {
        select.value = fallbackValue;
      }
    }

    function bindOtherInput(selectId, inputId, triggerValue = 'other') {
      const select = document.getElementById(selectId);
      const input = document.getElementById(inputId);
      const sync = () => {
        input.classList.toggle('visible', select.value === triggerValue);
      };
      select.addEventListener('change', sync);
      sync();
    }

    function getSelectedValues(kind) {
      return [...(state.selectedValues[kind] || [])];
    }

    function setSelectedValues(kind, values) {
      const previousSignature = state.intakeSession ? state.intakeBaseSignature : '';
      const normalized = [];
      const seen = new Set();
      (values || []).forEach(value => {
        const text = String(value || '').trim();
        const key = text.toLowerCase();
        if (!text || seen.has(key)) {
          return;
        }
        seen.add(key);
        normalized.push(text);
      });
      state.selectedValues[kind] = normalized;
      renderOptionGroup(kind);
      renderDraftSummary();
      if (state.intakeSession && previousSignature && basePayloadSignature(collectPayload()) !== previousSignature) {
        resetIntakeState('基础信息已更新，已清空后续问答与 PLAN.md，请重新开始问答。');
      }
    }

    function toggleSelectedValue(kind, value) {
      const current = getSelectedValues(kind);
      const normalized = String(value || '').trim();
      const lowered = normalized.toLowerCase();
      const exists = current.some(item => item.toLowerCase() === lowered);
      setSelectedValues(kind, exists ? current.filter(item => item.toLowerCase() !== lowered) : [...current, normalized]);
    }

    function addCustomValue(kind) {
      const input = kind === 'stack'
        ? stackCustomInput
        : (kind === 'constraint' ? constraintCustomInput : environmentCustomInput);
      const value = input.value.trim();
      if (!value) {
        return;
      }
      setSelectedValues(kind, [...getSelectedValues(kind), value]);
      input.value = '';
    }

    function removeSelectedValue(kind, value) {
      const lowered = String(value || '').trim().toLowerCase();
      setSelectedValues(kind, getSelectedValues(kind).filter(item => item.toLowerCase() !== lowered));
    }

    function renderOptionGroup(kind) {
      const target = kind === 'stack'
        ? stackOptions
        : (kind === 'constraint' ? constraintOptions : environmentOptions);
      const selectedTarget = kind === 'stack'
        ? stackSelected
        : (kind === 'constraint' ? constraintSelected : environmentSelected);
      const sourceOptions = kind === 'stack'
        ? OPTIONS.stack
        : (kind === 'constraint' ? OPTIONS.constraint : OPTIONS.environment);
      const options = sourceOptions.filter(value => value !== 'other');
      const selected = getSelectedValues(kind);
      const selectedLookup = new Set(selected.map(item => item.toLowerCase()));
      target.innerHTML = options.map(value => {
        const active = selectedLookup.has(value.toLowerCase());
        const display = kind === 'environment' ? (LABELS.environment[value] || value) : value;
        return `<button type="button" class="option-chip ${active ? 'active' : ''}" data-kind="${kind}" data-value="${escapeHtml(value)}">${escapeHtml(display)}</button>`;
      }).join('') + `<button type="button" class="option-chip freeform" data-kind="${kind}" data-freeform="true">+ 自定义</button>`;
      selectedTarget.innerHTML = selected.length
        ? selected.map(value => {
          const display = kind === 'environment' ? environmentDisplayValue([value]) : value;
          return `<div class="selected-tag">${escapeHtml(display)}<button type="button" data-kind-remove="${kind}" data-value="${escapeHtml(value)}">×</button></div>`;
        }).join('')
        : '<span class="panel-text">暂未选择</span>';
      Array.from(target.querySelectorAll('[data-value]')).forEach(button => {
        button.addEventListener('click', () => toggleSelectedValue(kind, button.getAttribute('data-value')));
      });
      const freeformButton = target.querySelector('[data-freeform="true"]');
      if (freeformButton) {
        freeformButton.addEventListener('click', () => {
          const input = kind === 'stack'
            ? stackCustomInput
            : (kind === 'constraint' ? constraintCustomInput : environmentCustomInput);
          input.focus();
        });
      }
      Array.from(selectedTarget.querySelectorAll('[data-kind-remove]')).forEach(button => {
        button.addEventListener('click', () => removeSelectedValue(kind, button.getAttribute('data-value')));
      });
    }

    function basePayloadSignature(payload) {
      return JSON.stringify(payload || {});
    }

    function isDeferredAnswer(value) {
      if (Array.isArray(value)) {
        return value.some(item => isDeferredAnswer(item));
      }
      return String(value || '').trim().startsWith(DEFERRED_ANSWER_PREFIX);
    }

    function deferredPlaceholder(question) {
      const title = question && question.title ? question.title : '该问题';
      return `${DEFERRED_ANSWER_PREFIX}${title}需后续补充`;
    }

    function clearPlanAutoTimer() {
      if (state.planAutoTimer) {
        window.clearTimeout(state.planAutoTimer);
        state.planAutoTimer = 0;
      }
    }

    function resetIntakeState(message = '') {
      const hadSession = !!state.intakeSession;
      clearPlanAutoTimer();
      state.intakeSession = null;
      state.intakeAnswers = {};
      state.ignoredQuestions = {};
      state.questionDrafts = {};
      state.intakeBaseSignature = '';
      state.generatedSessionId = '';
      renderQuestionnaire();
      renderPlanPreview();
      if (message && hadSession) {
        setStatus(message);
      }
    }

    function splitConstraintsAndNotes(values) {
      const note = (values || []).find(item => String(item || '').startsWith(FREEFORM_NOTE_PREFIX)) || '';
      return {
        constraints: (values || []).filter(item => !String(item || '').startsWith(FREEFORM_NOTE_PREFIX)),
        note: note ? note.slice(FREEFORM_NOTE_PREFIX.length).trim() : ''
      };
    }

    function getFieldValue(selectId, otherId = '') {
      const select = document.getElementById(selectId);
      if (!otherId || select.value !== 'other') {
        return select.value;
      }
      return document.getElementById(otherId).value.trim();
    }

    function setSelectOrOther(selectId, otherId, value) {
      const select = document.getElementById(selectId);
      const other = document.getElementById(otherId);
      const normalized = String(value || '').trim();
      const available = Array.from(select.options).map(option => option.value);
      if (!normalized) {
        select.value = available.includes('other') ? 'other' : (available[0] || '');
        other.value = '';
        select.dispatchEvent(new Event('change'));
        return;
      }
      if (available.includes(normalized)) {
        select.value = normalized;
        other.value = '';
      } else {
        select.value = 'other';
        other.value = normalized;
      }
      select.dispatchEvent(new Event('change'));
    }

    function activeTemplateValue() {
      return getFieldValue('template_select', 'template_other') || 'custom';
    }

    function activeTemplateMeta() {
      const value = document.getElementById('template_select').value;
      return TEMPLATE_META[value] || TEMPLATE_META.custom;
    }

    function renderTemplateCard() {
      const value = document.getElementById('template_select').value;
      const meta = TEMPLATE_META[value] || TEMPLATE_META.custom;
      templateTitle.textContent = meta.label;
      templateSummary.textContent = meta.intro;
      templateHighlights.innerHTML = meta.highlights.map(item => `<li>${escapeHtml(item)}</li>`).join('');
    }

    function normalizedValueSignature(value) {
      if (Array.isArray(value)) {
        return JSON.stringify(value.map(item => String(item || '').trim().toLowerCase()).filter(Boolean).sort());
      }
      return String(value || '').trim().toLowerCase();
    }

    function templateSuggestionSnapshot() {
      return {
        target_user: getFieldValue('target_user_select', 'target_user_other'),
        environment: getSelectedValues('environment'),
        stack: getSelectedValues('stack'),
        constraint: getSelectedValues('constraint')
      };
    }

    function templateFeedbackValue(field, value) {
      if (field === 'target_user') {
        return labelFor('targetUser', value);
      }
      if (field === 'environment') {
        return environmentDisplayValue(value);
      }
      if (Array.isArray(value)) {
        return value.length ? value.join(', ') : '清空';
      }
      return String(value || '').trim() || '未填写';
    }

    function applyTemplateDefaults(force = false) {
      const before = templateSuggestionSnapshot();
      const value = document.getElementById('template_select').value;
      const meta = TEMPLATE_META[value] || TEMPLATE_META.custom;
      const defaults = meta.defaults || {};
      const currentTargetUser = getFieldValue('target_user_select', 'target_user_other');
      const currentEnvironments = getSelectedValues('environment');
      const defaultEnvironments = splitEnvironmentValue(defaults.environment || 'browser_service');
      if (force || currentEnvironments.length === 0) {
        setSelectedValues('environment', defaultEnvironments);
      }
      if (force || !currentTargetUser || currentTargetUser === 'general') {
        setSelectOrOther('target_user_select', 'target_user_other', defaults.targetUser || 'general');
      }
      if (force || getSelectedValues('stack').length === 0) {
        setSelectedValues('stack', defaults.stack || []);
      }
      if (force || getSelectedValues('constraint').length === 0) {
        setSelectedValues('constraint', defaults.constraints || []);
      }
      renderDraftSummary();
      const after = templateSuggestionSnapshot();
      return [
        ['target_user', '目标用户'],
        ['environment', '运行环境'],
        ['stack', '偏好技术栈'],
        ['constraint', '约束条件']
      ]
        .filter(([field]) => normalizedValueSignature(before[field]) !== normalizedValueSignature(after[field]))
        .map(([field, label]) => ({
          field,
          label,
          before: templateFeedbackValue(field, before[field]),
          after: templateFeedbackValue(field, after[field])
        }));
    }

    function collectPayload() {
      const creativeNotes = creativeNotesInput.value.trim();
      const constraints = getSelectedValues('constraint');
      if (creativeNotes) {
        constraints.push(`${FREEFORM_NOTE_PREFIX}${creativeNotes}`);
      }
      return {
        template_type: activeTemplateValue(),
        industry: getFieldValue('industry_select', 'industry_other'),
        task_description: document.getElementById('task_description').value.trim(),
        target_user: getFieldValue('target_user_select', 'target_user_other'),
        output_language: getFieldValue('output_language_select', 'output_language_other'),
        environment: getSelectedValues('environment').join(', '),
        constraints,
        preferred_stack: getSelectedValues('stack'),
        risk_tolerance: getFieldValue('risk_tolerance_select', 'risk_tolerance_other')
      };
    }

    function handleBaseFormChange() {
      renderDraftSummary();
      if (state.intakeSession && state.intakeBaseSignature && basePayloadSignature(collectPayload()) !== state.intakeBaseSignature) {
        resetIntakeState('基础信息已更新，已清空后续问答与 PLAN.md，请重新开始问答。');
      }
    }

    function renderDraftSummary() {
      const payload = collectPayload();
      const split = splitConstraintsAndNotes(payload.constraints);
      const rows = [
        ['模板', templateLabel(document.getElementById('template_select').value === 'other' ? payload.template_type : document.getElementById('template_select').value)],
        ['行业', payload.industry || '未填写'],
        ['目标用户', labelFor('targetUser', payload.target_user)],
        ['输出语言', labelFor('outputLanguage', payload.output_language)],
        ['运行环境', environmentDisplayValue(payload.environment)],
        ['风险容忍度', labelFor('riskTolerance', payload.risk_tolerance)],
        ['偏好技术栈', payload.preferred_stack.length ? payload.preferred_stack.join(', ') : '未填写'],
        ['约束条件', split.constraints.length ? split.constraints.join(' / ') : '未填写'],
        ['补充说明', split.note || '未填写'],
        ['任务摘要', payload.task_description || '未填写']
      ];
      draftSummary.innerHTML = rows.map(([label, value]) => `
        <div class="summary-item">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
    }

    function iconForScreen(screenId) {
      if (screenId === 'workspace') {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3.75h8.5L19.5 8.75v11.5a1.5 1.5 0 0 1-1.5 1.5H6a1.5 1.5 0 0 1-1.5-1.5v-15A1.5 1.5 0 0 1 6 3.75Z"/><path d="M14.5 3.75v5h5"/><path d="m9 15 5.25-5.25 1.75 1.75L10.75 16.75 8.5 17.5 9 15Z"/></svg>';
      }
      if (screenId === 'library') {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 7.25A1.75 1.75 0 0 1 7.25 5.5h9.5A1.75 1.75 0 0 1 18.5 7.25v9.5a1.75 1.75 0 0 1-1.75 1.75h-9.5A1.75 1.75 0 0 1 5.5 16.75Z"/><path d="M8.5 9.5h7"/><path d="M8.5 13h5.5"/><path d="M3.5 9.25v8a2 2 0 0 0 2 2h8"/><path d="M9 3.5h8a2 2 0 0 1 2 2v8"/></svg>';
      }
      return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3.75h8.5L19.5 8.75v11.5a1.5 1.5 0 0 1-1.5 1.5H6a1.5 1.5 0 0 1-1.5-1.5v-15A1.5 1.5 0 0 1 6 3.75Z"/><path d="M14.5 3.75v5h5"/><path d="M8.5 12.25h7"/><path d="M8.5 16h4.5"/><path d="m8.25 7.75 1.75 1.75 3.75-3.75"/></svg>';
    }

    function renderMenu() {
      menu.innerHTML = MENU_CONFIG.map(item => `
        <button type="button" class="menu-button ${state.activeScreen === item.id ? 'active' : ''}" data-screen-button="${item.id}" data-label="${item.title}" title="${item.title}">
          <div class="menu-icon">${iconForScreen(item.id)}</div>
          <div class="menu-copy">
            <strong>${item.title}</strong>
            <span>${item.description}</span>
          </div>
        </button>
      `).join('');
      Array.from(menu.querySelectorAll('[data-screen-button]')).forEach(button => {
        button.addEventListener('click', () => showScreen(button.getAttribute('data-screen-button')));
      });
    }

    function showScreen(screenId) {
      state.activeScreen = screenId;
      screens.forEach(screen => {
        screen.classList.toggle('active', screen.getAttribute('data-screen') === screenId);
      });
      renderMenu();
      renderOverview();
      if (window.innerWidth <= 960) {
        appShell.classList.add('sidebar-collapsed');
      }
      syncSidebarState();
    }

    function renderStepList() {
      stepList.innerHTML = STEP_CONFIG.map((step, index) => `
        <button type="button" class="step-button ${state.currentStep === index ? 'active' : ''}" data-step-button="${index}">
          <strong>${index + 1}. ${step.title}</strong>
          <span>${step.description}</span>
        </button>
      `).join('');
      Array.from(stepList.querySelectorAll('[data-step-button]')).forEach(button => {
        button.addEventListener('click', () => showStep(Number(button.getAttribute('data-step-button'))));
      });
    }

    function syncStepActions() {
      prevStepBtn.style.visibility = state.currentStep === 0 ? 'hidden' : 'visible';
      nextStepBtn.style.display = state.currentStep <= 1 ? 'inline-flex' : 'none';
      if (state.currentStep === 2) {
        generateBtn.style.display = 'inline-flex';
        generateBtn.textContent = '开始问答';
      } else if (state.currentStep === 3) {
        generateBtn.style.display = 'inline-flex';
        generateBtn.textContent = '继续';
      } else if (state.currentStep === 4) {
        generateBtn.style.display = 'inline-flex';
        generateBtn.textContent = state.generationPending ? '生成中…' : '立即生成';
      } else {
        generateBtn.style.display = 'none';
      }
      generateBtn.disabled = state.generationPending;
    }

    function showStep(index) {
      if (index !== 4) {
        clearPlanAutoTimer();
      }
      state.currentStep = Math.max(0, Math.min(index, formSteps.length - 1));
      formSteps.forEach((step, currentIndex) => {
        step.classList.toggle('active', currentIndex === state.currentStep);
      });
      renderStepList();
      syncStepActions();
      renderDraftSummary();
      if (state.currentStep === 3) {
        renderQuestionnaire();
      }
      if (state.currentStep === 4) {
        renderPlanPreview();
      }
    }

    function validateCurrentStep() {
      const payload = collectPayload();
      if (state.currentStep === 0 && (!payload.industry || !payload.task_description)) {
        setStatus('请先填写行业和任务描述，再进入下一步。', true);
        return false;
      }
      return true;
    }

    function renderOverview() {
      const libraryTotal = Number(state.overview.library_total || state.library.length || 0);
      const runtime = defaultModelRuntime();
      const runtimeLabel = Object.keys(runtime || {}).length ? modelRuntimeDescription(runtime) : '未配置默认模型';
      const modelEnabled = !!(state.modelSettings ? state.modelSettings.model_enabled : runtime.enabled);
      const modelStatusClass = modelEnabled ? 'is-enabled' : 'is-disabled';
      heroPills.innerHTML = [
        `<div class="pill"><strong>${escapeHtml(libraryTotal)}</strong> 系统案例</div>`,
        `<div class="pill"><strong>${escapeHtml(state.activeScreen === 'workspace' ? '向导式' : '产品化')}</strong> 交互模式</div>`,
        `<div class="pill"><strong>${escapeHtml(adminEnabled ? 'Admin' : 'Public')}</strong> 服务模式</div>`
      ].join('');
      topbarActions.innerHTML = [
        `<button type="button" class="pill-button model-status-button ${modelStatusClass}" id="model-status-trigger">
          <span class="model-status-main">
            <span class="model-status-dot" aria-hidden="true"></span>
            <span class="model-status-copy">
              <strong>模型优化 ${escapeHtml(modelEnabled ? '已开启' : '已关闭')}</strong>
              <span>${escapeHtml(truncateText(runtimeLabel, 34) || '未配置默认模型')}</span>
            </span>
          </span>
          <span class="model-status-cta">开关与配置</span>
        </button>`,
        `<div class="topbar-card topbar-summary-card">
          <div class="topbar-summary-head">案例库概览</div>
          <div class="topbar-summary-list">
            <div class="topbar-summary-item">
              <strong>${escapeHtml(`${libraryTotal} 个系统案例`)}</strong>
              <span>当前可复用的系统创建结果</span>
            </div>
            <div class="topbar-summary-item">
              <strong>优先回看与复用</strong>
              <span>先看已有案例，再决定是否重做</span>
            </div>
          </div>
        </div>`
      ].join('');
      const modelTrigger = document.getElementById('model-status-trigger');
      if (modelTrigger) {
        modelTrigger.addEventListener('click', openModelModal);
      }
      sidebarFooter.innerHTML = `
        <strong>Navigation</strong>
        当前侧栏只保留创建、案例和结果三类入口；模型优化开关与配置统一收敛到右上角状态按钮。
      `;
      footerNote.textContent = '生产界面默认隐藏后台分析信息。创建页只负责收集任务、补充问答、预览 PLAN.md 和生成结果；模型优化统一通过右上角状态按钮开关与配置。';
      libraryTotalPill.textContent = String(libraryTotal);
      updateModelConfigVisibility();
    }

    function resultMetaMarkup(item) {
      const request = item.request || {};
      const chips = [
        item.template_label || templateLabel(item.template_type),
        request.industry || '未指定行业',
        labelFor('outputLanguage', request.output_language),
        environmentDisplayValue(request.environment),
        `生成于 ${formatTimestamp(item.created_at || item.timestamp)}`
      ];
      return chips.map(value => `<div class="chip alt">${escapeHtml(value)}</div>`).join('');
    }

    function filteredLibraryItems() {
      const search = librarySearch.value.trim().toLowerCase();
      const industry = libraryIndustryFilter.value || 'all';
      const template = libraryTemplateFilter.value || 'all';
      const language = libraryLanguageFilter.value || 'all';
      const items = state.library.filter(item => {
        const request = item.request || {};
        if (industry !== 'all' && request.industry !== industry) return false;
        if (template !== 'all' && item.template_type !== template) return false;
        if (language !== 'all' && request.output_language !== language) return false;
        if (!search) return true;
        const haystack = [
          item.title,
          item.summary,
          item.task_excerpt,
          item.template_type,
          request.industry,
          request.target_user,
          request.output_language,
          request.environment,
          request.task_description,
          ...(request.constraints || []),
          ...(request.preferred_stack || [])
        ].join(' ').toLowerCase();
        return haystack.includes(search);
      });
      const isDefaultView = !search && industry === 'all' && template === 'all' && language === 'all';
      return {
        all: items,
        visible: isDefaultView ? items.slice(0, 8) : items,
        isDefaultView
      };
    }

    function updateLibraryFilters() {
      const industries = Array.from(new Set(state.library.map(item => item.request && item.request.industry).filter(Boolean)));
      const templates = Array.from(new Set(state.library.map(item => item.template_type).filter(Boolean)));
      const languages = Array.from(new Set(state.library.map(item => item.request && item.request.output_language).filter(Boolean)));
      refillSelect('library-industry-filter', ['all', ...industries], { all: '全部行业' }, 'all');
      refillSelect('library-template-filter', ['all', ...templates], { all: '全部模板', ...LABELS.template }, 'all');
      refillSelect('library-language-filter', ['all', ...languages], { all: '全部语言', ...LABELS.outputLanguage }, 'all');
    }

    function renderLibrary() {
      updateLibraryFilters();
      const result = filteredLibraryItems();
      const allCount = state.library.length;
      const visibleCount = result.visible.length;
      librarySummary.textContent = allCount
        ? (result.isDefaultView
            ? `当前共 ${allCount} 个系统创建案例，默认展示最近 ${visibleCount} 条。`
            : `当前共 ${allCount} 个系统创建案例，符合筛选条件的有 ${result.all.length} 条。`)
        : '当前还没有系统创建案例。完成一次生成后，这里会自动出现对应案例卡片。';
      if (!allCount) {
        libraryGrid.innerHTML = '<div class="empty-state">当前还没有系统创建案例。先回到“创建”完成一次生成。</div>';
        return;
      }
      if (!visibleCount) {
        libraryGrid.innerHTML = '<div class="empty-state">当前筛选条件下没有匹配案例。</div>';
        return;
      }
      libraryGrid.innerHTML = result.visible.map(item => {
        const request = item.request || {};
        const fileName = basename(item.output_path || item.path || '');
        const downloadHref = fileName ? `/files/${encodeURIComponent(fileName)}` : '#';
        return `
          <article class="library-card">
            <div class="meta-row">
              <div class="chip alt">${escapeHtml(item.template_label || templateLabel(item.template_type))}</div>
              <div class="chip">${escapeHtml(request.industry || '未指定行业')}</div>
              <div class="chip">${escapeHtml(labelFor('outputLanguage', request.output_language))}</div>
              <div class="chip">${escapeHtml(generationStatusLabel(item.finalization_status))}</div>
            </div>
            <div>
              <h3>${escapeHtml(item.title || '未命名案例')}</h3>
              <p style="margin-top:10px;">${escapeHtml(item.summary || '暂无简介')}</p>
            </div>
            <p>${escapeHtml(item.task_excerpt || truncateText(request.task_description || ''))}</p>
            <div class="card-meta">
              <span>${escapeHtml(formatTimestamp(item.created_at || item.timestamp))}</span>
              <span>${escapeHtml(environmentDisplayValue(request.environment))}</span>
              <span>${escapeHtml((request.preferred_stack || []).slice(0, 3).join(' / ') || '未显式指定技术栈')}</span>
            </div>
            <div class="library-actions">
              <button type="button" class="button-secondary" data-library-detail="${escapeHtml(item.artifact_id)}">查看详情</button>
              <button type="button" class="button-primary" data-library-copy="${escapeHtml(item.artifact_id)}">一键复制</button>
              <a class="button-quiet" href="${downloadHref}" download="${escapeHtml(fileName)}">下载</a>
            </div>
          </article>
        `;
      }).join('');
      Array.from(libraryGrid.querySelectorAll('[data-library-detail]')).forEach(button => {
        button.addEventListener('click', async () => {
          const artifactId = button.getAttribute('data-library-detail');
          await openLibraryDetail(artifactId);
        });
      });
      Array.from(libraryGrid.querySelectorAll('[data-library-copy]')).forEach(button => {
        button.addEventListener('click', async () => {
          const artifactId = button.getAttribute('data-library-copy');
          const detail = await ensureLibraryDetail(artifactId);
          if (detail) {
            await copyText(detail.agents_markdown, '案例文档已复制。');
          }
        });
      });
    }

    async function refreshOverview() {
      const response = await fetch('/overview');
      const payload = await response.json();
      state.overview = payload.result || payload;
      renderOverview();
      return state.overview;
    }

    function trySelectProviderFromLabel(value) {
      const text = String(value || '').trim();
      if (!text) {
        document.getElementById('model_provider_select').value = 'openai';
        document.getElementById('model_provider_other').value = '';
        return;
      }
      const directMatch = Object.keys(LABELS.modelProvider).find(key => key === text);
      if (directMatch) {
        document.getElementById('model_provider_select').value = directMatch;
        document.getElementById('model_provider_other').value = '';
        return;
      }
      const labelMatch = Object.entries(LABELS.modelProvider).find(([, label]) => label === text);
      if (labelMatch) {
        document.getElementById('model_provider_select').value = labelMatch[0];
        document.getElementById('model_provider_other').value = '';
        return;
      }
      document.getElementById('model_provider_select').value = 'other';
      document.getElementById('model_provider_other').value = text;
    }

    function applyModelSettingsToForm(settings) {
      const saved = settings && settings.saved_default_model ? settings.saved_default_model : {};
      const runtime = settings && settings.effective_default_runtime ? settings.effective_default_runtime : {};
      const systemRuntime = settings && settings.system_default_runtime ? settings.system_default_runtime : {};
      const mode = saved && Object.keys(saved).length
        ? String(saved.mode || 'default')
        : (settings && settings.model_enabled
            ? (systemRuntime.enabled ? 'default' : (saved.has_custom_config ? 'custom' : 'default'))
            : 'disabled');
      document.getElementById('model_mode_select').value = mode;
      modelEnabledToggle.checked = mode !== 'disabled';
      trySelectProviderFromLabel(saved.provider_label || runtime.provider_label || systemRuntime.provider_label || 'openai');
      document.getElementById('model_wire_api_select').value = saved.wire_api || runtime.wire_api || systemRuntime.wire_api || 'chat_completions';
      document.getElementById('model_base_url').value = saved.base_url || '';
      document.getElementById('model_name').value = saved.model || runtime.model || systemRuntime.model || '';
      document.getElementById('model_api_key').value = '';
      syncModelTokenVisibilityButton();
      clearModelValidationState();
      renderModelValidationSummary();
      updateModelConfigVisibility();
      if (settings && settings.status_text) {
        setModelSettingsStatus(`当前状态：${settings.status_text}`);
      }
    }

    function openModelModal() {
      state.modelModalOpen = true;
      modelModal.classList.add('open');
      modelModalBackdrop.classList.add('open');
      modelModal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      void refreshModelSettings()
        .then(() => {
          if (state.modelSettings && state.modelSettings.admin_configured && !modelAdminTokenInput.value.trim()) {
            modelAdminTokenInput.focus();
          }
        })
        .catch(error => {
          setModelSettingsStatus(error.message || '读取模型配置失败', true);
        });
    }

    function closeModelModal() {
      state.modelModalOpen = false;
      modelModal.classList.remove('open');
      modelModalBackdrop.classList.remove('open');
      modelModal.setAttribute('aria-hidden', 'true');
      if (!libraryDrawer.classList.contains('open')) {
        syncSidebarState();
      }
    }

    async function refreshModelSettings() {
      const response = await fetch('/model-config');
      const payload = await response.json();
      if (!response.ok || payload.status !== 'ok') {
        throw new Error(payload.message || '读取模型配置失败');
      }
      state.modelSettings = payload.result || {};
      applyModelSettingsToForm(state.modelSettings);
      renderModelSettingsSidebar();
      syncModelActionButtons();
      renderOverview();
      return state.modelSettings;
    }

    async function validateDefaultModelSettings() {
      if (!validateModelConfig(true)) {
        return;
      }
      state.modelOperationPending = true;
      syncModelActionButtons();
      setModelSettingsStatus('正在验证模型配置，请稍候…');
      try {
        const response = await fetch('/model-config/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_token: modelAdminTokenInput.value.trim(),
            model_config: collectModelConfig()
          })
        });
        const payload = await response.json();
        if (!response.ok || payload.status !== 'ok') {
          throw new Error(payload.message || '模型配置验证失败');
        }
        state.modelValidationResult = payload.result || null;
        state.modelValidationToken = String((payload.result && payload.result.validation_token) || '');
        state.modelValidatedSignature = currentModelConfigSignature();
        renderModelValidationSummary();
        syncModelActionButtons();
        setModelSettingsStatus('模型配置验证通过，现在可以保存为服务默认模型。');
      } catch (error) {
        clearModelValidationState();
        renderModelValidationSummary();
        syncModelActionButtons();
        setModelSettingsStatus(error.message || String(error), true);
      } finally {
        state.modelOperationPending = false;
        syncModelActionButtons();
      }
    }

    async function saveDefaultModelSettings() {
      const mode = document.getElementById('model_mode_select').value || 'default';
      if (mode === 'disabled') {
        await disableDefaultModelSettings();
        return;
      }
      if (mode === 'default') {
        await enableDefaultModelSettings();
        return;
      }
      if (!validateModelConfig(true)) {
        return;
      }
      if (!state.modelValidationToken || state.modelValidatedSignature !== currentModelConfigSignature()) {
        setModelSettingsStatus('当前配置尚未通过验证，或验证后已被修改，请重新验证后再保存。', true);
        return;
      }
      state.modelOperationPending = true;
      syncModelActionButtons();
      setModelSettingsStatus('正在保存默认模型配置…');
      try {
        const response = await fetch('/model-config/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_token: modelAdminTokenInput.value.trim(),
            validation_token: state.modelValidationToken,
            model_config: collectModelConfig()
          })
        });
        const payload = await response.json();
        if (!response.ok || payload.status !== 'ok') {
          throw new Error(payload.message || '保存默认模型失败');
        }
        state.modelSettings = payload.result || {};
        applyModelSettingsToForm(state.modelSettings);
        await refreshOverview();
        setModelSettingsStatus('默认模型已保存并生效。');
      } catch (error) {
        setModelSettingsStatus(error.message || String(error), true);
      } finally {
        state.modelOperationPending = false;
        syncModelActionButtons();
      }
    }

    async function enableDefaultModelSettings() {
      state.modelOperationPending = true;
      syncModelActionButtons();
      setModelSettingsStatus('正在启用模型优化，并优先尝试系统默认模型…');
      try {
        const response = await fetch('/model-config/enable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_token: modelAdminTokenInput.value.trim()
          })
        });
        const payload = await response.json();
        if (!response.ok || payload.status !== 'ok') {
          throw new Error(payload.message || '启用默认模型失败');
        }
        state.modelSettings = payload.result || {};
        applyModelSettingsToForm(state.modelSettings);
        await refreshOverview();
        setModelSettingsStatus('模型优化已开启，当前优先使用系统默认模型。');
      } catch (error) {
        if (!modelHasUsableSystemDefault()) {
          setModelMode('custom', { clearValidation: true });
        }
        setModelSettingsStatus(error.message || String(error), true);
      } finally {
        state.modelOperationPending = false;
        syncModelActionButtons();
      }
    }

    async function disableDefaultModelSettings() {
      state.modelOperationPending = true;
      syncModelActionButtons();
      setModelSettingsStatus('正在禁用模型增强功能…');
      try {
        const response = await fetch('/model-config/disable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_token: modelAdminTokenInput.value.trim()
          })
        });
        const payload = await response.json();
        if (!response.ok || payload.status !== 'ok') {
          throw new Error(payload.message || '禁用默认模型失败');
        }
        state.modelSettings = payload.result || {};
        applyModelSettingsToForm(state.modelSettings);
        await refreshOverview();
        setModelSettingsStatus('模型优化已关闭。当前不会再涉及任何模型配置。');
      } catch (error) {
        setModelSettingsStatus(error.message || String(error), true);
      } finally {
        state.modelOperationPending = false;
        syncModelActionButtons();
      }
    }

    async function refreshLibrary() {
      const response = await fetch('/library');
      const payload = await response.json();
      state.library = payload.result || [];
      renderLibrary();
      renderOverview();
      return state.library;
    }

    async function ensureLibraryDetail(artifactId) {
      if (!artifactId) return null;
      if (state.libraryDetails[artifactId]) {
        return state.libraryDetails[artifactId];
      }
      const response = await fetch(`/library/${encodeURIComponent(artifactId)}`);
      const payload = await response.json();
      if (!response.ok || payload.status !== 'ok') {
        throw new Error(payload.message || '读取案例详情失败');
      }
      state.libraryDetails[artifactId] = payload.result || {};
      return state.libraryDetails[artifactId];
    }

    function openDrawer() {
      libraryDrawer.classList.add('open');
      drawerBackdrop.classList.add('open');
      libraryDrawer.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
      libraryDrawer.classList.remove('open');
      drawerBackdrop.classList.remove('open');
      libraryDrawer.setAttribute('aria-hidden', 'true');
      if (window.innerWidth > 960 || appShell.classList.contains('sidebar-collapsed')) {
        document.body.style.overflow = '';
      }
    }

    function syncDrawerVersionControls() {
      const item = state.drawerItem;
      const hasFinal = !!(item && item.final_markdown);
      const mode = hasFinal && state.drawerViewMode === 'final' ? 'final' : 'draft';
      state.drawerViewMode = mode;
      drawerViewFinalBtn.disabled = !hasFinal;
      drawerViewDraftBtn.disabled = !markdownForMode(item, 'draft');
      drawerViewFinalBtn.classList.toggle('active', mode === 'final');
      drawerViewDraftBtn.classList.toggle('active', mode === 'draft');
    }

    function syncDrawerDownload() {
      const filePath = outputPathForMode(state.drawerItem, state.drawerViewMode);
      const fileName = basename(filePath);
      if (fileName) {
        drawerDownloadBtn.href = `/files/${encodeURIComponent(fileName)}`;
        drawerDownloadBtn.setAttribute('download', fileName);
        drawerDownloadBtn.style.pointerEvents = '';
        drawerDownloadBtn.style.opacity = '1';
      } else {
        drawerDownloadBtn.href = '#';
        drawerDownloadBtn.removeAttribute('download');
        drawerDownloadBtn.style.pointerEvents = 'none';
        drawerDownloadBtn.style.opacity = '0.55';
      }
    }

    function syncDrawerView() {
      const item = state.drawerItem;
      if (!item) {
        return;
      }
      syncDrawerVersionControls();
      drawerStageNote.textContent = generationStageNote(item, state.drawerViewMode);
      renderMarkdownWithLineNumbers(drawerMarkdown, markdownForMode(item, state.drawerViewMode) || '');
      syncDrawerDownload();
    }

    function renderDrawer(item) {
      state.drawerItem = item;
      state.drawerViewMode = preferredViewMode(item);
      const request = item.request || {};
      const split = splitConstraintsAndNotes(request.constraints || []);
      drawerEyebrow.textContent = item.template_label || templateLabel(item.template_type);
      drawerTitle.textContent = item.title || '未命名案例';
      drawerSummary.textContent = item.summary || '暂无简介';
      drawerMeta.innerHTML = resultMetaMarkup(item);
      drawerTask.textContent = item.task_excerpt || request.task_description || '旧记录没有保存任务摘要。';
      drawerRequest.innerHTML = [
        ['模板', item.template_label || templateLabel(item.template_type)],
        ['行业', request.industry || '未填写'],
        ['目标用户', labelFor('targetUser', request.target_user)],
        ['输出语言', labelFor('outputLanguage', request.output_language)],
        ['运行环境', environmentDisplayValue(request.environment)],
        ['风险容忍度', labelFor('riskTolerance', request.risk_tolerance)],
        ['偏好技术栈', (request.preferred_stack || []).join(', ') || '未填写'],
        ['约束条件', split.constraints.join(' / ') || '未填写'],
        ['补充说明', split.note || '未填写']
      ].map(([label, value]) => `
        <div class="detail-item">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
      drawerStage.innerHTML = [
        ['当前状态', generationStatusLabel(item.finalization_status)],
        ['主展示版本', item.final_markdown ? '最终稿' : '草稿'],
        ['模型优化', item.used_model_optimization ? '已启用' : '未启用'],
        ['模型来源', modelRuntimeDescription(item.model_runtime || {})],
        ['状态说明', item.finalization_error || (item.final_markdown ? '第二阶段优化完成。' : '当前仅保留草稿结果。')]
      ].map(([label, value]) => `
        <div class="detail-item">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
      renderReferenceList(drawerReferences, item.reference_files || []);
      drawerPlanNote.textContent = item.plan_markdown
        ? '当前展示该案例在生成 AGENTS.md 之前形成的计划稿。'
        : '该案例没有保存 PLAN.md。';
      renderMarkdownWithLineNumbers(drawerPlanMarkdown, item.plan_markdown || '当前案例没有保存 PLAN.md。');
      drawerPlanSection.style.display = 'block';
      syncDrawerView();
      openDrawer();
    }

    async function openLibraryDetail(artifactId) {
      try {
        const item = await ensureLibraryDetail(artifactId);
        if (!item) return;
        renderDrawer(item);
      } catch (error) {
        setStatus(error.message || String(error), true);
      }
    }

    function applyRequestToForm(request) {
      if (!request || (!request.industry && !request.task_description)) {
        setStatus('该案例缺少可复用的输入元数据。', true);
        return;
      }
      const split = splitConstraintsAndNotes(request.constraints || []);
      setSelectOrOther('template_select', 'template_other', request.template_type || 'custom');
      setSelectOrOther('industry_select', 'industry_other', request.industry || '');
      setSelectOrOther('target_user_select', 'target_user_other', request.target_user || 'general');
      setSelectOrOther('output_language_select', 'output_language_other', request.output_language || 'zh');
      setSelectedValues('environment', splitEnvironmentValue(request.environment || ''));
      setSelectOrOther('risk_tolerance_select', 'risk_tolerance_other', request.risk_tolerance || 'medium');
      document.getElementById('task_description').value = request.task_description || '';
      setSelectedValues('stack', request.preferred_stack || []);
      setSelectedValues('constraint', split.constraints);
      creativeNotesInput.value = split.note;
      resetIntakeState();
      renderTemplateCard();
      renderDraftSummary();
      closeDrawer();
      showScreen('workspace');
      showStep(0);
      setStatus('案例输入已回填到创建向导，可继续修改后重新生成。');
    }

    function syncResultVersionControls() {
      const item = state.lastResult;
      const hasFinal = !!(item && item.final_markdown);
      const mode = hasFinal && state.resultViewMode === 'final' ? 'final' : 'draft';
      state.resultViewMode = mode;
      resultViewFinalBtn.disabled = !hasFinal;
      resultViewDraftBtn.disabled = !markdownForMode(item, 'draft');
      resultViewFinalBtn.classList.toggle('active', mode === 'final');
      resultViewDraftBtn.classList.toggle('active', mode === 'draft');
    }

    function syncResultDownload() {
      const filePath = outputPathForMode(state.lastResult, state.resultViewMode);
      const fileName = basename(filePath);
      if (fileName) {
        resultDownloadBtn.href = `/files/${encodeURIComponent(fileName)}`;
        resultDownloadBtn.setAttribute('download', fileName);
        resultDownloadBtn.style.pointerEvents = '';
        resultDownloadBtn.style.opacity = '1';
      } else {
        resultDownloadBtn.href = '#';
        resultDownloadBtn.removeAttribute('download');
        resultDownloadBtn.style.pointerEvents = 'none';
        resultDownloadBtn.style.opacity = '0.55';
      }
    }

    function syncResultView() {
      const item = state.lastResult;
      if (!item) {
        return;
      }
      syncResultVersionControls();
      resultStageNote.textContent = generationStageNote(item, state.resultViewMode);
      renderMarkdownWithLineNumbers(resultMarkdown, markdownForMode(item, state.resultViewMode) || '');
      syncResultDownload();
    }

    function renderResult(result) {
      state.lastResult = result;
      state.resultViewMode = preferredViewMode(result);
      const request = result.request || collectPayload();
      resultTitle.textContent = result.title || '最新生成结果';
      resultSummary.textContent = result.summary || result.task_excerpt || '文档已生成，可复制或下载。';
      resultMeta.innerHTML = [
        `<div class="chip alt">${escapeHtml(templateLabel(result.template_type || request.template_type))}</div>`,
        `<div class="chip">${escapeHtml(request.industry || '未指定行业')}</div>`,
        `<div class="chip">${escapeHtml(labelFor('outputLanguage', request.output_language))}</div>`,
        `<div class="chip">${escapeHtml(environmentDisplayValue(request.environment))}</div>`,
        `<div class="chip">${escapeHtml(formatTimestamp(result.created_at || ''))}</div>`,
        `<div class="chip">${escapeHtml(generationStatusLabel(result.finalization_status))}</div>`
      ].join('');
      resultStageSummary.innerHTML = [
        ['当前状态', generationStatusLabel(result.finalization_status)],
        ['主展示版本', result.final_markdown ? '最终稿' : '草稿'],
        ['模型优化', result.used_model_optimization ? '已启用' : '未启用'],
        ['模型来源', modelRuntimeDescription(result.model_runtime || {})],
        ['状态说明', result.finalization_error || (result.final_markdown ? '第二阶段优化完成。' : '当前仅保留草稿结果。')]
      ].map(([label, value]) => `
        <div class="detail-item">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `).join('');
      resultQuestions.innerHTML = (result.open_questions || []).length
        ? result.open_questions.map(item => `<li>${escapeHtml(item)}</li>`).join('')
        : '<li>当前没有明显缺失项。</li>';
      renderReferenceList(resultReferences, result.reference_files || []);
      resultPlanCard.style.display = 'block';
      resultPlanSummary.textContent = result.plan_markdown
        ? '当前展示的是生成前自动整理的 PLAN.md，可用来校对问答收集与执行计划。'
        : '该结果没有附带 PLAN.md。';
      renderMarkdownWithLineNumbers(resultPlanMarkdown, result.plan_markdown || '该结果没有附带 PLAN.md。');
      syncResultView();
    }

    function questionHasValue(value) {
      if (Array.isArray(value)) {
        return value.some(item => String(item || '').trim());
      }
      return !!String(value || '').trim();
    }

    function questionSuggestions(question) {
      return Array.isArray(question && question.suggestions)
        ? question.suggestions.map(item => String(item || '').trim()).filter(Boolean)
        : [];
    }

    function suggestionBulletText(question) {
      return questionSuggestions(question).map(item => `- ${item}`).join('\\n');
    }

    function splitBulletText(value) {
      const text = String(value || '').trim();
      if (!text) {
        return [];
      }
      return text
        .split('\\n')
        .map(item => item.trim().replace(/^[-*]\s*/, ''))
        .filter(Boolean);
    }

    function mergeSuggestionText(existingValue, suggestions) {
      const seen = new Set();
      const merged = [];
      [...splitBulletText(existingValue), ...(suggestions || [])].forEach(item => {
        const text = String(item || '').trim();
        const key = text.toLowerCase();
        if (!text || seen.has(key)) {
          return;
        }
        seen.add(key);
        merged.push(text);
      });
      return merged.map(item => `- ${item}`).join('\\n');
    }

    function applyQuestionSuggestions(questionId, mode = 'replace') {
      const question = questionById(questionId);
      const suggestions = questionSuggestions(question);
      if (!question || !suggestions.length) {
        return;
      }
      const currentValue = String(state.intakeAnswers[questionId] || '');
      const nextValue = mode === 'append'
        ? mergeSuggestionText(currentValue, suggestions)
        : suggestionBulletText(question);
      setQuestionValue(questionId, nextValue);
      renderQuestionnaire();
      setStatus(
        mode === 'append'
          ? `已将建议追加到“${question.title || questionId}”，你可以继续微调。`
          : `已将建议填入“${question.title || questionId}”，你可以继续微调。`
      );
    }

    function questionOptionMap(question) {
      return new Map(((question && question.options) || []).map(option => [String(option.value), option]));
    }

    function questionOptionValues(question) {
      return new Set(((question && question.options) || []).map(option => String(option.value)));
    }

    function questionValueLabel(question, value) {
      const normalized = String(value || '').trim();
      if (!normalized) {
        return '';
      }
      const match = questionOptionMap(question).get(normalized);
      return match && match.label ? match.label : normalized;
    }

    function questionIsIgnored(questionId) {
      return !!state.ignoredQuestions[String(questionId || '')];
    }

    function ignoreQuestion(questionId) {
      const question = questionById(questionId);
      if (!question || question.required) {
        return;
      }
      clearQuestionDraft(questionId);
      setQuestionValue(questionId, question.kind === 'multi_choice' ? [] : '');
      state.ignoredQuestions = {
        ...state.ignoredQuestions,
        [questionId]: true
      };
      renderQuestionnaire();
      setStatus(`已忽略“${question.title || questionId}”，你可以稍后恢复继续填写。`);
    }

    function restoreQuestion(questionId) {
      if (!questionIsIgnored(questionId)) {
        return;
      }
      const next = { ...state.ignoredQuestions };
      delete next[questionId];
      state.ignoredQuestions = next;
      renderQuestionnaire();
      window.setTimeout(() => focusQuestion(questionId), 120);
      const question = questionById(questionId);
      if (question) {
        setStatus(`已恢复“${question.title || questionId}”，可以继续补充。`);
      }
    }

    function setQuestionDraft(questionId, value) {
      const normalizedId = String(questionId || '');
      state.questionDrafts = {
        ...state.questionDrafts,
        [normalizedId]: String(value || '')
      };
    }

    function clearQuestionDraft(questionId) {
      const normalizedId = String(questionId || '');
      if (!(normalizedId in state.questionDrafts)) {
        return;
      }
      const next = { ...state.questionDrafts };
      delete next[normalizedId];
      state.questionDrafts = next;
    }

    function addCustomQuestionValue(questionId) {
      const question = questionById(questionId);
      if (!question || question.kind !== 'multi_choice') {
        return;
      }
      const draft = String(state.questionDrafts[questionId] || '').trim();
      if (!draft) {
        return;
      }
      const current = Array.isArray(state.intakeAnswers[questionId]) ? [...state.intakeAnswers[questionId]] : [];
      const exists = current.some(item => String(item || '').trim().toLowerCase() === draft.toLowerCase());
      if (!exists) {
        setQuestionValue(questionId, [...current, draft]);
      }
      clearQuestionDraft(questionId);
      renderQuestionnaire();
    }

    function questionById(questionId) {
      const session = state.intakeSession;
      const questions = session && Array.isArray(session.questions) ? session.questions : [];
      return questions.find(item => item.question_id === questionId) || null;
    }

    function questionIsActive(question, answers) {
      const dependsOn = question && question.depends_on ? question.depends_on : {};
      const entries = Object.entries(dependsOn);
      if (!entries.length) {
        return true;
      }
      return entries.every(([key, values]) => {
        const allowed = new Set((values || []).map(item => String(item)));
        const current = answers ? answers[key] : '';
        if (Array.isArray(current)) {
          return current.some(item => allowed.has(String(item)));
        }
        return allowed.has(String(current || ''));
      });
    }

    function activeQuestions() {
      const session = state.intakeSession;
      const questions = session && Array.isArray(session.questions) ? session.questions : [];
      return questions.filter(question => questionIsActive(question, state.intakeAnswers || {}));
    }

    function normalizeQuestionValue(question, rawValue) {
      if (question && question.kind === 'multi_choice') {
        const source = Array.isArray(rawValue) ? rawValue : [];
        const values = [];
        const seen = new Set();
        source.forEach(item => {
          const text = String(item || '').trim();
          const key = text.toLowerCase();
          if (!text || seen.has(key)) {
            return;
          }
          seen.add(key);
          values.push(text);
        });
        return values;
      }
      return String(rawValue || '');
    }

    function setQuestionValue(questionId, rawValue) {
      const question = questionById(questionId);
      if (!question) {
        return;
      }
      if (questionIsIgnored(questionId)) {
        const nextIgnored = { ...state.ignoredQuestions };
        delete nextIgnored[questionId];
        state.ignoredQuestions = nextIgnored;
      }
      state.intakeAnswers = {
        ...state.intakeAnswers,
        [questionId]: normalizeQuestionValue(question, rawValue)
      };
      if (state.intakeSession && state.intakeSession.validation_errors) {
        delete state.intakeSession.validation_errors[questionId];
      }
      if (state.intakeSession && Array.isArray(state.intakeSession.missing_required_ids)) {
        state.intakeSession.missing_required_ids = state.intakeSession.missing_required_ids.filter(item => item !== questionId);
      }
    }

    function toggleQuestionOption(questionId, value) {
      const current = Array.isArray(state.intakeAnswers[questionId]) ? [...state.intakeAnswers[questionId]] : [];
      const normalized = String(value || '').trim();
      const exists = current.some(item => String(item).toLowerCase() === normalized.toLowerCase());
      setQuestionValue(questionId, exists ? current.filter(item => String(item).toLowerCase() !== normalized.toLowerCase()) : [...current, normalized]);
    }

    function deferQuestion(questionId) {
      const question = questionById(questionId);
      if (!question) {
        return;
      }
      const value = question.kind === 'multi_choice'
        ? [deferredPlaceholder(question)]
        : deferredPlaceholder(question);
      setQuestionValue(questionId, value);
      renderQuestionnaire();
      setStatus(`已将“${question.title || questionId}”标记为稍后补充，计划稿中会保留待确认项。`);
    }

    function clearQuestion(questionId) {
      ignoreQuestion(questionId);
    }

    function focusQuestion(questionId) {
      const normalizedId = String(questionId || '');
      const element = questionnaireList.querySelector(`[data-question-card="${normalizedId}"]`);
      if (!element) {
        return;
      }
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const focusTarget = element.querySelector('textarea, input, select, button');
      if (focusTarget && typeof focusTarget.focus === 'function') {
        window.setTimeout(() => focusTarget.focus({ preventScroll: true }), 180);
      }
    }

    function firstQuestionIssueId() {
      const session = state.intakeSession;
      if (!session) {
        return '';
      }
      const activeIds = activeQuestions().map(item => item.question_id);
      const errors = session.validation_errors || {};
      for (const questionId of activeIds) {
        if (errors[questionId]) {
          return questionId;
        }
      }
      const missing = Array.isArray(session.missing_required_ids) ? session.missing_required_ids : [];
      for (const questionId of activeIds) {
        if (missing.includes(questionId)) {
          return questionId;
        }
      }
      return '';
    }

    function renderQuestionnaire() {
      const session = state.intakeSession;
      if (!session) {
        questionSummaryPills.innerHTML = '';
        questionnaireList.innerHTML = '<div class="empty-state">完成前 3 步后，点击“开始问答”，这里会出现补充问题。</div>';
        return;
      }
      const questions = activeQuestions();
      const validationErrors = session.validation_errors || {};
      const baseRequest = session.base_request || {};
      const generationMode = String(session.question_generation_mode || 'rule');
      const generationModeLabel = generationMode === 'rule_plus_model' ? '规则 + 模型优化' : '规则生成';
      let answeredCount = 0;
      let missingRequired = 0;
      let deferredCount = 0;
      let ignoredCount = 0;
      questions.forEach(question => {
        const hasValue = questionHasValue(state.intakeAnswers[question.question_id]);
        const hasError = !!validationErrors[question.question_id];
        const deferred = isDeferredAnswer(state.intakeAnswers[question.question_id]);
        const ignored = questionIsIgnored(question.question_id);
        if (hasValue && !hasError) {
          answeredCount += 1;
        } else if (question.required) {
          missingRequired += 1;
        }
        if (deferred) {
          deferredCount += 1;
        }
        if (ignored) {
          ignoredCount += 1;
        }
      });
      questionSummaryPills.innerHTML = [
        `<div class="pill"><strong>已读取</strong> 前 3 步基础输入</div>`,
        `<div class="pill"><strong>${escapeHtml(generationModeLabel)}</strong> 问答生成</div>`,
        `<div class="pill"><strong>${escapeHtml(templateLabel(baseRequest.template_type || 'custom'))}</strong> 模板</div>`,
        `<div class="pill"><strong>${escapeHtml(environmentDisplayValue(baseRequest.environment || ''))}</strong> 环境</div>`,
        `<div class="pill"><strong>${escapeHtml(String(questions.length))}</strong> 个当前问题</div>`,
        `<div class="pill"><strong>${escapeHtml(String(answeredCount))}</strong> 个已完成</div>`,
        `<div class="pill"><strong>${escapeHtml(String(missingRequired))}</strong> 个必填待补</div>`,
        `<div class="pill"><strong>${escapeHtml(String(deferredCount))}</strong> 个稍后补充</div>`,
        `<div class="pill"><strong>${escapeHtml(String(ignoredCount))}</strong> 个已忽略</div>`,
        `<div class="pill"><strong>${escapeHtml(String(session.completion_percent || 0))}%</strong> 当前完成度</div>`
      ].join('');
      if (!questions.length) {
        questionnaireList.innerHTML = '<div class="empty-state">当前没有额外问题。继续下一步即可查看 PLAN.md。</div>';
        return;
      }
      questionnaireList.innerHTML = `${session.question_generation_note ? `
        <div class="question-mode-note">
          <strong>当前问答来源</strong>
          <p>${escapeHtml(session.question_generation_note)}</p>
        </div>
      ` : ''}` + questions.map(question => {
        const value = state.intakeAnswers[question.question_id];
        const error = validationErrors[question.question_id] || '';
        const helpText = question.help_text || '';
        const kind = question.kind || 'free_text';
        const deferred = isDeferredAnswer(value);
        const ignored = questionIsIgnored(question.question_id);
        const invalid = !ignored && (!!error || (question.required && !questionHasValue(value)));
        const optionValues = questionOptionValues(question);
        const suggestions = questionSuggestions(question);
        const suggestionMarkup = suggestions.length ? `
          <div class="question-suggestion-card">
            <strong>系统已生成建议，可直接修改</strong>
            <p>建议先自动生成，再允许手工微调；如果模型可用，也会对建议和问法再优化一轮。</p>
            <ul class="question-suggestion-list">
              ${suggestions.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
            <div class="question-suggestion-actions">
              <button type="button" class="button-secondary" data-question-apply-suggestions="${escapeHtml(question.question_id)}" ${ignored ? 'disabled' : ''}>应用建议</button>
              <button type="button" class="button-quiet" data-question-append-suggestions="${escapeHtml(question.question_id)}" ${ignored ? 'disabled' : ''}>追加到当前内容</button>
            </div>
          </div>
        ` : '';
        let controlMarkup = '';
        if (kind === 'single_choice') {
          const normalizedValue = String(value || '').trim();
          const hasCustomDraft = Object.prototype.hasOwnProperty.call(state.questionDrafts, question.question_id);
          const customDraftValue = hasCustomDraft ? String(state.questionDrafts[question.question_id] || '') : '';
          const usingCustomValue = !!normalizedValue && !optionValues.has(normalizedValue);
          const usingCustomMode = usingCustomValue || hasCustomDraft;
          const selectValue = usingCustomMode ? CUSTOM_OPTION_VALUE : normalizedValue;
          controlMarkup = `
            <div class="question-custom-entry">
              <select class="question-select" data-question-select="${escapeHtml(question.question_id)}" ${ignored ? 'disabled' : ''}>
                <option value="">请选择</option>
                ${(question.options || []).map(option => `
                  <option value="${escapeHtml(option.value)}" ${selectValue === String(option.value) ? 'selected' : ''}>${escapeHtml(option.label)}</option>
                `).join('')}
                <option value="${CUSTOM_OPTION_VALUE}" ${selectValue === CUSTOM_OPTION_VALUE ? 'selected' : ''}>不在选项中，手动输入</option>
              </select>
              <div class="question-custom-entry" ${usingCustomMode ? '' : 'hidden'}>
                <input
                  type="text"
                  class="question-input"
                  data-question-custom-text="${escapeHtml(question.question_id)}"
                  placeholder="如果现有选项不合适，请直接输入"
                  value="${escapeHtml(usingCustomValue ? normalizedValue : customDraftValue)}"
                  ${ignored ? 'disabled' : ''}
                >
              </div>
            </div>
          `;
        } else if (kind === 'multi_choice') {
          const selected = Array.isArray(value) ? value : [];
          const selectedLookup = new Set(selected.map(item => String(item).toLowerCase()));
          const draftValue = String(state.questionDrafts[question.question_id] || '');
          controlMarkup = `
            <div class="question-options">
              ${(question.options || []).map(option => `
                <button
                  type="button"
                  class="question-option ${selectedLookup.has(String(option.value).toLowerCase()) ? 'active' : ''}"
                  data-question-toggle="${escapeHtml(question.question_id)}"
                  data-option-value="${escapeHtml(option.value)}"
                  ${ignored ? 'disabled' : ''}
                >
                  <strong>${escapeHtml(option.label)}</strong>
                  ${option.description ? `<small>${escapeHtml(option.description)}</small>` : ''}
                </button>
              `).join('')}
            </div>
            <div class="question-custom-entry inline">
              <input
                type="text"
                class="question-input"
                data-question-custom-entry="${escapeHtml(question.question_id)}"
                placeholder="选项里没有时，在这里补充自定义值"
                value="${escapeHtml(draftValue)}"
                ${ignored ? 'disabled' : ''}
              >
              <button
                type="button"
                class="button-secondary"
                data-question-custom-add="${escapeHtml(question.question_id)}"
                ${ignored ? 'disabled' : ''}
              >添加</button>
            </div>
            <div class="selected-list">
              ${selected.length
                ? selected.map(item => `
                  <div class="selected-tag">
                    ${escapeHtml(questionValueLabel(question, item))}
                    <button type="button" data-question-remove="${escapeHtml(question.question_id)}" data-option-value="${escapeHtml(item)}" ${ignored ? 'disabled' : ''}>×</button>
                  </div>
                `).join('')
                : '<span class="panel-text">暂未选择</span>'}
            </div>
          `;
        } else {
          controlMarkup = `
            <textarea
              data-question-text="${escapeHtml(question.question_id)}"
              placeholder="${escapeHtml(question.placeholder || '')}"
              ${ignored ? 'disabled' : ''}
            >${escapeHtml(String(value || ''))}</textarea>
          `;
        }
        return `
          <article class="question-card ${invalid ? 'invalid' : ''} ${ignored ? 'ignored' : ''}" data-question-card="${escapeHtml(question.question_id)}">
            <div class="question-head">
              <div>
                <div class="question-kicker">${escapeHtml(question.source_rule || 'Task Intake')}</div>
                <h4>${escapeHtml(question.title || question.question_id)}</h4>
                <p class="question-description">${escapeHtml(question.prompt || '')}</p>
              </div>
              <span class="question-badge ${question.required ? '' : 'optional'}">${question.required ? '必填' : '选填'}</span>
            </div>
            ${suggestionMarkup}
            ${controlMarkup}
            <div class="question-inline-actions">
              ${ignored
                ? `<button type="button" class="button-secondary" data-question-restore="${escapeHtml(question.question_id)}">恢复此项</button>`
                : `
                  <button type="button" class="button-link" data-question-defer="${escapeHtml(question.question_id)}">稍后补充</button>
                  ${!question.required ? `<button type="button" class="button-quiet" data-question-clear="${escapeHtml(question.question_id)}">忽略此项</button>` : ''}
                `}
            </div>
            ${ignored ? `<p class="field-help">当前已忽略，生成时不会把这一项当作已填写内容，你可以随时恢复。</p>` : ''}
            ${deferred ? `<p class="field-help">当前已标记为“稍后补充”，本次会继续生成，并在计划稿中保留待确认项。</p>` : ''}
            ${helpText ? `<p class="field-help">${escapeHtml(helpText)}</p>` : ''}
            ${error ? `<p class="field-help question-error">${escapeHtml(error)}</p>` : ''}
          </article>
        `;
      }).join('');
      Array.from(questionnaireList.querySelectorAll('[data-question-text]')).forEach(element => {
        element.addEventListener('input', () => {
          setQuestionValue(element.getAttribute('data-question-text'), element.value);
        });
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-select]')).forEach(element => {
        element.addEventListener('change', () => {
          const questionId = element.getAttribute('data-question-select');
          const question = questionById(questionId);
          if (!question) {
            return;
          }
          if (element.value === CUSTOM_OPTION_VALUE) {
            const currentValue = String(state.intakeAnswers[questionId] || '').trim();
            setQuestionDraft(questionId, questionOptionValues(question).has(currentValue) ? '' : currentValue);
            setQuestionValue(questionId, questionOptionValues(question).has(currentValue) ? '' : currentValue);
          } else {
            clearQuestionDraft(questionId);
            setQuestionValue(questionId, element.value);
          }
          renderQuestionnaire();
          if (element.value === CUSTOM_OPTION_VALUE) {
            const customInput = questionnaireList.querySelector(`[data-question-custom-text="${CSS.escape(questionId)}"]`);
            if (customInput && typeof customInput.focus === 'function') {
              window.setTimeout(() => customInput.focus(), 60);
            }
          }
        });
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-custom-text]')).forEach(element => {
        element.addEventListener('input', () => {
          const questionId = element.getAttribute('data-question-custom-text');
          setQuestionDraft(questionId, element.value);
          setQuestionValue(questionId, element.value);
        });
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-toggle]')).forEach(element => {
        element.addEventListener('click', () => {
          toggleQuestionOption(element.getAttribute('data-question-toggle'), element.getAttribute('data-option-value'));
          renderQuestionnaire();
        });
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-custom-entry]')).forEach(element => {
        element.addEventListener('input', () => {
          setQuestionDraft(element.getAttribute('data-question-custom-entry'), element.value);
        });
        element.addEventListener('keydown', event => {
          if (event.key === 'Enter') {
            event.preventDefault();
            addCustomQuestionValue(element.getAttribute('data-question-custom-entry'));
          }
        });
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-custom-add]')).forEach(element => {
        element.addEventListener('click', () => addCustomQuestionValue(element.getAttribute('data-question-custom-add')));
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-apply-suggestions]')).forEach(element => {
        element.addEventListener('click', () => applyQuestionSuggestions(element.getAttribute('data-question-apply-suggestions'), 'replace'));
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-append-suggestions]')).forEach(element => {
        element.addEventListener('click', () => applyQuestionSuggestions(element.getAttribute('data-question-append-suggestions'), 'append'));
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-remove]')).forEach(element => {
        element.addEventListener('click', () => {
          const questionId = element.getAttribute('data-question-remove');
          const valueToRemove = String(element.getAttribute('data-option-value') || '');
          const current = Array.isArray(state.intakeAnswers[questionId]) ? state.intakeAnswers[questionId] : [];
          setQuestionValue(questionId, current.filter(item => String(item || '').toLowerCase() !== valueToRemove.toLowerCase()));
          renderQuestionnaire();
        });
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-defer]')).forEach(element => {
        element.addEventListener('click', () => deferQuestion(element.getAttribute('data-question-defer')));
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-clear]')).forEach(element => {
        element.addEventListener('click', () => clearQuestion(element.getAttribute('data-question-clear')));
      });
      Array.from(questionnaireList.querySelectorAll('[data-question-restore]')).forEach(element => {
        element.addEventListener('click', () => restoreQuestion(element.getAttribute('data-question-restore')));
      });
    }

    function maybeScheduleAutoGenerate() {
      clearPlanAutoTimer();
      const session = state.intakeSession;
      if (
        state.currentStep !== 4
        || !session
        || !session.ready_for_plan
        || !session.session_id
        || state.generationPending
        || state.generatedSessionId === session.session_id
      ) {
        return;
      }
      planAutoNote.textContent = 'PLAN.md 已就绪，系统会自动继续生成 AGENTS.md；如需立即开始，也可以直接点击按钮。';
      state.planAutoTimer = window.setTimeout(() => {
        state.planAutoTimer = 0;
        void generateFromCurrentSession();
      }, 1500);
    }

    function renderPlanPreview() {
      const session = state.intakeSession;
      if (!session || !session.ready_for_plan || !session.plan_markdown) {
        planSummaryPills.innerHTML = '';
        planAutoNote.textContent = '完成问答并通过校验后，这里会展示 PLAN.md 预览，并自动继续生成 AGENTS.md。';
        renderMarkdownWithLineNumbers(planMarkdown, 'PLAN.md 尚未准备好。完成问答后，这里会显示计划预览。');
        return;
      }
      planSummaryPills.innerHTML = [
        ...(session.plan_summary || []).map(item => `<div class="pill">${escapeHtml(item)}</div>`),
        ...(session.plan_output_path ? [`<div class="pill"><strong>${escapeHtml(session.plan_output_path)}</strong> 计划文件</div>`] : [])
      ].join('');
      renderMarkdownWithLineNumbers(planMarkdown, session.plan_markdown);
      planAutoNote.textContent = state.generationPending
        ? '正在基于当前 PLAN.md 生成 AGENTS.md，请稍候。'
        : '当前 PLAN.md 已生成完成，系统会继续进入 AGENTS.md 生成。';
      maybeScheduleAutoGenerate();
    }

    async function startIntakeFlow() {
      const payload = collectPayload();
      if (!payload.industry || !payload.task_description) {
        setStatus('请先填写行业和任务描述。', true);
        showScreen('workspace');
        showStep(0);
        return;
      }
      const signature = basePayloadSignature(payload);
      if (state.intakeSession && state.intakeBaseSignature === signature) {
        setStatus('已加载当前任务的补充问答，请继续完成。');
        showStep(3);
        renderQuestionnaire();
        return;
      }
      const originalLabel = generateBtn.textContent;
      generateBtn.disabled = true;
      generateBtn.textContent = '准备中…';
      setStatus('正在根据基础信息整理补充问答…');
      try {
        const response = await fetch('/intake/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok || data.status !== 'ok') {
          throw new Error(data.message || '初始化问答失败');
        }
        state.intakeSession = data.result || {};
        state.intakeAnswers = { ...(state.intakeSession.answers || {}) };
        state.intakeBaseSignature = signature;
        state.generatedSessionId = '';
        renderQuestionnaire();
        renderPlanPreview();
        setStatus('问答已就绪。前面已填写的任务描述、环境和偏好已读入当前问答，可直接补充剩余信息。');
        showStep(3);
      } catch (error) {
        setStatus(error.message || String(error), true);
      } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = originalLabel;
        syncStepActions();
      }
    }

    async function submitQuestionnaire() {
      const session = state.intakeSession;
      if (!session || !session.session_id) {
        setStatus('请先完成基础信息并启动问答。', true);
        showStep(2);
        return;
      }
      const originalLabel = generateBtn.textContent;
      generateBtn.disabled = true;
      generateBtn.textContent = '校验中…';
      setStatus('正在校验补充问答并生成 PLAN.md…');
      try {
        const response = await fetch('/intake/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: session.session_id,
            answers: state.intakeAnswers
          })
        });
        const data = await response.json();
        if (!response.ok || data.status !== 'ok') {
          throw new Error(data.message || '提交问答失败');
        }
        state.intakeSession = data.result || {};
        state.intakeAnswers = { ...state.intakeAnswers, ...(state.intakeSession.answers || {}) };
        renderQuestionnaire();
        renderPlanPreview();
        if (state.intakeSession.ready_for_plan) {
          setStatus('PLAN.md 已准备好，正在进入预览。');
          showStep(4);
        } else {
          setStatus('还有必填项未完成，请继续补充。', true);
          showStep(3);
          const questionId = firstQuestionIssueId();
          if (questionId) {
            window.setTimeout(() => focusQuestion(questionId), 160);
          }
        }
      } catch (error) {
        setStatus(error.message || String(error), true);
      } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = originalLabel;
        syncStepActions();
      }
    }

    async function generateFromCurrentSession() {
      const session = state.intakeSession;
      if (!session || !session.session_id) {
        setStatus('请先完成问答并生成 PLAN.md。', true);
        showStep(3);
        return;
      }
      if (!session.ready_for_plan) {
        setStatus('当前问答尚未满足生成条件，请先补齐必填项。', true);
        showStep(3);
        return;
      }
      if (state.generationPending) {
        return;
      }
      clearPlanAutoTimer();
      const requestId = `req_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
      state.generationPending = true;
      syncStepActions();
      setStatus('正在基于 PLAN.md 生成 AGENTS.md，请稍候...');
      startProgressTracking(requestId);
      renderPlanPreview();
      try {
        const response = await fetch('/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: session.session_id,
            request_id: requestId
          })
        });
        const data = await response.json();
        if (!response.ok || data.status !== 'ok') {
          throw new Error(data.message || '生成失败');
        }
        finishProgress('ok', '生成完成，结果已写入案例库。');
        state.generatedSessionId = session.session_id;
        renderResult(data.result || {});
        await refreshOverview();
        await refreshLibrary();
        setStatus('生成完成，结果已写入案例库。');
        showScreen('result');
      } catch (error) {
        finishProgress('error', error.message || String(error));
        setStatus(error.message || String(error), true);
      } finally {
        state.generationPending = false;
        syncStepActions();
        renderPlanPreview();
      }
    }

    async function handleGenerate() {
      if (state.currentStep === 2) {
        await startIntakeFlow();
        return;
      }
      if (state.currentStep === 3) {
        await submitQuestionnaire();
        return;
      }
      if (state.currentStep === 4) {
        await generateFromCurrentSession();
      }
    }

    async function copyText(value, successText) {
      const text = String(value || '').trim();
      if (!text) {
        setStatus('当前没有可复制的内容。', true);
        return;
      }
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          const textarea = document.createElement('textarea');
          textarea.value = text;
          textarea.setAttribute('readonly', 'readonly');
          textarea.style.position = 'fixed';
          textarea.style.opacity = '0';
          document.body.appendChild(textarea);
          textarea.focus();
          textarea.select();
          document.execCommand('copy');
          textarea.remove();
        }
        setStatus(successText);
      } catch (error) {
        setStatus(error.message || '复制失败', true);
      }
    }

    function syncSidebarState() {
      const collapsed = appShell.classList.contains('sidebar-collapsed');
      const mobile = window.innerWidth <= 960;
      sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
      sidebarToggle.setAttribute('aria-label', collapsed ? '展开侧边栏' : '收起侧边栏');
      sidebarToggle.innerHTML = collapsed
        ? '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2.5"></rect><path d="M9 4.5v15"></path><path d="m14.5 9 3 3"></path><path d="m14.5 15 3-3"></path></svg>'
        : '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2.5"></rect><path d="M9 4.5v15"></path><path d="m14.5 12 3-3"></path><path d="m14.5 12 3 3"></path></svg>';
      topbarNavBtn.setAttribute('aria-expanded', String(mobile && !collapsed));
      topbarNavBtn.setAttribute('aria-label', mobile && !collapsed ? '收起导航' : '展开导航');
      topbarNavBtn.innerHTML = mobile && !collapsed
        ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12"></path><path d="M18 6 6 18"></path></svg>'
        : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16"></path><path d="M4 12h16"></path><path d="M4 18h16"></path></svg>';
      if (!libraryDrawer.classList.contains('open') && !state.modelModalOpen) {
        document.body.style.overflow = mobile && !collapsed ? 'hidden' : '';
      }
    }

    function toggleSidebar() {
      const collapsed = appShell.classList.toggle('sidebar-collapsed');
      if (window.innerWidth > 960) {
        window.localStorage.setItem('agents_sidebar_collapsed', collapsed ? '1' : '0');
      }
      syncSidebarState();
    }

    function restoreSidebarState() {
      if (window.innerWidth <= 960) {
        appShell.classList.add('sidebar-collapsed');
      } else {
        const saved = window.localStorage.getItem('agents_sidebar_collapsed');
        appShell.classList.toggle('sidebar-collapsed', saved === '1');
      }
      syncSidebarState();
    }

    function handleResize() {
      restoreSidebarState();
    }

    try {
      fillSelect('template_select', OPTIONS.template, LABELS.template);
      fillSelect('industry_select', OPTIONS.industry, LABELS.industry);
      fillSelect('target_user_select', OPTIONS.targetUser, LABELS.targetUser);
      fillSelect('output_language_select', OPTIONS.outputLanguage, LABELS.outputLanguage);
      fillSelect('risk_tolerance_select', OPTIONS.riskTolerance, LABELS.riskTolerance);
      fillSelect('model_mode_select', OPTIONS.modelMode, LABELS.modelMode);
      fillSelect('model_provider_select', OPTIONS.modelProvider, LABELS.modelProvider);
      fillSelect('model_wire_api_select', OPTIONS.modelWireApi, LABELS.modelWireApi);
      fillSelect('library-industry-filter', ['all'], { all: '全部行业' });
      fillSelect('library-template-filter', ['all'], { all: '全部模板' });
      fillSelect('library-language-filter', ['all'], { all: '全部语言' });

      bindOtherInput('template_select', 'template_other');
      bindOtherInput('industry_select', 'industry_other');
      bindOtherInput('target_user_select', 'target_user_other');
      bindOtherInput('output_language_select', 'output_language_other');
      bindOtherInput('risk_tolerance_select', 'risk_tolerance_other');
      bindOtherInput('model_provider_select', 'model_provider_other');

      document.getElementById('template_select').value = 'http_service';
      document.getElementById('industry_select').value = 'devtools';
      document.getElementById('target_user_select').value = 'general';
      document.getElementById('output_language_select').value = 'zh';
      document.getElementById('risk_tolerance_select').value = 'medium';
      document.getElementById('model_mode_select').value = 'default';
      document.getElementById('model_provider_select').value = 'openai';
      document.getElementById('model_wire_api_select').value = 'chat_completions';

      renderOptionGroup('environment');
      renderOptionGroup('stack');
      renderOptionGroup('constraint');
      renderTemplateCard();
      applyTemplateDefaults(false);
      renderDraftSummary();
      renderMenu();
      renderStepList();
      renderOverview();
      renderLibrary();
      showStep(0);
      showScreen('workspace');
      restoreSidebarState();

      addEnvironmentBtn.addEventListener('click', () => addCustomValue('environment'));
      addStackBtn.addEventListener('click', () => addCustomValue('stack'));
      addConstraintBtn.addEventListener('click', () => addCustomValue('constraint'));
      applyTemplateBtn.addEventListener('click', () => {
        const hadIntakeSession = !!state.intakeSession;
        const changes = applyTemplateDefaults(true);
        const resetNote = hadIntakeSession && !state.intakeSession ? '基础信息发生变化，后续问答与 PLAN.md 已清空，需要重新开始问答。' : '';
        if (!changes.length) {
          setStatus(`当前字段已与模板建议一致，没有新的变更可应用。${resetNote ? ` ${resetNote}` : ''}`.trim());
          return;
        }
        const details = changes.map(item => `${item.label} -> ${item.after}`).join('；');
        setStatus(`已应用模板建议：${details}。${resetNote || '你可以继续微调后再生成。'}`);
      });
      prevStepBtn.addEventListener('click', () => showStep(state.currentStep - 1));
      nextStepBtn.addEventListener('click', () => {
        if (!validateCurrentStep()) return;
        showStep(state.currentStep + 1);
      });
      generateBtn.addEventListener('click', handleGenerate);
      openLibraryBtn.addEventListener('click', () => showScreen('library'));
      jumpResultBtn.addEventListener('click', () => showScreen('result'));
      resultBackBtn.addEventListener('click', () => showScreen('workspace'));
      resultCopyBtn.addEventListener('click', () => copyText(markdownForMode(state.lastResult, state.resultViewMode), 'AGENTS.md 内容已复制。'));
      drawerCopyBtn.addEventListener('click', () => copyText(markdownForMode(state.drawerItem, state.drawerViewMode), '案例文档已复制。'));
      drawerReuseBtn.addEventListener('click', () => applyRequestToForm(state.drawerItem && state.drawerItem.request));
      drawerCloseBtn.addEventListener('click', closeDrawer);
      drawerBackdrop.addEventListener('click', closeDrawer);
      resultViewFinalBtn.addEventListener('click', () => {
        state.resultViewMode = 'final';
        syncResultView();
      });
      resultViewDraftBtn.addEventListener('click', () => {
        state.resultViewMode = 'draft';
        syncResultView();
      });
      drawerViewFinalBtn.addEventListener('click', () => {
        state.drawerViewMode = 'final';
        syncDrawerView();
      });
      drawerViewDraftBtn.addEventListener('click', () => {
        state.drawerViewMode = 'draft';
        syncDrawerView();
      });
      modelModalBackdrop.addEventListener('click', closeModelModal);
      modelModalCloseBtn.addEventListener('click', closeModelModal);
      modelEnableBtn.addEventListener('click', () => {
        setModelMode(modelHasUsableSystemDefault() ? 'default' : 'custom', { clearValidation: true });
        if (!modelHasUsableSystemDefault()) {
          setModelSettingsStatus('已切换到开启状态，但当前未检测到系统默认模型，请继续补充自定义模型接口。');
        } else {
          setModelSettingsStatus('已切换到开启状态。点击“应用当前设置”后会正式启用模型优化。');
        }
      });
      modelDisableBtn.addEventListener('click', () => {
        setModelMode('disabled', { clearValidation: true });
        setModelSettingsStatus('已切换为关闭状态。点击“应用当前设置”后会正式禁用模型优化。');
      });
      Array.from(modelSourceSwitch.querySelectorAll('[data-model-source]')).forEach(button => {
        button.addEventListener('click', () => {
          const source = button.getAttribute('data-model-source');
          if (source === 'default') {
            if (!modelHasUsableSystemDefault()) {
              setModelSettingsStatus('当前没有可用的系统默认模型，请改用自定义模型接口。', true);
              return;
            }
            setModelMode('default', { clearValidation: true });
          } else {
            setModelMode('custom', { clearValidation: true });
          }
        });
      });
      document.getElementById('model_mode_select').addEventListener('change', () => {
        clearModelValidationState();
        renderModelValidationSummary();
        updateModelConfigVisibility();
      });
      document.getElementById('model_provider_select').addEventListener('change', () => {
        clearModelValidationState();
        renderModelValidationSummary();
        updateModelConfigVisibility();
      });
      document.getElementById('model_wire_api_select').addEventListener('change', () => {
        clearModelValidationState();
        renderModelValidationSummary();
        updateModelConfigVisibility();
      });
      ['model_provider_other', 'model_base_url', 'model_name', 'model_api_key']
        .forEach(id => {
          document.getElementById(id).addEventListener('input', () => {
            clearModelValidationState();
            renderModelValidationSummary();
            updateModelConfigVisibility();
          });
        });
      modelAdminTokenInput.addEventListener('input', syncModelActionButtons);
      modelTokenVisibilityBtn.addEventListener('click', () => {
        modelAdminTokenInput.type = modelAdminTokenInput.type === 'password' ? 'text' : 'password';
        syncModelTokenVisibilityButton();
        modelAdminTokenInput.focus();
      });
      modelValidateBtn.addEventListener('click', () => {
        void validateDefaultModelSettings();
      });
      modelSaveBtn.addEventListener('click', () => {
        void saveDefaultModelSettings();
      });
      modelRefreshBtn.addEventListener('click', () => {
        void refreshModelSettings().catch(error => {
          setModelSettingsStatus(error.message || '读取模型配置失败', true);
        });
      });
      sidebarBackdrop.addEventListener('click', () => {
        appShell.classList.add('sidebar-collapsed');
        syncSidebarState();
      });
      sidebarToggle.addEventListener('click', toggleSidebar);
      topbarNavBtn.addEventListener('click', toggleSidebar);
      librarySearch.addEventListener('input', renderLibrary);
      libraryIndustryFilter.addEventListener('change', renderLibrary);
      libraryTemplateFilter.addEventListener('change', renderLibrary);
      libraryLanguageFilter.addEventListener('change', renderLibrary);
      libraryClearBtn.addEventListener('click', () => {
        librarySearch.value = '';
        libraryIndustryFilter.value = 'all';
        libraryTemplateFilter.value = 'all';
        libraryLanguageFilter.value = 'all';
        renderLibrary();
      });
      document.getElementById('template_select').addEventListener('change', () => {
        renderTemplateCard();
        applyTemplateDefaults(false);
        handleBaseFormChange();
      });
      ['template_other', 'industry_other', 'target_user_other', 'output_language_other', 'risk_tolerance_other', 'task_description', 'creative_notes']
        .forEach(id => document.getElementById(id).addEventListener('input', handleBaseFormChange));
      ['industry_select', 'target_user_select', 'output_language_select', 'risk_tolerance_select']
        .forEach(id => document.getElementById(id).addEventListener('change', handleBaseFormChange));
      stackCustomInput.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
          event.preventDefault();
          addCustomValue('stack');
        }
      });
      constraintCustomInput.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
          event.preventDefault();
          addCustomValue('constraint');
        }
      });
      environmentCustomInput.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
          event.preventDefault();
          addCustomValue('environment');
        }
      });
      window.addEventListener('resize', handleResize);
      window.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
          closeModelModal();
          closeDrawer();
          if (window.innerWidth <= 960 && !appShell.classList.contains('sidebar-collapsed')) {
            appShell.classList.add('sidebar-collapsed');
            syncSidebarState();
          }
        }
      });

      syncModelTokenVisibilityButton();
      Promise.all([refreshOverview(), refreshLibrary(), refreshModelSettings()]).catch(error => {
        setStatus(error.message || '初始化数据失败', true);
        setModelSettingsStatus(error.message || '初始化模型配置失败', true);
      });
    } catch (error) {
      setStatus(`页面初始化失败：${error && error.message ? error.message : String(error)}`, true);
      console.error(error);
    }
  </script>
</body>
</html>
"""
    return html.replace("__OVERVIEW_JSON__", overview_json).replace("__ADMIN_JSON__", admin_json)
