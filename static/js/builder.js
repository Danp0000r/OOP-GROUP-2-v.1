/**
 * builder.js — BuildLab PC Builder frontend logic
 * Handles: drag-and-drop, slot management, templates, compatibility check, save/export build
 */

let currentBuildId = null; // Track currently loaded build for updates

const CAT_COLOR = {
  CPU:"#1e0a3c", Motherboard:"#0a1e3c", GPU:"#0a1040", RAM:"#0a2e1a",
  Storage:"#2e1a0a", PSU:"#2e0a1a", Cooling:"#0a2030", Case:"#1a1a2e"
};
const CAT_TEXT = {
  CPU:"#a78bfa", Motherboard:"#78bffa", GPU:"#60a5fa", RAM:"#6ee7b7",
  Storage:"#fbbf24", PSU:"#f472b6", Cooling:"#67e8f9", Case:"#c4b5fd"
};
const ICONS = { CPU:"⚙", Motherboard:"🔌", GPU:"🖥", RAM:"🧩", Storage:"💾", PSU:"⚡", Cooling:"❄", Case:"📦" };

let draggingId  = null;
let draggingCat = null;
const selectedParts = {};
window.selectedParts = selectedParts;
let adminModeActive = false;

function isAdminUser() {
  return window.builderIsAdmin === true || window.builderIsAdmin === 'true';
}

function updateAdminModeUI() {
  const adminBtn = document.getElementById('admin-mode-btn');
  const exportBtn = document.getElementById('position-export-btn');
  const importBtn = document.getElementById('position-import-btn');

  if (adminBtn) {
    adminBtn.style.display = isAdminUser() ? 'inline-flex' : 'none';
    adminBtn.textContent = adminModeActive ? 'Admin Mode: ON' : 'Admin Mode';
    adminBtn.classList.toggle('btn-primary', adminModeActive);
    adminBtn.classList.toggle('btn-ghost', !adminModeActive);
  }

  if (exportBtn) {
    exportBtn.style.display = adminModeActive ? 'inline-flex' : 'none';
  }
  if (importBtn) {
    importBtn.style.display = adminModeActive ? 'inline-flex' : 'none';
  }
  const adminHint = document.getElementById('admin-mode-hint');
  if (adminHint) {
    adminHint.style.display = adminModeActive ? 'flex' : 'none';
  }
  const subpartSelector = document.getElementById('subpart-selector');
  if (subpartSelector) {
    subpartSelector.style.display = adminModeActive ? subpartSelector.style.display || 'flex' : 'none';
  }
}

function setAdminMode(enabled) {
  if (!isAdminUser()) return;
  adminModeActive = Boolean(enabled);
  if (window.nexus3d_full && typeof window.nexus3d_full.setAdminMode === 'function') {
    window.nexus3d_full.setAdminMode(adminModeActive);
  }
  updateAdminModeUI();
}

function toggleAdminMode() {
  if (!isAdminUser()) return;
  if (!adminModeActive) {
    const confirmed = confirm(
      'Admin mode lets you move component positions for everyone. Only use this to edit the shared layout. Continue?'
    );
    if (!confirmed) return;
  }
  setAdminMode(!adminModeActive);
}

/* ── Add a component to a slot ───────────────────────── */
function addToSlot(id, name, brand, cat, price) {
  const componentId = Number(id);
  const card = document.querySelector(`.component-card[data-id="${componentId}"]`);
  const cardPrice = card?.dataset?.selectedPrice ? parseFloat(card.dataset.selectedPrice) : null;
  const finalPrice = (cardPrice !== null && !isNaN(cardPrice)) ? cardPrice : price;
  selectedParts[cat] = { id: componentId, name, brand, price: finalPrice };
  renderSlot(cat);
  updateProgress();
  if (window.nexus3d_full && typeof window.nexus3d_full.refresh === 'function') {
    window.nexus3d_full.refresh();
    if (typeof window.nexus3d_full.updateSelectedUI === 'function') {
      window.nexus3d_full.updateSelectedUI();
    }
    if (typeof scheduleCompatPreview === 'function') scheduleCompatPreview();
  }
}

function removeFromSlot(cat) {
  delete selectedParts[cat];
  renderSlot(cat);
  updateProgress();
  if (window.nexus3d_full && typeof window.nexus3d_full.refresh === 'function') {
    window.nexus3d_full.refresh();
    if (typeof window.nexus3d_full.updateSelectedUI === 'function') {
      window.nexus3d_full.updateSelectedUI();
    }
    if (typeof scheduleCompatPreview === 'function') scheduleCompatPreview();
  }
}

