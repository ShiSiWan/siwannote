<template>
  <div
    class="relative min-h-screen w-full bg-theme-background text-theme-text overflow-x-hidden"
  >
    <!-- Left Sidebar (Document Directory & Outline) -->
    <Sidebar v-if="showSidebar" />

    <!-- Main Content Area (Push layout using margin-left on PC, perfectly centered in remaining space) -->
    <main
      class="app-main-container flex min-h-screen min-w-0 flex-1 flex-col print:pt-0"
      :style="mainLayoutStyle"
      :class="isDraggingSidebar ? 'transition-none' : 'transition-[margin-left,width] duration-200 ease-out'"
    >
      <LoadingIndicator
        ref="loadingIndicator"
        class="flex w-full flex-1 flex-col"
      >
        <div
          data-app-content
          class="mx-auto flex w-full flex-1 flex-col px-4 sm:px-6 lg:px-6 py-4 pt-16 md:pt-6 print:max-w-full print:px-0 transition-all duration-200"
          :style="{ maxWidth: pageWidth }"
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
        </div>
      </LoadingIndicator>
    </main>

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

    <!-- Persistent Top-Right Controls -->
    <div
      v-if="showTopRightControls"
      class="fixed right-3 sm:right-5 top-3 z-40 flex items-center gap-1.5 sm:gap-2 print:hidden"
    >
      <button
        v-if="isAdmin"
        class="flex items-center justify-center rounded-xl border border-indigo-500/30 bg-theme-background-elevated/90 w-9 h-9 text-indigo-500 shadow-md backdrop-blur-md transition hover:bg-indigo-500 hover:text-white dark:bg-slate-800/90"
        title="打开 AI 智能助手"
        @click="toggleAiPanel"
      >
        <KeylineIcon name="sparkles" size="16" strokeWidth="2" />
      </button>

      <button
        class="flex items-center justify-center rounded-xl border border-theme-border bg-theme-background-elevated/90 w-9 h-9 text-theme-text shadow-md backdrop-blur-md transition hover:border-theme-brand hover:text-theme-brand dark:bg-slate-800/90"
        title="打开设置中心"
        @click="openSettings"
      >
        <KeylineIcon name="settings" size="16" strokeWidth="2" />
      </button>
    </div>
  </div>
</template>

<script setup>
import Mousetrap from "mousetrap";
import "mousetrap/plugins/global-bind/mousetrap-global-bind";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
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

const isDesktopMode = ref(typeof window !== "undefined" ? window.innerWidth >= 1024 : true);
const isDraggingSidebar = ref(false);

const mainLayoutStyle = computed(() => {
  if (isDesktopMode.value && showSidebar.value && globalStore.isSidebarOpen) {
    return {
      marginLeft: `${globalStore.sidebarWidth}px`,
      width: `calc(100% - ${globalStore.sidebarWidth}px)`,
    };
  }
  return {
    marginLeft: "0px",
    width: "100%",
  };
});

function handleWindowResize() {
  isDesktopMode.value = window.innerWidth >= 1024;
}

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

// Reactive page width (synced with SettingsPanel's siwan_page_width setting)
function normalizePageWidth(w) {
  if (w === "100%") return "100%";
  if (w === "1024px" || w === "1120px" || w === "1180px") return "1180px";
  return "1440px";
}

const pageWidth = ref(normalizePageWidth(localStorage.getItem("siwan_page_width")));

function syncPageWidth(event) {
  pageWidth.value = normalizePageWidth(event?.detail || localStorage.getItem("siwan_page_width"));
}

onMounted(() => {
  checkAdmin();
  globalStore.loadSiteBranding();
  window.addEventListener("resize", handleWindowResize);
  window.addEventListener("siwan-auth-changed", checkAdmin);
  window.addEventListener("siwan-open-search", toggleSearchModal);
  window.addEventListener("siwan-page-width-changed", syncPageWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleWindowResize);
  window.removeEventListener("siwan-auth-changed", checkAdmin);
  window.removeEventListener("siwan-open-search", toggleSearchModal);
  window.removeEventListener("siwan-page-width-changed", syncPageWidth);
});

loadTheme();
</script>

<style>
/* Printing: ignore the responsive page-width maxWidth set via inline style */
@media print {
  [data-app-content] {
    max-width: none !important;
  }
}
</style>
