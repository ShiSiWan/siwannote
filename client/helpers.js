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

export function formatRelativeTime(isoOrTimestamp) {
  if (!isoOrTimestamp) return "";
  const date = typeof isoOrTimestamp === "number"
    ? new Date(isoOrTimestamp * 1000)
    : new Date(isoOrTimestamp);
  if (isNaN(date.getTime())) return String(isoOrTimestamp);

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  if (diffMs < 0) return "刚刚";
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 45) return "刚刚";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} 分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小时前`;
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay < 30) return `${diffDay} 天前`;
  const diffMonth = Math.floor(diffDay / 30);
  if (diffMonth < 12) return `${diffMonth} 个月前`;
  return `${Math.floor(diffDay / 365)} 年前`;
}

export function formatAbsoluteTime(isoOrTimestamp) {
  if (!isoOrTimestamp) return "";
  const date = typeof isoOrTimestamp === "number"
    ? new Date(isoOrTimestamp * 1000)
    : new Date(isoOrTimestamp);
  if (isNaN(date.getTime())) return String(isoOrTimestamp);
  return date.toLocaleString("zh-CN", { hour12: false });
}
