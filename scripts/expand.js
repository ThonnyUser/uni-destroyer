// Run this in the page with your browser tool's JavaScript action.
// It opens content hidden behind toggles (accordions, details, tabs, "show more").
// It clicks only toggle-like controls that are CLOSED, and never submits, deletes,
// posts, pays or signs out. Safe to run twice (a second run opens nested toggles).
// After it returns, read the page text again.
(async () => {
  const BAD = /submit|delete|remove|sign ?out|log ?out|buy|pay|purchase|send|post|confirm|unsubscribe|reset|cancel|upload|give|enrol|enroll|drop|save|edit/i;
  const GOOD = /show|expand|more|view|open|reveal|details|read|toggle|example|hint|walkthrough|stub|output|stage|faq/i;
  const before = document.body.innerText.length;
  let opened = 0;
  document.querySelectorAll("details:not([open])").forEach((d) => { d.open = true; opened++; });
  const isClosed = (el) =>
    el.getAttribute("aria-expanded") === "false" ||
    el.classList.contains("collapsed") ||
    (el.getAttribute("role") === "tab" && el.getAttribute("aria-selected") === "false");
  const all = [...document.querySelectorAll('[aria-expanded], [data-bs-toggle], [data-toggle], .collapsed, [role="tab"], button')];
  for (const el of all) {
    if (el.tagName === "SUMMARY" || el.closest("form")) continue;
    const label = (el.innerText || el.getAttribute("aria-label") || "").trim();
    if (!label || BAD.test(label)) continue;
    if (el.tagName === "A" && !(el.getAttribute("href") || "#").startsWith("#")) continue;
    const toggle = el.hasAttribute("aria-expanded") || el.hasAttribute("data-bs-toggle") ||
      el.hasAttribute("data-toggle") || el.getAttribute("role") === "tab" || el.classList.contains("collapsed");
    if (toggle ? !isClosed(el) : !GOOD.test(label) || el.getAttribute("aria-expanded") === "true") continue;
    try { el.click(); opened++; await new Promise((r) => setTimeout(r, 150)); } catch (e) { /* ignore */ }
  }
  document.querySelectorAll(".collapse:not(.show)").forEach((e) => e.classList.add("show"));
  return `${opened} controls opened; page text ${before} -> ${document.body.innerText.length} characters`;
})()
