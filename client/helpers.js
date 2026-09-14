export function getToastOptions(description, title, severity) {
  return {
    summary: title,
    detail: description,
    severity: severity,
    closable: false,
    life: 5000,
  };
}

export function applyTheme(theme, save = true) {
  const root = document.documentElement;
  const body = document.body;

  root.classList.remove("dark", "eye-care");
  body.classList.remove("dark", "eye-care");

  let actual = theme;
  if (theme === "system") {
    actual = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  if (actual === "dark") {
    root.classList.add("dark");
    body.classList.add("dark");
  } else if (actual === "eye-care") {
    root.classList.add("eye-care");
    body.classList.add("eye-care");
  }

  if (save) {
    localStorage.setItem("siwan_theme", theme);
  }
}

export function getSavedTheme() {
  return localStorage.getItem("siwan_theme") || localStorage.getItem("theme") || "eye-care";
}

export function loadTheme() {
  const storedTheme = getSavedTheme();
  if (storedTheme) {
    applyTheme(storedTheme, false);
  } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    applyTheme("dark", false);
  } else {
    applyTheme("light", false);
  }
}
