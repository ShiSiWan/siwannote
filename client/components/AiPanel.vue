<template>
  <div>
    <!-- Mobile Backdrop -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
      @click="togglePanel"
    ></div>

    <!-- AI Panel Drawer -->
    <aside
      class="fixed bottom-0 right-0 top-0 z-50 flex w-full max-w-[440px] sm:w-[390px] flex-col border-l border-theme-border bg-theme-background shadow-2xl transition-transform duration-200 ease-in-out dark:bg-slate-900"
      :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-theme-border px-4 py-3.5">
        <div class="flex items-center gap-2 font-bold text-indigo-500">
          <KeylineIcon name="sparkles" size="18" strokeWidth="2.2" />
          <span class="text-sm tracking-wide text-theme-text">SiWan AI 智能助手</span>
        </div>
        <div class="flex items-center gap-1">
          <button
            class="rounded p-1.5 text-theme-text-muted transition hover:bg-theme-background-elevated hover:text-theme-text"
            title="打开设置与 AI 配置"
            @click="openSettings"
          >
            <KeylineIcon name="settings" size="16" />
          </button>
          <button
            class="rounded p-1.5 text-theme-text-muted transition hover:bg-theme-background-elevated hover:text-theme-text"
            title="收起"
            @click="togglePanel"
          >
            <KeylineIcon name="x" size="16" />
          </button>
        </div>
      </div>

      <!-- Mode Switch Tabs -->
      <div class="flex border-b border-theme-border bg-theme-background-elevated/40 p-1.5 gap-1.5">
        <button
          class="flex-1 rounded-md py-1.5 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="tab === 'summary' ? 'bg-indigo-600 text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="tab = 'summary'"
        >
          <KeylineIcon name="file-text" size="13" />
          <span>文档智能总结</span>
        </button>
        <button
          class="flex-1 rounded-md py-1.5 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="tab === 'chat' ? 'bg-indigo-600 text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="tab = 'chat'"
        >
          <KeylineIcon name="message-square" size="13" />
          <span>上下文对话</span>
        </button>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto p-3 text-xs leading-relaxed">
        <!-- Tab 1: Document Summary -->
        <div v-show="tab === 'summary'">
          <!-- Document Status Card -->
          <div class="mb-3 rounded-lg border border-theme-border bg-theme-background-elevated/50 p-2.5">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-theme-text truncate max-w-[200px]" :title="currentDocTitle">
                {{ currentDocTitle || '未选择文档' }}
              </span>
              <button
                v-if="currentDocTitle"
                class="rounded bg-indigo-600/20 px-2 py-1 text-[11px] font-semibold text-indigo-400 hover:bg-indigo-600/30 flex items-center gap-1"
                :disabled="isLoadingSummary"
                @click="triggerSummarize"
              >
                <KeylineIcon :name="isLoadingSummary ? 'refresh' : 'sparkles'" size="11" :class="isLoadingSummary ? 'animate-spin' : ''" />
                <span>{{ isLoadingSummary ? '生成中...' : '重新生成' }}</span>
              </button>
            </div>
            <div class="mt-1 text-[11px] text-theme-text-muted">
              {{ currentDocContent ? `文档字数约 ${currentDocContent.length} 字` : '请在左侧选择笔记以进行总结' }}
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoadingSummary" class="flex flex-col items-center justify-center py-12 gap-3 text-theme-text-muted">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
            <span class="text-xs">AI 正在解析全文，提炼核心论点与公式...</span>
          </div>

          <!-- Summary Content Display: Pure Preview Mode with Only Copy Button -->
          <div v-else-if="summaryText" class="space-y-3">
            <!-- Header Bar: Model tag + ONLY Copy Button -->
            <div class="flex items-center justify-between border-b border-theme-border pb-2 text-[11px] text-theme-text-muted">
              <span class="rounded bg-indigo-500/10 px-1.5 py-0.5 font-mono text-[10px] text-indigo-400">
                {{ summaryModel || 'AI Model' }}
              </span>
              <button
                class="flex items-center gap-1 rounded border border-theme-border bg-theme-background-elevated px-2.5 py-1 text-xs font-semibold text-theme-text hover:border-indigo-500 hover:text-indigo-500 transition cursor-pointer"
                title="复制总结内容"
                @click="copySummary"
              >
                <KeylineIcon name="copy" size="12" />
                <span>复制</span>
              </button>
            </div>

            <!-- Error Notice Card -->
            <div
              v-if="isSummaryError"
              class="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-500 leading-relaxed whitespace-pre-wrap"
            >
              {{ summaryText }}
            </div>

            <template v-else>
              <!-- Thinking Process Card (Collapsible) -->
              <details
                v-if="thinkingContent"
                class="rounded-lg border border-theme-border bg-theme-background-elevated/70 p-2.5 text-theme-text-muted transition"
              >
                <summary class="cursor-pointer font-semibold text-[11px] text-indigo-500 select-none flex items-center gap-1.5 hover:text-indigo-400">
                  <KeylineIcon name="sparkles" size="12" />
                  <span>深度思考过程 (点击展开/折叠)</span>
                </summary>
                <div class="mt-2 pl-2 border-l-2 border-indigo-500/40 text-[11px] leading-relaxed whitespace-pre-wrap font-mono text-theme-text-muted">
                  {{ thinkingContent }}
                </div>
              </details>

              <!-- Direct Markdown Preview -->
              <div class="ai-summary-container rounded-lg border border-theme-border/60 bg-theme-background p-3">
                <ToastViewer
                  v-if="cleanMarkdownSummary"
                  :key="cleanMarkdownSummary"
                  :initialValue="cleanMarkdownSummary"
                  :enableTocSync="false"
                  class="ai-toast-viewer"
                />
              </div>
            </template>
          </div>

          <!-- Empty State -->
          <div v-else class="py-14 text-center text-theme-text-muted">
            <div class="flex justify-center mb-3">
              <div class="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400">
                <KeylineIcon name="sparkles" size="28" />
              </div>
            </div>
            <p class="font-medium text-theme-text">暂无当前文档总结</p>
            <p class="text-[11px] text-theme-text-muted mt-1">点击下方按钮立即提炼核心要点与公式</p>
            <button
              v-if="currentDocTitle"
              class="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-indigo-700"
              @click="triggerSummarize"
            >
              <KeylineIcon name="sparkles" size="13" />
              <span>一键生成当前文档总结</span>
            </button>
          </div>
        </div>

        <!-- Tab 2: Context-Aware Chat -->
        <div v-show="tab === 'chat'" class="flex h-full flex-col">
          <div class="flex-1 space-y-3 overflow-y-auto pr-1">
            <div v-if="messages.length === 0" class="py-10 text-center text-theme-text-muted">
              <div class="flex justify-center mb-2">
                <div class="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
                  <KeylineIcon name="message-square" size="22" />
                </div>
              </div>
              <p class="font-medium text-theme-text">针对此笔记随时提问</p>
              <p class="text-[11px] opacity-75 mt-1">例如：“解释这篇笔记里提到了哪些核心公式？”</p>
            </div>

            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="rounded-lg p-2.5 text-xs transition"
              :class="msg.role === 'user' ? 'bg-indigo-500/10 border border-indigo-500/30 text-theme-text ml-4' : 'bg-theme-background-elevated border border-theme-border text-theme-text mr-4'"
            >
              <div class="font-bold text-[11px] opacity-75 mb-1 flex items-center justify-between">
                <div class="flex items-center gap-1" :class="msg.role === 'user' ? 'text-indigo-500' : 'text-theme-text-muted'">
                  <KeylineIcon :name="msg.role === 'user' ? 'user' : 'sparkles'" size="11" />
                  <span>{{ msg.role === 'user' ? '您' : 'SiWan AI' }}</span>
                </div>
                <!-- Simple Copy Button for AI replies -->
                <button
                  v-if="msg.role !== 'user'"
                  class="flex items-center gap-1 text-[10px] text-theme-text-muted hover:text-indigo-400 cursor-pointer"
                  title="复制回答内容"
                  @click="copyText(msg.content)"
                >
                  <KeylineIcon name="copy" size="11" />
                  <span>复制</span>
                </button>
              </div>
              <!-- Formatted Preview Rendering -->
              <div class="chat-msg-body leading-relaxed" v-html="formatMessage(msg.content)"></div>
            </div>

            <div v-if="isLoadingChat" class="flex items-center gap-2 text-theme-text-muted p-2">
              <div class="h-3 w-3 animate-spin rounded-full border border-indigo-500 border-t-transparent"></div>
              <span class="text-[11px]">AI 思考中...</span>
            </div>
          </div>

          <!-- Chat Input -->
          <div class="mt-2 border-t border-theme-border pt-2">
            <div class="flex gap-1.5">
              <textarea
                v-model="inputQuery"
                rows="2"
                placeholder="输入问题 (Enter 发送)..."
                class="flex-1 rounded-md border border-theme-border bg-theme-background-elevated/70 p-2 text-xs outline-none focus:border-indigo-500 text-theme-text"
                @keydown.enter.exact.prevent="sendChat"
              ></textarea>
              <button
                class="rounded-md bg-indigo-600 px-3 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                :disabled="!inputQuery.trim() || isLoadingChat"
                @click="sendChat"
              >
                发送
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useToast } from "primevue/usetoast";
import katex from "katex";
import "katex/dist/katex.min.css";
import KeylineIcon from "./KeylineIcon.vue";
import ToastViewer from "./toastui/ToastViewer.vue";
import { useGlobalStore } from "../globalStore.js";
import { getAiConfig, summarizeDocument, chatWithAi } from "../api.js";