/* ── Render a single slot ─────────────────────────────── */
function renderSlot(cat) {
  const slot = document.getElementById("slot-" + cat);
  if (!slot) return;
  const p = selectedParts[cat];
  slot.classList.toggle("filled", !!p);
  slot.innerHTML = `
    <div class="slot-icon" style="${p ? `background:${CAT_COLOR[cat]};` : ""}">
      <span style="${p ? `color:${CAT_TEXT[cat]};` : ""}">${ICONS[cat] || "⚙"}</span>
    </div>
    <div class="slot-info" style="flex:1;min-width:0;">
      <div class="slot-cat" style="${p ? `color:${CAT_TEXT[cat]};` : ""}">${cat}</div>
      ${p
        ? `<div class="slot-name">${p.name}</div><div class="slot-brand">${p.brand}</div>`
        : `<div class="slot-empty-text">Click or drag a component here</div>`
      }
    </div>
    ${p ? `
      <span class="slot-price">&#8369;${p.price.toLocaleString()}</span>
      <button class="slot-remove" onclick="event.stopPropagation();removeFromSlot('${cat}')">&#x2715;</button>
      <span class="slot-check">&#10003;</span>
    ` : ""}
  `;
  slot.setAttribute("ondragover", `event.preventDefault();onDragOver(event,'${cat}')`);
  slot.setAttribute("ondragleave", "onDragLeave(event)");
  slot.setAttribute("ondrop", `onDrop(event,'${cat}')`);
}

/* ── Progress / Total ─────────────────────────────────── */
function updateProgress() {
  const filled = Object.keys(selectedParts).length;
  const total  = 8;
  const pct    = Math.round((filled / total) * 100);
  const sum    = Object.values(selectedParts).reduce((s, p) => s + p.price, 0);

  const bar   = document.getElementById("prog-bar");
  const label = document.getElementById("prog-label");
  const totEl = document.getElementById("build-total");

  if (bar)   { bar.style.width = pct + "%"; bar.style.background = filled === total ? "#22c55e" : "var(--primary)"; }
  if (label) label.textContent = `${filled}/8`;
  if (totEl) totEl.innerHTML   = `&#8369;${sum.toLocaleString()}`;
}

/* ── Filter by category ──────────────────────────────── */
let currentCat = "ALL";

function setCat(cat, el) {
  currentCat = cat;
  document.querySelectorAll(".cat-pills .filter-pill").forEach(b => b.classList.remove("active"));
  if (el) el.classList.add("active");
  filterComponents(document.getElementById("component-search")?.value || "");
}

function filterComponents(query) {
  const q = (query || "").toLowerCase();
  document.querySelectorAll(".component-card").forEach(card => {
    const matchCat  = currentCat === "ALL" || card.dataset.cat === currentCat;
    const matchName = !q || card.dataset.name.toLowerCase().includes(q);
    card.style.display = (matchCat && matchName) ? "" : "none";
  });
}

function selectSlotComponent(cat, event) {
  if (event && event.preventDefault) event.preventDefault();
  const pill = Array.from(document.querySelectorAll('.cat-pills .filter-pill')).find(b => b.textContent.trim() === cat.toUpperCase());
  if (pill) setCat(cat, pill);
  else setCat('ALL', document.querySelector('.cat-pills .filter-pill'));

  const multiSelect = event && (event.ctrlKey || event.metaKey);
  if (window.nexus3d_full && typeof window.nexus3d_full.selectSlot === 'function') {
    window.nexus3d_full.selectSlot(cat, multiSelect);
  }
}

/* ── Drag & Drop ─────────────────────────────────────── */
function onDragStart(event, id, cat) {
  draggingId  = id;
  draggingCat = cat;
  event.dataTransfer.effectAllowed = "move";
  // Store data in dataTransfer as backup
  event.dataTransfer.setData("text/plain", JSON.stringify({ id, cat }));
}

function onDragOver(event, slotCat) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  // Allow drop if categories match
  if (draggingCat && draggingCat !== slotCat) return;
  const slot = document.getElementById("slot-" + slotCat);
  if (slot) slot.classList.add("drag-over");
}

function onDragLeave(event) {
  event.currentTarget.classList.remove("drag-over");
}

