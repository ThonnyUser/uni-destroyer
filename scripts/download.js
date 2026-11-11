// Run in a logged-in Moodle-style course page with your browser tool's JavaScript action.
// It saves files to the browser's normal Downloads folder, ONE file per call.
// Name every file starting with "hwtmp" so `hw.py finish --also-delete hwtmp*` can remove them later.
//
//   await window.__dl("Course Outline - PDF", "hwtmp ELEC1111 Course Outline");   // one file by its link text
//
//   window.__collect(/^Topic (\d)/, /Workshop|Tutorial/i);   // list files in matching sections
//   await window.__dlk(0);                                    // then download item 0, 1, 2 ... one per call
//
// Moodle "resource" links open a page that points to the real file; this finds it.
// Waiting for the user to allow "multiple downloads" in the browser may be needed the first time.
const __fileOf = async (href) => {
  let r = await fetch(href, { credentials: "include" });
  let type = r.headers.get("content-type") || "";
  if (/html/i.test(type)) {
    const doc = new DOMParser().parseFromString(await r.text(), "text/html");
    const el = doc.querySelector('a[href*="pluginfile"], object[data*="pluginfile"], embed[src*="pluginfile"], iframe[src*="pluginfile"]');
    const u = el && (el.getAttribute("href") || el.getAttribute("data") || el.getAttribute("src"));
    if (!u) return null;
    r = await fetch(new URL(u, href).href, { credentials: "include" });
    type = r.headers.get("content-type") || "";
  }
  return { blob: await r.blob(), type };
};
const __save = (blob, type, name) => {
  const ext = /pdf/i.test(type) ? ".pdf" : /presentation|powerpoint/i.test(type) ? ".pptx" : /word/i.test(type) ? ".docx" : /zip/i.test(type) ? ".zip" : ".bin";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name.replace(/[<>:"/\\|?*]/g, "") + ext;
  document.body.appendChild(a); a.click(); a.remove();
  return `${name}${ext} ${Math.round(blob.size / 1024)} KB`;
};
window.__dl = async (needle, outName) => {
  const link = [...document.querySelectorAll(".activityname a")].find((a) => (a.innerText || "").replace(/\s+/g, " ").includes(needle));
  if (!link) return "not found: " + needle;
  const f = await __fileOf(link.href);
  return f ? __save(f.blob, f.type, outName) : "no file link for " + needle;
};
window.__collect = (sectionRe, nameRe) => {
  window.__items = [];
  document.querySelectorAll("li.section, .course-section").forEach((s) => {
    const sn = ((s.querySelector(".sectionname, h3") || {}).innerText || "").trim();
    const m = sn.match(sectionRe);
    if (!m) return;
    s.querySelectorAll(".activityname a").forEach((a) => {
      const name = (a.innerText || "").replace(/\s+/g, " ").replace(/ ?(File|Folder|URL|Page|External tool|Quiz|Assignment|Forum)$/, "").trim();
      if (/mod\/resource\//.test(a.getAttribute("href") || "") && nameRe.test(name)) window.__items.push({ sec: m[1] || sn, name, href: a.href });
    });
  });
  return window.__items.length + " | " + window.__items.map((x, i) => `${i}:${x.sec} ${x.name.slice(0, 26)}`).join(" | ");
};
window.__dlk = async (k) => {
  const j = (window.__items || [])[k];
  if (!j) return "no item " + k;
  const f = await __fileOf(j.href);
  return f ? `${k} ${j.name.slice(0, 30)} ` + __save(f.blob, f.type, `hwtmp ${j.sec} ${String(k).padStart(2, "0")}`) : `${k} no file link`;
};
"download helpers ready"