const props = defineProps({
  currentDocTitle: {
    type: String,
    default: "",
  },
  currentDocContent: {
    type: String,
    default: "",
  },
});

const globalStore = useGlobalStore();
const toast = useToast();

const isOpen = computed({
  get: () => globalStore.isAiPanelOpen,
  set: (val) => {
    globalStore.isAiPanelOpen = val;
    localStorage.setItem("siwan_aipanel_open", val ? "1" : "0");
  },
});

const tab = ref("summary");

const summaryText = ref("");
const summaryModel = ref("");
const isLoadingSummary = ref(false);

const messages = ref([]);
const inputQuery = ref("");
const isLoadingChat = ref(false);

onMounted(() => {
  const isDesktop = window.innerWidth >= 1024;
  const saved = localStorage.getItem("siwan_aipanel_open");
  if (isDesktop && saved === "1") {
    globalStore.isAiPanelOpen = true;
  } else {
    globalStore.isAiPanelOpen = false;
  }

  // Listen to note saved event
  window.addEventListener("siwan-note-saved", (e) => {
    if (e.detail?.title) {
      checkAndAutoSummarize();
    }
  });
});

watch(
  () => props.currentDocTitle,
  (newTitle) => {
    summaryText.value = "";
    messages.value = [];
    if (newTitle) {
      checkAndAutoSummarize();
    }
  }
);

