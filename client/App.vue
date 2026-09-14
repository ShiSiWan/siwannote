<template>
  <div class="relative min-h-screen">
    <!-- Left Sidebar (Document Directory & Outline) -->
    <Sidebar v-if="showSidebar" />

    <!-- Right AI Assistant Drawer (Only for Admin, 访客不加载) -->
    <AiPanel
      v-if="showAiPanel && isAdmin"
      :current-doc-title="globalStore.currentDocTitle"
      :current-doc-content="globalStore.currentDocContent"
      @open-config="globalStore.isSettingsOpen = true"
    />

    <!-- Right Settings Drawer (Replaces Menu & Modal) -->
    <SettingsPanel
      v-model="globalStore.isSettingsOpen"
      @toggle-search-modal="toggleSearchModal"
    />

    <!-- First-Time Theme Onboarding Modal -->
    <ThemeOnboardingModal />

    <!-- Persistent Top-Right Controls (设置始终显示在右上角，访客页面不显示AI) -->
    <div
      v-if="showTopRightControls"
      class="fixed right-3 sm:right-5 top-3 z-40 flex items-center gap-1.5 sm:gap-2 print:hidden"
    >
      <!-- AI Assistant Button (Admin Only: 访客不显示) -->
      <button
        v-if="isAdmin"
        class="flex items-center gap-1 sm:gap-1.5 rounded-xl border border-indigo-500/30 bg-theme-background-elevated/90 px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-indigo-500 shadow-md backdrop-blur-md transition hover:bg-indigo-500 hover:text-white dark:bg-slate-800/90"
        title="打开 AI 智能助手"
        @click="toggleAiPanel"
      >
        <KeylineIcon name="sparkles" size="14" strokeWidth="2" />
        <span class="hidden sm:inline">AI 助手</span>
      </button>

      <!-- Settings Button (始终显示在右上角) -->
      <button
        class="flex items-center gap-1 sm:gap-1.5 rounded-xl border border-theme-border bg-theme-background-elevated/90 px-2.5 sm:px-3.5 py-1.5 text-xs font-semibold text-theme-text shadow-md backdrop-blur-md transition hover:border-theme-brand hover:text-theme-brand dark:bg-slate-800/90"
        title="打开设置中心"
        @click="openSettings"
      >
        <KeylineIcon name="settings" size="14" strokeWidth="2" />
        <span class="hidden sm:inline">设置</span>
      </button>
    </div>

    <LoadingIndicator
      ref="loadingIndicator"
      class="app-main-container container mx-auto flex min-h-screen flex-col px-3.5 sm:px-6 py-3 pt-16 md:pt-4 print:pt-0 print:max-w-full transition-all duration-200"
    >
      <PrimeToast />
      <SearchModal v-model="isSearchModalVisible" />
      <NavBar
        v-if="showNavBar"
        ref="navBar"
        :class="{ 'print:hidden': route.name == 'note' }"
        :hide-logo="!showNavBarLogo"
        @toggleSearchModal="toggleSearchModal"
      />
      <RouterView />
    </LoadingIndicator>
  </div>
</template>

<script setup>
import Mousetrap from "mousetrap";
import "mousetrap/plugins/global-bind/mousetrap-global-bind";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref } from "vue";
import { RouterView, useRoute } from "vue-router";

import { apiErrorHandler, getConfig, getSecurityStatus } from "./api.js";
import PrimeToast from "./components/PrimeToast.vue";
import { useGlobalStore } from "./globalStore.js";
import { loadTheme } from "./helpers.js";
import KeylineIcon from "./components/KeylineIcon.vue";
import NavBar from "./partials/NavBar.vue";
import SearchModal from "./partials/SearchModal.vue";
import LoadingIndicator from "./components/LoadingIndicator.vue";
import Sidebar from "./components/Sidebar.vue";
import AiPanel from "./components/AiPanel.vue";
import SettingsPanel from "./components/SettingsPanel.vue";
import ThemeOnboardingModal from "./components/ThemeOnboardingModal.vue";
import router from "./router.js";

const globalStore = useGlobalStore();
const isSearchModalVisible = ref(false);
const loadingIndicator = ref();
const navBar = ref();
const route = useRoute();
const toast = useToast();
const isAdmin = ref(false);

async function checkAdmin() {
  try {
    const res = await getSecurityStatus();
    isAdmin.value = res.is_admin === true;
  } catch {
    isAdmin.value = false;
  }
}

function openSettings() {
  globalStore.isSettingsOpen = true;
}

function toggleAiPanel() {
  globalStore.isAiPanelOpen = !globalStore.isAiPanelOpen;
}

// '/' to search
Mousetrap.bind("/", () => {
  if (route.name !== "login") {
    toggleSearchModal();
    return false;
  }
});

// 'CTRL + ALT/OPT + N' to create new note
Mousetrap.bindGlobal("ctrl+alt+n", () => {
  if (route.name !== "login") {
    if (isAdmin.value) {
      router.push({ name: "new" });
    } else {
      toast.add({
        severity: "warn",
        summary: "访客模式提示",
        detail: "访客模式仅支持浏览与留言，如需创建新文本请在右上角「设置」中登录管理员",
        life: 4000,
      });
      globalStore.isSettingsOpen = true;
    }
    return false;
  }
});

// 'CTRL + ALT/OPT + H' to go to home
Mousetrap.bindGlobal("ctrl+alt+h", () => {
  if (route.name !== "login") {
    router.push({ name: "home" });
    return false;
  }
});

getConfig()
  .then((data) => {
    globalStore.config = data;
    loadingIndicator.value.setLoaded();
  })
  .catch((error) => {
    apiErrorHandler(error, toast);
    loadingIndicator.value.setFailed();
  });

const showTopRightControls = computed(() => {
  return route.name !== "login";
});

const showNavBar = computed(() => {
  return route.name !== "login";
});

const showNavBarLogo = computed(() => {
  return route.name !== "home";
});

const showSidebar = computed(() => {
  return route.name !== "login";
});

const showAiPanel = computed(() => {
  return route.name !== "login";
});

function toggleSearchModal() {
  isSearchModalVisible.value = !isSearchModalVisible.value;
}

onMounted(() => {
  checkAdmin();
  globalStore.loadSiteBranding();
  window.addEventListener("siwan-auth-changed", checkAdmin);
  window.addEventListener("siwan-open-search", toggleSearchModal);

  function updateResponsiveWidth() {
    const el = document.querySelector(".app-main-container");
    if (el) {
      if (window.innerWidth < 1024) {
        el.style.maxWidth = "100%";
      } else {
        el.style.maxWidth = localStorage.getItem("siwan_page_width") || "1280px";
      }
    }
  }

  updateResponsiveWidth();
  window.addEventListener("resize", updateResponsiveWidth);
});

loadTheme();
</script>

<style>
@media (min-width: 1024px) {
  body.fn-sidebar-open .app-main-container {
    padding-left: 295px;
  }
}
</style>
