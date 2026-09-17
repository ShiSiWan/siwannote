import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { getSiteConfig } from "./api.js";

export const useGlobalStore = defineStore("global", () => {
  const config = ref({});
  const currentDocTitle = ref("");
  const currentDocContent = ref("");
  const isSettingsOpen = ref(false);
  const isAiPanelOpen = ref(false);
  const isAnnotationPanelOpen = ref(false);

  // App Modes: "reading" (阅读模式) vs "creation" (创作模式)
  const currentMode = ref("reading");
  // Creation Mode Sub-views: "source" (源码视图) vs "preview" (预览视图)
  const creationSubView = ref(localStorage.getItem("siwan_creation_subview") || "source");

  // Sidebar Push State (DeepSeek style, mode-specific width)
  const isDesktop = typeof window !== "undefined" ? window.innerWidth >= 1024 : true;
  const initialSidebarOpen = isDesktop
    ? localStorage.getItem("siwan_sidebar_open") !== "0"
    : false;
  const isSidebarOpen = ref(initialSidebarOpen);

  const sidebarWidth = ref(
    Math.min(
      Math.max(
        parseInt(
          localStorage.getItem("siwan_sidebar_width") ||
            localStorage.getItem("siwan_sidebar_width_reading")
        ) || 280,
        200
      ),
      520
    )
  );

  const isAiScanning = ref(false);
  const aiScanningTitle = ref("");

  function toggleSidebar() {
    isSidebarOpen.value = !isSidebarOpen.value;
    localStorage.setItem("siwan_sidebar_open", isSidebarOpen.value ? "1" : "0");
    window.dispatchEvent(
      new CustomEvent("siwan-sidebar-toggle", {
        detail: { isOpen: isSidebarOpen.value, width: sidebarWidth.value },
      })
    );
  }

  function setSidebarWidth(width) {
    const clamped = Math.min(Math.max(width, 200), 520);
    sidebarWidth.value = clamped;
    localStorage.setItem("siwan_sidebar_width", String(clamped));
  }

  function setCreationSubView(view) {
    creationSubView.value = view;
    localStorage.setItem("siwan_creation_subview", view);
  }
  const siteTitle = ref(localStorage.getItem("siwan_site_title") || "siwannote");
  const siteSubtitle = ref(localStorage.getItem("siwan_site_subtitle") || "SLAM & KNOWLEDGE LAB");

  async function loadSiteBranding() {
    try {
      const res = await getSiteConfig();
      if (res.site_title) {
        siteTitle.value = res.site_title;
        localStorage.setItem("siwan_site_title", res.site_title);
      }
      if (res.site_subtitle !== undefined) {
        siteSubtitle.value = res.site_subtitle;
        localStorage.setItem("siwan_site_subtitle", res.site_subtitle);
      }
      document.title = siteTitle.value;
    } catch (e) {
      console.warn("[globalStore] Failed to load site branding:", e);
    }
  }

  function setSiteBranding(title, subtitle) {
    siteTitle.value = title || "siwannote";
    siteSubtitle.value = subtitle !== undefined ? subtitle : "";
    localStorage.setItem("siwan_site_title", siteTitle.value);
    localStorage.setItem("siwan_site_subtitle", siteSubtitle.value);
    document.title = siteTitle.value;
  }

  return {
    config,
    currentDocTitle,
    currentDocContent,
    isSettingsOpen,
    isAiPanelOpen,
    isAnnotationPanelOpen,
    currentMode,
    creationSubView,
    setCreationSubView,
    isSidebarOpen,
    sidebarWidth,
    isAiScanning,
    aiScanningTitle,
    toggleSidebar,
    setSidebarWidth,
    siteTitle,
    siteSubtitle,
    loadSiteBranding,
    setSiteBranding,
  };
});