function onDrop(event, slotCat) {
  event.preventDefault();
  const slot = document.getElementById("slot-" + slotCat);
  if (slot) slot.classList.remove("drag-over");

  // Try to recover data from dataTransfer if state was lost
  let dropId  = draggingId;
  let dropCat = draggingCat;
  if (!dropId) {
    try {
      const stored = JSON.parse(event.dataTransfer.getData("text/plain") || "{}");
      dropId  = stored.id;
      dropCat = stored.cat;
    } catch(e) {}
  }

  if (!dropId || !dropCat || dropCat !== slotCat) return;

  const card = document.querySelector(`.component-card[data-id="${dropId}"]`);
  if (!card) return;
  const name  = card.querySelector(".cc-name")?.textContent  || "";
  const priceText = card.querySelector(".cc-price")?.textContent || "0";
  const price = parseFloat(priceText.replace(/[^\d.]/g, "")) || 0;
  const brand = card.querySelector(".cc-brand")?.textContent || "";
  addToSlot(dropId, name, brand, slotCat, price);
  draggingId = null; draggingCat = null;
}

function getCardLowestPrice(card) {
  if (!card) return 0;
  const storeBtns = Array.from(card.querySelectorAll('.cc-store-btn'));
  if (storeBtns.length) {
    return Math.min(...storeBtns.map(btn => parseFloat(btn.dataset.price) || Infinity));
  }
  const raw = card.dataset.defaultPrice || card.querySelector('.cc-price')?.textContent || '0';
  return parseFloat(String(raw).replace(/[^\d.]/g, '')) || 0;
}

function sortCardStoreButtons(card) {
  const container = card.querySelector('.cc-store-links');
  if (!container) return [];
  const buttons = Array.from(container.querySelectorAll('.cc-store-btn'));
  buttons.sort((a, b) => (parseFloat(a.dataset.price) || 0) - (parseFloat(b.dataset.price) || 0));
  buttons.forEach(btn => container.appendChild(btn));
  return buttons;
}

function activateDefaultStoreSelection(card) {
  if (!card) return;
  const buttons = sortCardStoreButtons(card);
  const firstBtn = buttons[0] || card.querySelector('.cc-store-btn');
  if (!firstBtn) return;
  card.querySelectorAll('.cc-store-btn').forEach(btn => btn.classList.remove('active'));
  firstBtn.classList.add('active');
  const price = parseFloat(firstBtn.getAttribute('data-price')) || getCardLowestPrice(card);
  card.dataset.selectedPrice = price;
  const priceEl = card.querySelector('.cc-price');
  if (priceEl) {
    priceEl.textContent = '₱' + price.toLocaleString();
  }
}

function resetCardStoreSelection(card) {
  if (!card) return;
  card.removeAttribute('data-selected-price');
  const defaultPrice = getCardLowestPrice(card);
  const priceEl = card.querySelector('.cc-price');
  if (priceEl) {
    priceEl.textContent = '₱' + defaultPrice.toLocaleString();
  }
  card.querySelectorAll('.cc-store-btn').forEach(btn => btn.classList.remove('active'));
  activateDefaultStoreSelection(card);
}

function resetAllStoreSelections() {
  document.querySelectorAll('.component-card').forEach(resetCardStoreSelection);
}

/* ── Compatibility check ─────────────────────────────── */
function checkCompat() {
  const ids = Object.values(selectedParts).map(p => p.id);
  if (!ids.length) { alert("Add some parts first."); return; }
  fetch("/api/compatibility", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ component_ids: ids }),
  })
    .then(r => r.json())
    .then(data => {
      const el = document.getElementById("compat-result");
      if (!el) return;
      el.style.display = "block";
      el.className = "compat-banner " + (data.compatible ? "compat-ok" : "compat-fail");
      el.textContent = data.compatible ? "All parts are compatible!" : data.issues.join(" · ");
    })
    .catch(() => alert("Compatibility check failed."));
}

/* ── Save build ──────────────────────────────────────── */
function saveBuild() {
  const ids  = Object.values(selectedParts).map(p => p.id);
  const name = document.getElementById("build-name")?.textContent.trim() || "My Build";
  if (!ids.length) { alert("Add some parts first."); return; }
  
  if (currentBuildId) {
    // Update existing build
    fetch("/api/builds/" + currentBuildId, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, component_ids: ids }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) { alert(data.error); return; }
        alert("Build updated!");
      })
      .catch(() => alert("Update failed."));
  } else {
    // Create new build
    fetch("/api/builds/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, component_ids: ids }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) { alert(data.error); return; }
        alert("Build saved! View it in My Builds.");
      })
      .catch(() => alert("Save failed."));
  }
}

