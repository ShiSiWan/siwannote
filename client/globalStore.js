import { defineStore } from "pinia";
import { ref } from "vue";
import { getSiteConfig } from "./api.js";

export const useGlobalStore = defineStore("global", () => {
  const config = ref({});
  const currentDocTitle = ref("");
  const currentDocContent = ref("");
  const isSettingsOpen = ref(false);
  const isAiPanelOpen = ref(false);
  
  // Custom Site Branding
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
    siteTitle,
    siteSubtitle,
    loadSiteBranding,
    setSiteBranding,
  };
});
