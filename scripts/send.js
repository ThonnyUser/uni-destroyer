// Run this in a logged-in page with your browser tool's JavaScript action.
// It lets the page hand files and pictures to `hw.py receive`, which saves them in the vault.
// Set the port and token that `hw.py receive` printed, then call the helpers ONE AT A TIME.
//
//   window.__HW = { port: 8765, token: "abcd1234" };
//   await window.__file(url, "Course Outline.pdf");          // a file the page can open (uses your sign-in)
//   await window.__shot("Week 3", "q12", document.body);     // a picture of the page (or one element)
//
// Files go to the vault's _work folder (temporary). Pictures go to Homework/<group>/.
window.__HW = window.__HW || { port: 8765, token: "" };
window.__post = async (kind, name, group, blob) => {
  const q = new URLSearchParams({ kind, name, group: group || "", token: window.__HW.token });
  const r = await fetch(`http://127.0.0.1:${window.__HW.port}/?${q}`, { method: "POST", body: blob });
  return r.status;
};
window.__file = async (url, name) => {
  let r = await fetch(url, { credentials: "include" });
  let type = r.headers.get("content-type") || "";
  if (/html/i.test(type)) { // Moodle "resource" pages point to the real file
    const doc = new DOMParser().parseFromString(await r.text(), "text/html");
    const el = doc.querySelector('a[href*="pluginfile"], object[data*="pluginfile"], embed[src*="pluginfile"], iframe[src*="pluginfile"]');
    const u = el && (el.getAttribute("href") || el.getAttribute("data") || el.getAttribute("src"));
    if (!u) return "no file link";
    r = await fetch(new URL(u, url).href, { credentials: "include" });
  }
  const blob = await r.blob();
  const status = await window.__post("file", name, "", blob);
  return `${name}: sent ${Math.round(blob.size / 1024)} KB, status ${status}`;
};
window.__shot = async (group, name, el) => {
  if (!window.html2canvas) {
    await new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
      s.onload = ok; s.onerror = () => bad(new Error("html2canvas blocked"));
      document.head.appendChild(s);
    });
  }
  const canvas = await window.html2canvas(el || document.body, { useCORS: true, scale: 1, logging: false });
  const blob = await new Promise((ok) => canvas.toBlob(ok, "image/png"));
  const status = await window.__post("shot", name.endsWith(".png") ? name : name + ".png", group, blob);
  return `${name}: picture ${canvas.width}x${canvas.height}, ${Math.round(blob.size / 1024)} KB, status ${status}`;
};
"sent helpers"
