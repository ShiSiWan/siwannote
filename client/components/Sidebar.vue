<template>
  <div>
    <!-- Mobile Backdrop -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
      @click="toggleSidebar"
    ></div>

    <!-- 页面左侧上方快捷入口：显示（边栏，搜索，新文本） -->
    <div
      v-if="!isOpen"
      class="fixed left-3 sm:left-5 top-3 z-40 flex items-center rounded-xl border border-theme-border bg-theme-background-elevated/90 p-1 shadow-md backdrop-blur-md transition-all dark:bg-slate-800/90"
    >
      <button
        class="flex items-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-2.5 py-1.5 text-xs font-semibold text-theme-text transition hover:bg-theme-background hover:text-theme-brand"
        title="展开边栏 (文档列表与大纲)"
        @click="toggleSidebar"
      >
        <KeylineIcon name="book-open" size="14" strokeWidth="2.2" />
        <span class="hidden sm:inline">边栏</span>
      </button>

      <button
        class="flex items-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-2.5 py-1.5 text-xs font-semibold text-theme-text transition hover:bg-theme-background hover:text-theme-brand border-l border-theme-border/60"
        title="全局搜索 (/)"
        @click="triggerSearch"
      >
        <KeylineIcon name="search" size="14" strokeWidth="2" />
        <span class="hidden sm:inline">搜索</span>
      </button>

      <button
        class="flex items-center gap-1 sm:gap-1.5 rounded-lg px-2 sm:px-2.5 py-1.5 text-xs font-semibold text-theme-text transition hover:bg-theme-background hover:text-theme-brand border-l border-theme-border/60"
        title="创建新文本"
        @click="triggerNewNote"
      >
        <KeylineIcon name="plus" size="14" strokeWidth="2.2" />
        <span class="hidden sm:inline">新文本</span>
      </button>
    </div>

    <!-- Sidebar Container -->
    <aside
      class="fixed bottom-0 left-0 top-0 z-50 flex w-[305px] max-w-[85vw] flex-col border-r border-theme-border bg-theme-background shadow-2xl transition-transform duration-200 ease-in-out dark:bg-slate-900"
      :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- 边栏顶部控制区：分两行 -->
      <div class="border-b border-theme-border p-3 space-y-2 bg-theme-background-elevated/30">
        <!-- 第一行：主页，搜索，边栏 (关闭) -->
        <div class="flex items-center gap-1.5">
          <button
            class="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-theme-border bg-theme-background py-1.5 text-xs font-semibold text-theme-text shadow-sm transition hover:border-theme-brand hover:text-theme-brand"
            title="返回主页"
            @click="goHome"
          >
            <KeylineIcon name="home" size="13" strokeWidth="2" />
            <span>主页</span>
          </button>

          <button
            class="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-theme-border bg-theme-background py-1.5 text-xs font-semibold text-theme-text shadow-sm transition hover:border-theme-brand hover:text-theme-brand"
            title="全局内容搜索 (/)"
            @click="triggerSearch"
          >
            <KeylineIcon name="search" size="13" strokeWidth="2" />
            <span>搜索</span>
          </button>

          <button
            class="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-theme-brand/40 bg-theme-brand/10 py-1.5 text-xs font-semibold text-theme-brand shadow-sm transition hover:bg-theme-brand hover:text-white"
            title="关闭收起边栏"
            @click="toggleSidebar"
          >
            <KeylineIcon name="book-open" size="13" strokeWidth="2" />
            <span>边栏</span>
          </button>
        </div>

        <!-- 第二行：新文本 -->
        <button
          class="w-full flex items-center justify-center gap-2 rounded-lg bg-theme-brand py-2 text-xs font-bold text-white shadow-sm hover:bg-orange-600 active:scale-95 transition"
          title="创建新文本"
          @click="triggerNewNote"
        >
          <KeylineIcon name="plus" size="14" strokeWidth="2.5" />
          <span>新文本</span>
        </button>
      </div>

      <!-- Tabs Header -->
      <div class="flex border-b border-theme-border bg-theme-background-elevated/40 p-1.5 gap-1.5">
        <button
          class="flex-1 rounded-md py-1.5 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="activeTab === 'files' ? 'bg-theme-brand text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="switchTab('files')"
        >
          <KeylineIcon name="file-text" size="13" />
          <span>文档列表 ({{ filteredNotes.length }})</span>
        </button>
        <button
          class="flex-1 rounded-md py-1.5 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="activeTab === 'toc' ? 'bg-theme-brand text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="switchTab('toc')"
        >
          <KeylineIcon name="list-tree" size="13" />
          <span>章节大纲</span>
        </button>
      </div>

      <!-- Panel 1: Document List (以实际数据库目录中的文件为准) -->
      <div v-show="activeTab === 'files'" class="flex flex-1 flex-col overflow-hidden p-2.5">
        <!-- Search filter input -->
        <div class="relative mb-2">
          <KeylineIcon name="search" size="13" className="absolute left-2.5 top-1/2 -translate-y-1/2 opacity-60 text-theme-text-muted" />
          <input
            v-model="fileFilter"
            type="text"
            placeholder="按名称快速筛选文档..."
            class="w-full rounded-md border border-theme-border bg-theme-background-elevated/60 py-1.5 pl-8 pr-2.5 text-xs outline-none transition focus:border-theme-brand text-theme-text"
          />
        </div>

        <!-- Document Flat List Area -->
        <div class="flex-1 overflow-y-auto pr-1 space-y-0.5">
          <div v-if="filteredNotes.length === 0" class="py-8 text-center text-xs text-theme-text-muted">
            {{ fileFilter ? '未匹配到任何文档' : '暂无文档' }}
          </div>

          <div
            v-for="note in filteredNotes"
            :key="note.title"
            class="group flex cursor-pointer items-center justify-between rounded-md px-2.5 py-1.5 text-xs transition hover:bg-theme-background-elevated"
            :class="isActiveNote(note.title) ? 'bg-theme-brand/15 font-semibold text-theme-brand border-l-2 border-theme-brand' : 'text-theme-text-muted hover:text-theme-text'"
            @click="selectNote(note.title)"
          >
            <div class="flex items-center gap-2 overflow-hidden">
              <KeylineIcon name="file-text" size="13" className="shrink-0 opacity-70 group-hover:opacity-100" />
              <span class="truncate leading-snug" :title="note.title">{{ note.title }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel 2: Document Outline (TOC) -->
      <div v-show="activeTab === 'toc'" class="flex flex-1 flex-col overflow-y-auto p-2.5 pr-1.5">
        <div v-if="headings.length === 0" class="py-12 text-center text-xs text-theme-text-muted">
          <span>当前页面无大纲</span>
          <div class="mt-1 text-[11px] opacity-70">打开文档后自动提取层级标题</div>
        </div>

        <div
          v-for="h in headings"
          :key="h.id"
          class="mb-1 block cursor-pointer rounded px-2 py-1.5 text-xs transition hover:bg-theme-background-elevated"
          :class="[
            activeHeadingId === h.id ? 'font-bold text-theme-brand bg-theme-brand/10 border-l-2 border-theme-brand' : 'text-theme-text-muted hover:text-theme-text',
            h.level === 'h1' ? 'font-semibold text-theme-text' : '',
            h.level === 'h2' ? 'pl-4' : '',
            h.level === 'h3' ? 'pl-7 opacity-85 text-[11.5px]' : '',
            h.level === 'h4' ? 'pl-10 opacity-75 text-[11px]' : ''
          ]"
          @click="jumpToHeading(h.id)"
        >
          <span class="truncate block" :title="h.text">{{ h.text }}</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import KeylineIcon from "./KeylineIcon.vue";