function togglePanel() {
  isOpen.value = !isOpen.value;
}

function openSettings() {
  globalStore.isSettingsOpen = true;
}

async function checkAndAutoSummarize() {
  try {
    const cfg = await getAiConfig();
    if (cfg?.has_key && cfg?.auto_summarize && props.currentDocContent) {
      triggerSummarize();
    }
  } catch (_) {}
}

async function triggerSummarize() {
  if (!props.currentDocTitle || !props.currentDocContent) return;

  isLoadingSummary.value = true;
  summaryText.value = "";

  try {
    const res = await summarizeDocument(props.currentDocTitle, props.currentDocContent);
    summaryText.value = res.summary;
    summaryModel.value = res.model;
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || "总结失败";
    summaryText.value = `❌ 生成总结出错：${msg}`;
  } finally {
    isLoadingSummary.value = false;
  }
}

const isSummaryError = computed(() => {
  return summaryText.value.startsWith("❌");
});

const thinkingContent = computed(() => {
  if (!summaryText.value || isSummaryError.value) return "";
  const match = summaryText.value.match(/<think>([\s\S]*?)<\/think>/i);
  return match ? match[1].trim() : "";
});

const cleanMarkdownSummary = computed(() => {
  if (!summaryText.value || isSummaryError.value) return "";
  return summaryText.value.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
});

function copyText(text) {
  if (!text) return;
  const clean = text.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
  navigator.clipboard.writeText(clean);
  toast.add({
    severity: "success",
    summary: "已复制",
    detail: "内容已复制到剪贴板",
    life: 2000,
  });
}

function copySummary() {
  const textToCopy = cleanMarkdownSummary.value || summaryText.value;
  copyText(textToCopy);
}

