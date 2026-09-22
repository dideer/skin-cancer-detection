/**
 * nav.js
 * Shared navigation behaviour:
 * - Injects the sidebar into every authenticated page
 * - Highlights the active nav link based on current URL
 * - Handles mobile hamburger / overlay
 * - Loads and renders the current user in the sidebar footer
 */

import { getCurrentUser } from "./data-service.js";

/* ------------------------------------------------------------------ */
/*  ICONS (inline SVG, Lucide-style stroked icons)                     */
/* ------------------------------------------------------------------ */
const icons = {
  logo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 0 1 10 10"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/></svg>`,
  dashboard: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>`,
  patients: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  admin: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>`,
  audit: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>`,
  logout: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
  menu: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`,
};

const NAV_LINKS = [
  { href: "dashboard.html", label: "Dashboard",       icon: "dashboard" },
  { href: "upload.html",    label: "Upload & Predict", icon: "upload" },
  { href: "patients.html",  label: "Patients",         icon: "patients" },
  { href: "admin.html",     label: "Administration",   icon: "admin" },
  { href: "audit.html",     label: "Audit Log",        icon: "audit" },
];

function roleLabel(role) {
  const map = {
    admin:                "Administrator",
    dermatologist:        "Dermatologist",
    general_practitioner: "General Practitioner",
    nurse:                "Nurse",
  };
  return map[role] || role;
}

function initials(name) {
  return name.split(" ").filter(Boolean).map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

function currentPage() {
  return window.location.pathname.split("/").pop() || "index.html";
}

function buildSidebar(user) {
  const page = currentPage();
  const navItems = NAV_LINKS.map(link => {
    const active = page === link.href ? "active" : "";
    return `<a href="${link.href}" class="nav-item ${active}" aria-current="${active ? "page" : "false"}">
      ${icons[link.icon]}
      <span>${link.label}</span>
    </a>`;
  }).join("");

  return `
    <aside class="sidebar" id="sidebar" role="navigation" aria-label="Main navigation">
      <div class="sidebar-header">
        <div class="sidebar-logo">${icons.logo}</div>
        <div class="sidebar-brand">
          <span class="sidebar-brand-name">DermisAI</span>
          <span class="sidebar-brand-sub">Clinical Detection</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">
          <span class="nav-section-label">Navigation</span>
        </div>
        ${navItems}
      </nav>
      <div class="sidebar-footer">
        <div class="sidebar-user">
          <div class="user-avatar" aria-hidden="true">${initials(user.name)}</div>
          <div class="user-info">
            <div class="user-name">${user.name}</div>
            <div class="user-role">${roleLabel(user.role)}</div>
          </div>
        </div>
        <a href="index.html" class="btn-logout">
          ${icons.logout}
          <span>Sign out</span>
        </a>
      </div>
    </aside>
    <div class="sidebar-overlay" id="sidebarOverlay" aria-hidden="true"></div>
  `;
}

function buildMobileHeader() {
  const page = currentPage();
  const link = NAV_LINKS.find(l => l.href === page);
  const label = link ? link.label : "DermisAI";
  return `
    <header class="mobile-header" role="banner">
      <div class="mobile-header-brand">
        ${icons.logo}
        <span>${label}</span>
      </div>
      <button class="mobile-menu-btn" id="mobileMenuBtn" aria-label="Open navigation menu" aria-expanded="false" aria-controls="sidebar">
        ${icons.menu}
      </button>
    </header>
  `;
}

function attachMobileHandlers() {
  const btn     = document.getElementById("mobileMenuBtn");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");

  if (!btn || !sidebar || !overlay) return;

  function openSidebar() {
    sidebar.classList.add("open");
    overlay.classList.add("active");
    btn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    sidebar.classList.remove("open");
    overlay.classList.remove("active");
    btn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  btn.addEventListener("click", openSidebar);
  overlay.addEventListener("click", closeSidebar);

  // close on Escape
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && sidebar.classList.contains("open")) closeSidebar();
  });
}

/**
 * initNav()
 * Call once at the top of each authenticated page script.
 * Injects the sidebar + mobile header into #navMount or before #mainContent.
 */