import { useGlobalStore } from "../globalStore.js";
import { getNotes, getSecurityStatus } from "../api.js";

const route = useRoute();
const router = useRouter();
const toast = useToast();
const globalStore = useGlobalStore();

const isOpen = ref(false);
const activeTab = ref("files");
const fileFilter = ref("");
const notesList = ref([]);
const headings = ref([]);
const activeHeadingId = ref("");
const isAdmin = ref(false);

const isDesktop = () => window.innerWidth >= 1024;

async function checkAdmin() {
  try {
    const res = await getSecurityStatus();
    isAdmin.value = res.is_admin === true;
  } catch {
    isAdmin.value = false;
  }
}

function goHome() {
  router.push({ name: "home" });
  if (!isDesktop()) {
    toggleSidebar();
  }
}

function triggerSearch() {
  window.dispatchEvent(new CustomEvent("siwan-open-search"));
}

function triggerNewNote() {
  if (isAdmin.value) {
    router.push({ name: "new" });
    if (!isDesktop()) {
      toggleSidebar();
    }
  } else {
    toast.add({
      severity: "warn",
      summary: "访客模式提示",
      detail: "访客模式仅支持浏览与留言，如需创建新文本请在右上角「设置」中登录管理员",
      life: 4000,
    });
    globalStore.isSettingsOpen = true;
  }
}

