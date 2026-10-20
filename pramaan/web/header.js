const escapeHtml = (text) => String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let root = parentElement.querySelector(".bar");
  if (!root) {
    root = document.createElement("header");
    root.className = "bar";
    parentElement.appendChild(root);
  }
  const nav = data.nav.map((name, i) => `<button class="${i === data.active ? "on" : ""}" data-nav="${i}">${escapeHtml(name)}</button>`).join("");
  const langs = data.langs.map((l) => `<button class="${l.value === data.lang ? "on" : ""}" data-lang="${l.value}">${escapeHtml(l.label)}</button>`).join("");
  root.innerHTML = `
    <div class="brand" data-nav="0"><span class="word">pramaan<i>.</i></span><span class="script">பிரமாணம் · प्रमाण</span></div>
    <nav aria-label="Main">${nav}</nav>
    <div class="right">
      <div class="search"><input type="text" placeholder="${escapeHtml(data.search)}" aria-label="${escapeHtml(data.search)}"><span class="kbd">/</span><div class="results"></div></div>
      <div class="seg" role="group">${langs}</div>
      <div class="who"><span class="avatar">TN</span><span class="role">${escapeHtml(data.role)}</span></div>
    </div>`;

  root.querySelectorAll("[data-nav]").forEach((el) => {
    el.onclick = () => setTriggerValue("nav", Number(el.dataset.nav));
  });
  root.querySelectorAll("[data-lang]").forEach((el) => {
    el.onclick = () => { if (el.dataset.lang !== data.lang) setTriggerValue("lang", el.dataset.lang); };
  });

  const input = root.querySelector(".search input");
  const box = root.querySelector(".results");
  let matches = [];
  let active = 0;
  const show = () => {
    const query = input.value.trim().toLowerCase();
    matches = query ? data.items.filter((item) => item.label.toLowerCase().includes(query)).slice(0, 8) : [];
    active = 0;
    box.innerHTML = matches.map((m, i) => `<button class="${i === 0 ? "hl" : ""}" data-pick="${i}">${escapeHtml(m.label)}<span>${escapeHtml(m.kind)}</span></button>`).join("");
    box.classList.toggle("open", matches.length > 0);
    box.querySelectorAll("[data-pick]").forEach((el) => {
      el.onmousedown = (event) => { event.preventDefault(); setTriggerValue("search", matches[Number(el.dataset.pick)].value); };
    });
  };
  input.oninput = show;
  input.onblur = () => setTimeout(() => box.classList.remove("open"), 120);
  input.onkeydown = (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!matches.length) return;
      active = (active + (event.key === "ArrowDown" ? 1 : matches.length - 1)) % matches.length;
      box.querySelectorAll("button").forEach((b, i) => b.classList.toggle("hl", i === active));
    } else if (event.key === "Enter" && matches.length) {
      setTriggerValue("search", matches[active].value);
    } else if (event.key === "Escape") {
      input.value = "";
      box.classList.remove("open");
      input.blur();
    }
  };

  const slash = (event) => {
    const tag = (event.composedPath()[0] || {}).tagName || "";
    if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(tag)) {
      event.preventDefault();
      input.focus();
    }
  };
  document.addEventListener("keydown", slash);
  return () => document.removeEventListener("keydown", slash);
}
