/* HEMS-Link Global Shell Helpers (Theme, Role, i18n, Reset) */

const HEMS = {
  getRole() {
    return localStorage.getItem("hems_role") || "coordinator";
  },
  setRole(role) {
    localStorage.setItem("hems_role", role);
  },
  getTheme() {
    return localStorage.getItem("hems_theme") || "light";
  },
  setTheme(theme) {
    localStorage.setItem("hems_theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
  },
  getLang() {
    return localStorage.getItem("hems_lang") || "en";
  },
  setLang(lang) {
    localStorage.setItem("hems_lang", lang);
    const dict = (window.HEMS_I18N && window.HEMS_I18N[lang]) || window.HEMS_I18N.en;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });
  },
  async api(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      "X-Role": this.getRole(),
      ...(options.headers || {}),
    };
    const res = await fetch(path, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  },
  async resetDemo() {
    await this.api("/api/reset", { method: "POST" });
    window.location.reload();
  },
};

document.addEventListener("DOMContentLoaded", () => {
  HEMS.setTheme(HEMS.getTheme());
  HEMS.setLang(HEMS.getLang());

  const roleSelect = document.getElementById("role-select");
  if (roleSelect) {
    roleSelect.value = HEMS.getRole();
    roleSelect.addEventListener("change", (e) => HEMS.setRole(e.target.value));
  }

  const langSelect = document.getElementById("lang-select");
  if (langSelect) {
    langSelect.value = HEMS.getLang();
    langSelect.addEventListener("change", (e) => HEMS.setLang(e.target.value));
  }

  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const next = HEMS.getTheme() === "dark" ? "light" : "dark";
      HEMS.setTheme(next);
      themeBtn.textContent = next === "dark" ? "☀ Light" : "☾ Dark";
    });
    themeBtn.textContent = HEMS.getTheme() === "dark" ? "☀ Light" : "☾ Dark";
  }
});