function onAuthChanged() {
  loadNotes();
  checkAdmin();
}

onMounted(() => {
  const saved = localStorage.getItem("siwan_sidebar_open");
  if (isDesktop() && (saved === "1" || saved === null)) {
    isOpen.value = true;
    updateBodyClass();
  } else {
    isOpen.value = false;
    updateBodyClass();
  }

  loadNotes();
  checkAdmin();

  window.addEventListener("siwan-headings-updated", extractHeadings);
  window.addEventListener("siwan-auth-changed", onAuthChanged);
  window.addEventListener("siwan-storage-changed", loadNotes);
  window.addEventListener("scroll", handleScroll, { passive: true });

  setTimeout(extractHeadings, 300);
});

onBeforeUnmount(() => {
  window.removeEventListener("siwan-headings-updated", extractHeadings);
  window.removeEventListener("siwan-auth-changed", onAuthChanged);
  window.removeEventListener("siwan-storage-changed", loadNotes);
  window.removeEventListener("scroll", handleScroll);
});

watch(
  () => route.fullPath,
  () => {
    setTimeout(extractHeadings, 300);
  }
);

function toggleSidebar() {
  isOpen.value = !isOpen.value;
  localStorage.setItem("siwan_sidebar_open", isOpen.value ? "1" : "0");
  updateBodyClass();
}

function updateBodyClass() {
  if (isOpen.value && isDesktop()) {
    document.body.classList.add("fn-sidebar-open");
  } else {
    document.body.classList.remove("fn-sidebar-open");
  }
}

function switchTab(tab) {
  activeTab.value = tab;
  if (tab === "toc") {
    extractHeadings();
  }
}

async function loadNotes() {
  try {
    const data = await getNotes("*", "title", "asc", 500);
    notesList.value = data.sort((a, b) =>
      a.title.localeCompare(b.title, "zh-Hans-CN", { numeric: true, sensitivity: "base" })
    );
  } catch (err) {
    console.warn("[Sidebar] Failed to load notes:", err);
  }
}

const filteredNotes = computed(() => {
  const term = fileFilter.value.trim().toLowerCase();
  if (!term) return notesList.value;
  return notesList.value.filter((n) => n.title.toLowerCase().includes(term));
});

function isActiveNote(title) {
  return route.name === "note" && route.params.title === title;
}

function selectNote(title) {
  router.push({ name: "note", params: { title } });
  if (!isDesktop()) {
    toggleSidebar();
  }
}

function extractHeadings() {
  const container = document.querySelector(".toast-viewer .toastui-editor-contents");
  if (!container) {
    headings.value = [];
    return;
  }

  const elements = container.querySelectorAll("h1, h2, h3, h4");
  const result = [];

  elements.forEach((el, index) => {
    const text = el.textContent.trim();
    if (!text) return;
    if (!el.id) {
      el.id = `heading-section-${index}`;
    }
    result.push({
      id: el.id,
      text: text,
      level: el.tagName.toLowerCase(),
      top: el.offsetTop,
    });
  });

  headings.value = result;
}

function jumpToHeading(id) {
  const target = document.getElementById(id);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    activeHeadingId.value = id;
    if (!isDesktop()) {
      toggleSidebar();
    }
  }
}

let scrollTimer = null;
function handleScroll() {
  if (scrollTimer) return;
  scrollTimer = setTimeout(() => {
    scrollTimer = null;
    if (headings.value.length === 0) return;
    const scrollPos = window.scrollY + 100;
    let current = headings.value[0]?.id;
    for (const h of headings.value) {
      const el = document.getElementById(h.id);
      if (el && el.offsetTop <= scrollPos) {
        current = h.id;
      } else {
        break;
      }
    }
    if (current) {
      activeHeadingId.value = current;
    }
  }, 100);
}
</script>