export async function initNav() {
  let user;
  try {
    user = await getCurrentUser();
  } catch {
    user = { name: "Unknown User", role: "nurse", email: "" };
  }

  // Find mount point or prepend to app-layout
  const mount = document.getElementById("navMount");
  const appLayout = document.querySelector(".app-layout");

  if (mount) {
    mount.innerHTML = buildSidebar(user) + buildMobileHeader();
  } else if (appLayout) {
    appLayout.insertAdjacentHTML("afterbegin", buildSidebar(user) + buildMobileHeader());
  }

  // The mobile header must be outside the app-layout for sticky positioning
  const mobileHeader = document.querySelector(".mobile-header");
  if (mobileHeader && appLayout && appLayout.contains(mobileHeader)) {
    appLayout.parentNode.insertBefore(mobileHeader, appLayout);
  }

  attachMobileHandlers();
  return user;
}

/* ------------------------------------------------------------------ */
/*  Shared UI helpers available to all pages                           */
/* ------------------------------------------------------------------ */

/** Render a loading skeleton into a container */
export function renderLoading(container, rows = 5, cols = 5) {
  if (!container) return;
  container.innerHTML = Array.from({ length: rows }, () => `
    <tr class="skeleton-row">
      ${Array.from({ length: cols }, () => `<td><div class="skeleton skeleton-text" style="width:${60 + Math.random()*30}%"></div></td>`).join("")}
    </tr>
  `).join("");
}

/** Render an empty state into a container */
export function renderEmpty(container, message = "No records found.", description = "Try adjusting your search or filters.") {
  if (!container) return;
  const isTable = container.tagName === "TBODY";
  const colSpan = container.closest("table")?.querySelectorAll("th").length || 6;
  const html = `
    <div class="state-container">
      <div class="state-icon empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </div>
      <p class="state-title">${message}</p>
      <p class="state-description">${description}</p>
    </div>`;
  if (isTable) {
    container.innerHTML = `<tr><td colspan="${colSpan}">${html}</td></tr>`;
  } else {
    container.innerHTML = html;
  }
}

/** Render an error state into a container */
export function renderError(container, message = "Something went wrong.", retryFn = null) {
  if (!container) return;
  const isTable = container.tagName === "TBODY";
  const colSpan = container.closest("table")?.querySelectorAll("th").length || 6;
  const retryBtn = retryFn ? `<button class="btn btn-secondary btn-sm" id="retryBtn">Retry</button>` : "";
  const html = `
    <div class="state-container">
      <div class="state-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <p class="state-title">Unable to load data</p>
      <p class="state-description">${message}</p>
      ${retryBtn}
    </div>`;
  if (isTable) {
    container.innerHTML = `<tr><td colspan="${colSpan}">${html}</td></tr>`;
  } else {
    container.innerHTML = html;
  }
  if (retryFn) {
    container.querySelector("#retryBtn")?.addEventListener("click", retryFn);
  }
}

/** Format ISO timestamp to locale string */
export function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/** Debounce helper for search inputs */
export function debounce(fn, delay = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

/** Render pagination controls */
export function renderPagination(container, { total, page, perPage, totalPages }, onPageChange) {
  if (!container) return;
  const start = (page - 1) * perPage + 1;
  const end   = Math.min(page * perPage, total);

  let pages = "";
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
      pages += `<button class="page-btn ${i === page ? "active" : ""}" data-page="${i}">${i}</button>`;
    } else if (i === page - 2 || i === page + 2) {
      pages += `<span style="color:var(--color-text-muted);padding:0 4px">…</span>`;
    }
  }

  container.innerHTML = `
    <div class="pagination-info">Showing ${start}–${end} of ${total} records</div>
    <div class="pagination-controls">
      <button class="page-btn" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""} aria-label="Previous page">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      ${pages}
      <button class="page-btn" data-page="${page + 1}" ${page >= totalPages ? "disabled" : ""} aria-label="Next page">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>
  `;

  container.querySelectorAll(".page-btn:not([disabled])").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = parseInt(btn.dataset.page, 10);
      if (p && p !== page) onPageChange(p);
    });
  });
}