/* ── Export build (download as .txt) ─────────────────── */
function exportBuild() {
  const name  = document.getElementById("build-name")?.textContent.trim() || "My Build";
  const parts = Object.entries(selectedParts);
  if (!parts.length) { alert("Add some parts first."); return; }

  const sep   = "=".repeat(40);
  const lines = [`BuildLab — ${name}`, sep];
  let total   = 0;

  const ORDER = ["CPU","Motherboard","RAM","GPU","PSU","Case","Storage","Cooling"];
  ORDER.forEach(cat => {
    const p = selectedParts[cat];
    if (p) {
      lines.push(`${cat.padEnd(14)} ${p.name} (${p.brand})  —  P${p.price.toLocaleString()}`);
      total += p.price;
    } else {
      lines.push(`${cat.padEnd(14)} —`);
    }
  });

  lines.push(sep);
  lines.push(`${"TOTAL".padEnd(14)} P${total.toLocaleString()}`);

  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = name.replace(/\s+/g, "_") + ".txt";
  a.click();
  URL.revokeObjectURL(url);
}

/* ── Templates ─────────────────────────────────────────
   IDs mapped from actual components.json:
   CPU: 1-6 | GPU: 7-13 | RAM: 14-19 | Mobo: 20-25
   PSU: 26-29 | Storage: 30-33 | Cooling: 34-38 | Case: 39-41
   Budget : CPU=1(5600G), GPU=7(GTX1650),  RAM=14(8GB DDR4),  Mobo=20(A520M),   PSU=26(550W Brnz), Stor=30(256GB SATA), Cool=34(Stock),       Case=39
   Mid    : CPU=2(5600),  GPU=9(RX6600),   RAM=15(16GB DDR4), Mobo=22(B550M),   PSU=27(650W Brnz), Stor=32(500GB NVMe), Cool=35(AK400),        Case=40
   Gaming : CPU=6(i5-13), GPU=12(RTX4070), RAM=16(32GB DDR4), Mobo=25(B760M-A), PSU=29(750W Gold), Stor=33(1TB NVMe),   Cool=37(LE520),        Case=41
   ────────────────────────────────────────────────────── */
const TEMPLATES = {
  budget: [1, 7,  14, 20, 26, 30, 34, 39],
  mid:    [2, 9,  15, 22, 27, 32, 35, 40],
  gaming: [6, 12, 19, 25, 29, 33, 37, 41],
};

function loadTemplate(key) {
  const ids = TEMPLATES[key] || [];
  // Clear existing
  Object.keys(selectedParts).forEach(cat => delete selectedParts[cat]);
  ["CPU","Motherboard","RAM","GPU","PSU","Case","Storage","Cooling"].forEach(renderSlot);

  resetAllStoreSelections();

  let loaded = 0;
  ids.forEach(id => {
    const card = document.querySelector(`.component-card[data-id="${id}"]`);
    if (!card) { console.warn("Template: card not found for id", id); return; }
    const cat   = card.dataset.cat;
    const name  = card.querySelector(".cc-name")?.textContent  || "";
    const price = getCardLowestPrice(card);
    const brand = card.querySelector(".cc-brand")?.textContent || "";
    selectedParts[cat] = { id, name, brand, price };
    loaded++;
  });

  ["CPU","Motherboard","RAM","GPU","PSU","Case","Storage","Cooling"].forEach(renderSlot);
  updateProgress();
  if (window.nexus3d_full && typeof window.nexus3d_full.refresh === 'function') {
    window.nexus3d_full.refresh();
    if (typeof window.nexus3d_full.updateSelectedUI === 'function') {
      window.nexus3d_full.updateSelectedUI();
    }
      if (typeof scheduleCompatPreview === 'function') scheduleCompatPreview();
  }

  const nameMap = { budget:"Budget Build", mid:"Mid-Range Build", gaming:"Gaming Build" };
  const nameEl  = document.getElementById("build-name");
  if (nameEl) nameEl.textContent = nameMap[key] || "My Build";

  if (loaded < ids.length) {
    console.warn(`Template '${key}': loaded ${loaded}/${ids.length} parts`);
  }

  // Refresh card UI states
  if (typeof refreshCardStates === "function") refreshCardStates();
}

