<template>
  <div
    v-if="isVisible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in"
  >
    <div
      class="relative w-full max-w-lg rounded-2xl border border-theme-border bg-theme-background p-6 shadow-2xl transition-all duration-300"
    >
      <!-- Brand Header -->
      <div class="mb-5 flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/10 text-theme-brand border border-orange-500/20">
          <KeylineIcon name="sun" size="20" />
        </div>
        <div>
          <h2 class="text-lg font-bold text-theme-text">欢迎使用 SiWan_notes</h2>
          <p class="text-xs text-theme-text-muted mt-0.5">请选择您初次访问的偏好主题风格</p>
        </div>
      </div>

      <!-- Theme Cards Selection -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        <!-- Light Theme -->
        <button
          type="button"
          class="flex flex-col items-center rounded-xl border p-3.5 text-center transition-all duration-200"
          :class="currentTheme === 'light' ? 'border-theme-brand bg-orange-500/10 ring-2 ring-orange-500/20 shadow-sm' : 'border-theme-border bg-theme-background-elevated/40 hover:border-theme-text-muted'"
          @click="selectTheme('light')"
        >
          <div class="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-700 shadow-sm border border-slate-200">
            <KeylineIcon name="sun" size="18" />
          </div>
          <span class="text-xs font-bold text-theme-text">浅色模式</span>
          <span class="text-[11px] text-theme-text-muted mt-0.5">明亮清爽</span>
        </button>

        <!-- Eye-Care Theme -->
        <button
          type="button"
          class="flex flex-col items-center rounded-xl border p-3.5 text-center transition-all duration-200"
          :class="currentTheme === 'eye-care' ? 'border-theme-brand bg-amber-500/15 ring-2 ring-amber-500/30 shadow-sm' : 'border-theme-border bg-theme-background-elevated/40 hover:border-theme-text-muted'"
          @click="selectTheme('eye-care')"
        >
          <div class="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-[#ede7dc] text-[#5c4a32] shadow-sm border border-[#dcd3c3]">
            <KeylineIcon name="eye" size="18" />
          </div>
          <div class="flex items-center gap-1">
            <span class="text-xs font-bold text-theme-text">柔和护眼</span>
            <span class="rounded bg-amber-500/20 px-1 py-0.2 text-[9px] font-bold text-amber-700 dark:text-amber-300">推荐</span>
          </div>
          <span class="text-[11px] text-theme-text-muted mt-0.5">温润纸感久看舒适</span>
        </button>

        <!-- Dark Theme -->
        <button
          type="button"
          class="flex flex-col items-center rounded-xl border p-3.5 text-center transition-all duration-200"
          :class="currentTheme === 'dark' ? 'border-theme-brand bg-indigo-500/10 ring-2 ring-indigo-500/20 shadow-sm' : 'border-theme-border bg-theme-background-elevated/40 hover:border-theme-text-muted'"
          @click="selectTheme('dark')"
        >
          <div class="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-amber-400 shadow-sm border border-slate-700">
            <KeylineIcon name="moon" size="18" />
          </div>
          <span class="text-xs font-bold text-theme-text">深色模式</span>
          <span class="text-[11px] text-theme-text-muted mt-0.5">极客暗调夜间护眼</span>
        </button>
      </div>

      <!-- Reminder Notice -->
      <div class="mb-6 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
        <span class="text-sm shrink-0">💡</span>
        <div class="leading-relaxed">
          <strong class="font-semibold">无需担心：</strong>
          后续您可以随时在右上角 <span class="font-mono font-bold text-theme-brand">设置 (⚙️)</span> 中随意切换主题、配置 AI 助手以及调整页面布局宽度。
        </div>
      </div>

      <!-- Confirm Button -->
      <div class="flex justify-end">
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl bg-theme-brand px-6 py-2.5 text-xs font-bold text-white shadow-md shadow-orange-500/20 transition-all hover:bg-orange-600 active:scale-95 flex items-center justify-center gap-2"
          @click="confirmSelection"
        >
          <KeylineIcon name="check" size="15" />
          <span>开始使用 SiWan_notes</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import KeylineIcon from "./KeylineIcon.vue";
import { applyTheme, getSavedTheme } from "../helpers.js";

const isVisible = ref(false);
const currentTheme = ref("eye-care");

onMounted(() => {
  const initialized = localStorage.getItem("siwan_theme_initialized");
  if (!initialized) {
    const saved = getSavedTheme();
    currentTheme.value = saved || "eye-care";
    // Apply initial preview
    applyTheme(currentTheme.value);
    isVisible.value = true;
  }
});

function selectTheme(theme) {
  currentTheme.value = theme;
  applyTheme(theme);
}

function confirmSelection() {
  localStorage.setItem("siwan_theme_initialized", "true");
  applyTheme(currentTheme.value);
  isVisible.value = false;
}
</script>