function formatMessage(content) {
  let txt = content || "";
  txt = txt.replace(
    /<think>([\s\S]*?)<\/think>/gi,
    '<details class="mb-2 rounded-lg bg-black/10 dark:bg-black/25 border border-theme-border p-2 text-theme-text-muted"><summary class="cursor-pointer text-[10px] text-indigo-400 font-semibold select-none">🧠 思考过程 (展开)</summary><div class="mt-1.5 pl-2 border-l-2 border-indigo-500/30 text-[10.5px] leading-relaxed whitespace-pre-wrap font-mono">$1</div></details>',
  );

  // Render display math $$...$$
  txt = txt.replace(/\$\$([\s\S]+?)\$\$/g, (match, math) => {
    try {
      const rendered = katex.renderToString(math.trim(), { displayMode: true, throwOnError: false, errorColor: "#cc0000" });
      return `<div class="katex-display-wrapper my-1 overflow-x-auto text-center">${rendered}</div>`;
    } catch {
      return match;
    }
  });

  // Render inline math $...$
  txt = txt.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)(?<!\$)\$(?!\$)/g, (match, math) => {
    try {
      return katex.renderToString(math.trim(), { displayMode: false, throwOnError: false, errorColor: "#cc0000" });
    } catch {
      return match;
    }
  });

  // Markdown formatting without hardcoded white
  txt = txt
    .replace(/^### (.*$)/gim, '<div class="font-bold text-xs text-indigo-400 mt-2 mb-0.5">$1</div>')
    .replace(/^## (.*$)/gim, '<div class="font-bold text-xs text-indigo-500 mt-2.5 mb-1">$1</div>')
    .replace(/^# (.*$)/gim, '<div class="font-bold text-sm text-theme-brand mt-3 mb-1">$1</div>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-theme-text">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="italic opacity-90 text-theme-text">$1</em>')
    .replace(/`([^`\n]+)`/g, '<code class="bg-theme-background-elevated border border-theme-border/60 px-1 py-0.5 rounded font-mono text-[11px] text-theme-brand">$1</code>')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-theme-background-elevated border border-theme-border p-2 rounded-md my-1 font-mono text-[10.5px] overflow-x-auto text-theme-text"><code>$2</code></pre>');

  return txt;
}

async function sendChat() {
  const query = inputQuery.value.trim();
  if (!query || isLoadingChat.value) return;

  messages.value.push({ role: "user", content: query });
  inputQuery.value = "";
  isLoadingChat.value = true;

  try {
    const res = await chatWithAi(
      props.currentDocTitle,
      props.currentDocContent,
      messages.value
    );
    messages.value.push({ role: "assistant", content: res.reply });
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || "请求失败";
    messages.value.push({ role: "assistant", content: `❌ 请求出错：${msg}` });
  } finally {
    isLoadingChat.value = false;
  }
}
</script>

<style>
.ai-toast-viewer.toast-viewer,
.ai-toast-viewer .toastui-editor-contents {
  font-size: 12px !important;
  line-height: 1.65 !important;
  color: rgb(var(--theme-text)) !important;
}

.ai-toast-viewer .toastui-editor-contents h1 {
  font-size: 15px !important;
  color: rgb(var(--theme-brand)) !important;
  margin: 10px 0 4px 0 !important;
  border: none !important;
}

.ai-toast-viewer .toastui-editor-contents h2 {
  font-size: 14px !important;
  color: rgb(var(--theme-brand)) !important;
  margin: 8px 0 4px 0 !important;
  border: none !important;
}

.ai-toast-viewer .toastui-editor-contents h3 {
  font-size: 13px !important;
  color: #6366f1 !important;
  margin: 8px 0 3px 0 !important;
  border: none !important;
}

.ai-toast-viewer .toastui-editor-contents h4,
.ai-toast-viewer .toastui-editor-contents h5,
.ai-toast-viewer .toastui-editor-contents h6 {
  font-size: 12.5px !important;
  color: rgb(var(--theme-text)) !important;
  margin: 6px 0 2px 0 !important;
  border: none !important;
}

.ai-toast-viewer .toastui-editor-contents p {
  margin: 0 0 8px 0 !important;
  color: rgb(var(--theme-text)) !important;
  line-height: 1.65 !important;
}

.ai-toast-viewer .toastui-editor-contents strong {
  font-weight: 600 !important;
  color: rgb(var(--theme-text)) !important;
}

.ai-toast-viewer .toastui-editor-contents ul,
.ai-toast-viewer .toastui-editor-contents ol {
  padding-left: 18px !important;
  margin-bottom: 8px !important;
  color: rgb(var(--theme-text)) !important;
}

.ai-toast-viewer .toastui-editor-contents li {
  margin: 2px 0 !important;
  color: rgb(var(--theme-text)) !important;
}

.ai-toast-viewer .toastui-editor-contents pre {
  padding: 8px !important;
  margin: 6px 0 !important;
  border-radius: 6px !important;
  background-color: rgb(var(--theme-background-elevated)) !important;
  border: 1px solid rgb(var(--theme-border)) !important;
}

.ai-toast-viewer .toastui-editor-contents code {
  color: rgb(var(--theme-text)) !important;
  font-size: 11px !important;
}

.ai-toast-viewer .katex-display-wrapper {
  margin: 6px 0 !important;
  padding: 4px 0 !important;
  font-size: 13px !important;
}

.chat-msg-body {
  color: rgb(var(--theme-text));
}
.chat-msg-body strong {
  color: rgb(var(--theme-text)) !important;
}
</style>