function clearBuild() {
  currentBuildId = null; // Reset to new build
  Object.keys(selectedParts).forEach(cat => delete selectedParts[cat]);
  ["CPU","Motherboard","RAM","GPU","PSU","Case","Storage","Cooling"].forEach(renderSlot);
  updateProgress();
  resetAllStoreSelections();
  if (window.nexus3d_full && typeof window.nexus3d_full.refresh === 'function') {
    window.nexus3d_full.refresh();
    if (typeof window.nexus3d_full.updateSelectedUI === 'function') {
      window.nexus3d_full.updateSelectedUI();
    }
    if (typeof scheduleCompatPreview === 'function') scheduleCompatPreview();
  }
}

function clearAllComponents() {
  if (confirm('Remove all components from your build? This cannot be undone.')) {
    clearBuild();
  }
}

/* ── Init ────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".component-card").forEach(card => {
    card.addEventListener("dragend", () => { draggingId = null; draggingCat = null; });
    activateDefaultStoreSelection(card);
  });
  // Attach safe click handlers for "Add to Build" buttons (avoid inline JS with unescaped names)
  document.querySelectorAll('.cc-add-btn').forEach(btn => {
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const card = btn.closest('.component-card');
      if (!card) return;
      const id = card.dataset.id;
      const name = card.dataset.name || card.querySelector('.cc-name')?.textContent || '';
      const brand = card.dataset.brand || card.querySelector('.cc-brand')?.textContent || '';
      const cat = card.dataset.cat;
      const priceText = card.querySelector('.cc-price')?.textContent || '0';
      const price = parseFloat(priceText.replace(/[^0-9.]/g, '')) || 0;
      addToSlot(id, name, brand, cat, price);
      if (typeof refreshCardStates === 'function') refreshCardStates();
    });
  });
  // Handle clicks on store buttons: set component price to link price
  document.addEventListener('click', (e) => {
    let target = e.target;
    if (target.nodeType !== Node.ELEMENT_NODE) {
      target = target.parentElement;
    }
    const btn = target?.closest('.cc-store-btn');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const price = parseFloat(btn.getAttribute('data-price')) || 0;

    const card = btn.closest('.component-card');
    if (!card) return;

    const priceEl = card.querySelector('.cc-price');
    if (priceEl) priceEl.textContent = '₱' + price.toLocaleString();

    card.querySelectorAll('.cc-store-btn').forEach(other => other.classList.remove('active'));
    btn.classList.add('active');

    card.dataset.selectedPrice = price;

    const category = card.dataset.cat;
    if (selectedParts[category] && String(selectedParts[category].id) === String(card.dataset.id)) {
      selectedParts[category].price = price;
      renderSlot(category);
      updateProgress();
    }
  });

  // Compatibility Deep Info modal logic
  function gatherSelectedPartsString() {
    const parts = Object.values(selectedParts).map(p => p.name).filter(Boolean);
    return parts.join(', ');
  }

  // Debounced compatibility preview (power draw + status only)
  let __compatPreviewTimer = null;
  function scheduleCompatPreview() {
    if (__compatPreviewTimer) clearTimeout(__compatPreviewTimer);
    __compatPreviewTimer = setTimeout(() => { __compatPreviewTimer = null; updateCompatibilityPreview(); }, 450);
  }

  function updateCompatibilityPreview() {
    const parts = gatherSelectedPartsString();
    const powerEl = document.getElementById('compat-power');
    const statusEl = document.getElementById('compat-status');
    if (!parts) {
      if (powerEl) powerEl.textContent = '— W';
      if (statusEl) { statusEl.textContent = 'Unknown'; statusEl.style.color = 'var(--muted)'; }
      if (window.nexus3d_full && typeof window.nexus3d_full.setCompatibilityAlert === 'function') {
        window.nexus3d_full.setCompatibilityAlert(false);
      }
      return;
    }
    fetch('/api/compatibility/evaluate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ parts })
    })
    .then(r => r.json())
    .then(report => {
      if (powerEl) powerEl.textContent = (report.wattageEstimate || '—') + ' W';
      if (statusEl) {
        statusEl.textContent = (report.status || 'Unknown').toUpperCase();
        statusEl.style.color = report.compatible ? '#34d399' : '#fb7185';
      }
      if (window.nexus3d_full && typeof window.nexus3d_full.setCompatibilityAlert === 'function') {
        window.nexus3d_full.setCompatibilityAlert(!report.compatible);
      }
    })
    .catch(err => {
      console.warn('Compat preview failed', err);
      if (powerEl) powerEl.textContent = '— W';
      if (statusEl) { statusEl.textContent = 'Unknown'; statusEl.style.color = 'var(--muted)'; }
      if (window.nexus3d_full && typeof window.nexus3d_full.setCompatibilityAlert === 'function') {
        window.nexus3d_full.setCompatibilityAlert(false);
      }
    });
  }
  // expose to global so other functions can schedule it
  window.scheduleCompatPreview = scheduleCompatPreview;
  window.updateCompatibilityPreview = updateCompatibilityPreview;

  function openCompatDeepInfo() {
    const parts = gatherSelectedPartsString();
    if (!parts) {
      alert('Select some parts first to analyze.');
      return;
    }
    const modal = document.getElementById('compat-deep-modal');
    const body = document.getElementById('compat-deep-body');
    if (!modal || !body) return;
    // open modal immediately with a loading state so user sees the popup
    modal.style.display = 'flex';
    document.getElementById('compat-deep-summary').innerHTML = '<div style="font-weight:700;color:#9ca3ff;">Analyzing…</div>';
    document.getElementById('compat-deep-issues').innerHTML = '';
    document.getElementById('compat-deep-recs').innerHTML = '';
    document.getElementById('compat-detected-list').innerHTML = '';

    // If the selected parts were chosen from DB-backed cards, prefer sending their IDs
    // so the server can use authoritative DB prices. Otherwise fall back to free-text evaluate.
    const selectedIds = Object.values(selectedParts).map(p => p.id).filter(Boolean);
    if (selectedIds.length === Object.keys(selectedParts).length) {
      // All selected parts have IDs — call compatibility route that accepts component_ids
      fetch('/api/compatibility', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ component_ids: selectedIds })
      })
      .then(r => r.json())
      .then(report => renderCompatDeepReport(report))
      .catch(err => {
        console.warn('Compatibility fetch failed', err);
        document.getElementById('compat-deep-summary').innerHTML = '<div style="color:#f87171;font-weight:800;">Failed to fetch compatibility report.</div>';
      });
    } else {
      fetch('/api/compatibility/evaluate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ parts })
      })
      .then(r => r.json())
      .then(report => renderCompatDeepReport(report))
      .catch(err => {
        console.warn('Compatibility fetch failed', err);
        document.getElementById('compat-deep-summary').innerHTML = '<div style="color:#f87171;font-weight:800;">Failed to fetch compatibility report.</div>';
      });
    }
  }

  function closeCompatDeepInfo() {
    const modal = document.getElementById('compat-deep-modal');
    if (modal) modal.style.display = 'none';
  }

  // expose modal controls globally for inline onclick handlers
  window.openCompatDeepInfo = openCompatDeepInfo;
  window.closeCompatDeepInfo = closeCompatDeepInfo;

  function renderCompatDeepReport(report) {
    const summary = document.getElementById('compat-deep-summary');
    const issuesEl = document.getElementById('compat-deep-issues');
    const recsEl = document.getElementById('compat-deep-recs');
    const listEl = document.getElementById('compat-detected-list');
    if (!summary || !issuesEl || !recsEl || !listEl) return;

    const summaryExtras = [];
    if (report.buildTier) summaryExtras.push(report.buildTier);
    if (report.totalBuildPriceFormatted) summaryExtras.push(report.totalBuildPriceFormatted);
    summary.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div style="font-size:13px;font-weight:800;color:${report.compatible ? '#34d399' : '#fb7185'};letter-spacing:.03em;">${(report.status||'Unknown').toUpperCase()} — Compatible: ${report.compatible}</div>
        <div style="font-size:15px;font-weight:700;color:#f8fafc;">${report.summary || 'No summary available.'}</div>
        ${summaryExtras.length ? `<div style="font-size:12px;color:rgba(255,255,255,.75);">${summaryExtras.join(' • ')}</div>` : ''}
        <div style="display:flex;flex-wrap:wrap;gap:12px;font-size:13px;color:rgba(255,255,255,.8);">
          <span>Estimated Wattage: <strong style="color:#f8fafc;">${report.wattageEstimate || 'N/A'}W</strong></span>
          <span>Recommended PSU: <strong style="color:#f8fafc;">${report.recommendedPsuWattage || 'N/A'}W</strong></span>
        </div>
      </div>
    `;

    // Clear any previous performance section before rendering a fresh one
    const existingPerf = summary.parentNode.querySelector('.compat-perf-summary');
    if (existingPerf) {
      existingPerf.remove();
    }

    // Performance summary (bottleneck, resolution, estimated FPS)
    const perfContainer = document.createElement('div');
    perfContainer.className = 'compat-perf-summary';
    perfContainer.style.marginTop = '12px';
    perfContainer.style.paddingTop = '8px';
    perfContainer.style.borderTop = '1px dashed rgba(255,255,255,.03)';

    const bot = report.bottleneckAnalysis || report.bottleneck || null;
    if (bot) {
      const bHtml = `
        <div style="font-weight:800;color:#fbbf24;margin-bottom:6px;">Performance / Bottleneck</div>
        <div style="font-size:13px;color:rgba(255,255,255,.8);">Balance: ${bot.balance || 'N/A'}</div>
        <div style="font-size:13px;color:rgba(255,255,255,.8);">CPU Score: ${bot.cpuPerformanceScore || 'N/A'} • GPU Score: ${bot.gpuPerformanceScore || 'N/A'}</div>
        <div style="font-size:12px;color:rgba(255,255,255,.6);margin-top:6px;">${bot.description || ''}</div>
      `;
      const div = document.createElement('div'); div.innerHTML = bHtml; perfContainer.appendChild(div);
    }

    if (report.gamingResolution) {
      const r = document.createElement('div'); r.style.marginTop='8px'; r.style.color='rgba(255,255,255,.8)'; r.innerHTML = `<div style="font-weight:800;color:#a78bfa;">Estimated Gaming Resolution</div><div style="margin-top:6px;">${report.gamingResolution}</div>`;
      perfContainer.appendChild(r);
    }

    const fps = report.estimatedFps || report.estimated_fps || null;
    if (fps && Object.keys(fps).length) {
      const fpsWrap = document.createElement('div'); fpsWrap.style.marginTop='10px';
      fpsWrap.innerHTML = '<div style="font-weight:800;color:#60a5fa;margin-bottom:6px;">Estimated FPS (1080p / 1440p / 4K)</div>';
      Object.entries(fps).forEach(([game, data]) => {
        const row = document.createElement('div'); row.style.display='flex'; row.style.justifyContent='space-between'; row.style.alignItems='center'; row.style.padding='6px 8px'; row.style.borderRadius='6px'; row.style.background='rgba(255,255,255,.02)'; row.style.marginTop='6px';
        const left = document.createElement('div'); left.style.fontWeight='700'; left.style.color='#e6e9ff'; left.textContent = game;
        const right = document.createElement('div'); right.style.color='rgba(255,255,255,.75)'; right.textContent = `${data['1080p'] || '?'} / ${data['1440p'] || '?'} / ${data['4K'] || '?'}`;
        row.appendChild(left); row.appendChild(right); fpsWrap.appendChild(row);
      });
      perfContainer.appendChild(fpsWrap);
    }

    // insert perfContainer after the summary
    summary.parentNode.insertBefore(perfContainer, summary.nextSibling);

    // Detected parts
    listEl.innerHTML = '';
    (report.detectedParts||[]).forEach(p => {
      const item = document.createElement('div');
      item.style.display = 'flex'; item.style.justifyContent = 'space-between'; item.style.alignItems='center';
      item.style.padding = '8px'; item.style.borderRadius = '8px'; item.style.background = 'rgba(255,255,255,.02)';
      item.innerHTML = `
        <div>
          <div style="font-weight:800;color:#e6e9ff;">${p.name || 'Unknown'}</div>
          <div style="font-size:12px;color:rgba(255,255,255,.55);">${p.type || ''} • ${p.source||'unknown'} ${p.verified?'<span style="color:#34d399;margin-left:6px;">✔ Verified</span>':''}</div>
        </div>
        <div style="font-weight:900;color:#a78bfa;">${p.priceFormatted||'N/A'}</div>
      `;
      listEl.appendChild(item);
    });

    // Issues
    issuesEl.innerHTML = '';
    if (report.issues && report.issues.length) {
      const h = document.createElement('div'); h.style.fontWeight='800'; h.style.color='#fb7185'; h.textContent='Issues'; issuesEl.appendChild(h);
      report.issues.forEach(it => {
        const d = document.createElement('div'); d.style.marginTop='8px'; d.style.padding='8px'; d.style.borderRadius='8px'; d.style.background='rgba(251,113,133,.06)';
        d.innerHTML = `<div style="font-weight:700;color:#ff9aa2">${it.severity?.toUpperCase() || 'NOTICE'} — ${it.component || ''}</div><div style="color:rgba(255,255,255,.75);margin-top:6px;">${it.message}</div>`;
        issuesEl.appendChild(d);
      });
    } else {
      issuesEl.innerHTML = '<div style="color:#34d399;font-weight:700;">No issues detected.</div>';
    }

    // (moved scheduleCompatPreview/updateCompatibilityPreview to outer scope)

    // Recommendations
    recsEl.innerHTML = '';
    if (report.passedChecks && report.passedChecks.length) {
      const h1 = document.createElement('div'); h1.style.fontWeight='800'; h1.style.color='#60a5fa'; h1.textContent='Passed Checks'; recsEl.appendChild(h1);
      const ul1 = document.createElement('ul'); ul1.style.marginTop='8px'; ul1.style.paddingLeft='18px';
      report.passedChecks.forEach(note => { const li = document.createElement('li'); li.style.marginTop='6px'; li.style.color='rgba(255,255,255,.8)'; li.textContent = note; ul1.appendChild(li); });
      recsEl.appendChild(ul1);
    }

    if (report.recommendations && report.recommendations.length) {
      const h2 = document.createElement('div'); h2.style.fontWeight='800'; h2.style.color='#fbbf24'; h2.textContent='Recommendations'; recsEl.appendChild(h2);
      const ul = document.createElement('ul'); ul.style.marginTop='8px'; ul.style.paddingLeft='18px';
      report.recommendations.forEach(r => { const li = document.createElement('li'); li.style.marginTop='6px'; li.style.color='rgba(255,255,255,.8)'; li.textContent = r; ul.appendChild(li); });
      recsEl.appendChild(ul);
    }

    if (report.upgradeSuggestions && report.upgradeSuggestions.length) {
      const h3 = document.createElement('div'); h3.style.fontWeight='800'; h3.style.color='#7dd3fc'; h3.textContent='Upgrade Suggestions'; recsEl.appendChild(h3);
      const ul3 = document.createElement('ul'); ul3.style.marginTop='8px'; ul3.style.paddingLeft='18px';
      report.upgradeSuggestions.forEach(s => { const li = document.createElement('li'); li.style.marginTop='6px'; li.style.color='rgba(255,255,255,.8)'; li.textContent = s; ul3.appendChild(li); });
      recsEl.appendChild(ul3);
    }

    if (report.valueRating || report.airflowWarning || report.futureHeadroom) {
      const misc = document.createElement('div'); misc.style.marginTop='10px'; misc.style.padding='10px'; misc.style.borderRadius='10px'; misc.style.background='rgba(255,255,255,.03)';
      misc.innerHTML = `
        ${report.valueRating ? `<div style="font-weight:800;color:#8b5cf6;">Value Rating</div><div style="color:rgba(255,255,255,.76);margin-top:4px;">${report.valueRating}</div>` : ''}
        ${report.airflowWarning ? `<div style="font-weight:800;color:#f97316;margin-top:10px;">Airflow Warning</div><div style="color:rgba(255,255,255,.76);margin-top:4px;">${report.airflowWarning}</div>` : ''}
        ${report.futureHeadroom ? `<div style="font-weight:800;color:#34d399;margin-top:10px;">Future Upgrade Headroom</div><div style="color:rgba(255,255,255,.76);margin-top:4px;">${report.futureHeadroom}</div>` : ''}
      `;
      recsEl.appendChild(misc);
    }

    // update short view
    const powerEl = document.getElementById('compat-power');
    const statusEl = document.getElementById('compat-status');
    if (powerEl) powerEl.textContent = (report.wattageEstimate || '—') + ' W';
    if (statusEl) {
      statusEl.textContent = (report.status || 'Unknown').toUpperCase();
      statusEl.style.color = report.compatible ? '#34d399' : '#fb7185';
    }
      if (window.nexus3d_full && typeof window.nexus3d_full.setCompatibilityAlert === 'function') {
        window.nexus3d_full.setCompatibilityAlert(!report.compatible);
      }
  }
  updateAdminModeUI();
  if (typeof scheduleCompatPreview === 'function') scheduleCompatPreview();
});
