<template>
  <!-- Confirm Deletion Modal -->
  <ConfirmModal
    v-model="isDeleteModalVisible"
    title="确认删除"
    :message="`确定要永久删除笔记《${note.title}》吗？此操作不可撤销。`"
    confirmButtonText="删除"
    confirmButtonStyle="danger"
    rejectButtonText="取消"
    @confirm="deleteConfirmedHandler"
  />

  <!-- Save Changes Modal -->
  <ConfirmModal
    v-model="isSaveChangesModalVisible"
    title="保存更改"
    message="检测到您对该笔记进行了修改，是否保存？"
    confirmButtonText="保存"
    confirmButtonStyle="success"
    rejectButtonText="放弃更改"
    rejectButtonStyle="danger"
    @confirm="saveHandler((close = true))"
    @reject="closeNote"
  />

  <!-- Draft Modal -->
  <ConfirmModal
    v-model="isDraftModalVisible"
    title="发现本地未保存草稿"
    message="检测到浏览器中存在此笔记的未保存草稿版本。您希望恢复草稿还是舍弃？"
    confirmButtonText="恢复草稿"
    confirmButtonStyle="cta"
    rejectButtonText="舍弃草稿"
    rejectButtonStyle="danger"
    @confirm="setCreationMode()"
    @reject="
      clearDraft();
      setCreationMode();
    "
  />

  <LoadingIndicator ref="loadingIndicator" class="flex h-full flex-col">
    <!-- Header -->
    <div class="flex flex-col-reverse md:flex-row md:items-baseline">
      <!-- Title & Note Timestamps -->
      <div class="grow min-w-0">
        <div class="truncate text-3xl leading-[1.6em]">
          <span v-show="!isCreationMode" :title="note.title">{{ note.title }}</span>
          <input
            v-show="isCreationMode"
            v-model.trim="newTitle"
            class="w-full bg-theme-background outline-none font-bold"
            placeholder="输入笔记标题..."
          />
        </div>
        <!-- Note Timestamps (Reading Mode) -->
        <div
          v-if="!isCreationMode && note.title"
          class="mt-1 flex items-center gap-3 flex-wrap text-xs text-theme-text-muted"
        >
          <span
            v-if="note.updated || note.last_modified"
            :title="formatAbsoluteTime(note.updated || note.last_modified)"
            class="inline-flex items-center gap-1 cursor-help hover:text-theme-text transition-colors"
          >
            <KeylineIcon name="refresh" size="11" />
            <span>更新于 {{ formatRelativeTime(note.updated || note.last_modified) }}</span>
          </span>
          <span
            v-if="note.created"
            :title="formatAbsoluteTime(note.created)"
            class="inline-flex items-center gap-1 cursor-help hover:text-theme-text transition-colors"
          >
            <KeylineIcon name="file-text" size="11" />
            <span>创建于 {{ formatRelativeTime(note.created) }}</span>
          </span>
          <span
            v-if="globalStore.isAiScanning && globalStore.aiScanningTitle === note.title"
            class="inline-flex items-center gap-1.5 text-purple-600 dark:text-purple-400 font-semibold bg-purple-500/10 px-2 py-0.5 rounded-full border border-purple-500/30 animate-pulse"
            title="AI 正在后台进行结构化深度总结与第二读者批注审查..."
          >
            <KeylineIcon name="sparkles" size="11" />
            <span>AI 第二读者正在审阅...</span>
          </span>
          <span
            v-else-if="note.reviewed"
            :title="formatAbsoluteTime(note.reviewed)"
            class="inline-flex items-center gap-1 text-purple-600 dark:text-purple-400 font-medium cursor-help"
          >
            <KeylineIcon name="sparkles" size="11" />
            <span>AI 审阅于 {{ formatRelativeTime(note.reviewed) }}</span>
          </span>
          <!-- Manual AI Review & Summary Button -->
          <button
            v-if="canModify && (!globalStore.isAiScanning || globalStore.aiScanningTitle !== note.title)"
            type="button"
            class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border border-purple-500/30 bg-purple-500/10 text-purple-600 hover:bg-purple-500/20 dark:text-purple-300 dark:border-purple-400/30 transition cursor-pointer font-medium"
            @click="manualTriggerAiScan"
            :title="note.reviewed ? '文档未改动时AI不自动重复审阅。点击此处可手动重新审阅与生成总结' : '手动触发 AI 第二读者审阅与摘要生成'"
          >
            <KeylineIcon name="sparkles" size="11" />
            <span>{{ note.reviewed ? '重新审阅' : 'AI 审阅与总结' }}</span>
          </button>
        </div>
      </div>

      <!-- Buttons -->
      <div class="flex shrink-0 self-end md:self-baseline print:hidden items-center flex-wrap gap-1">
        <!-- Delete Button -->
        <CustomButton
          v-show="canModify && !isNewNote"
          label="删除"
          :iconPath="mdilDelete"
          @click="deleteHandler"
        />

        <!-- Save Button (Active in Creation Mode) -->
        <CustomButton
          v-show="isCreationMode"
          label="保存"
          :iconPath="mdilContentSave"
          @click="saveHandler((close = false))"
          class="relative ml-1"
          title="保存文档 (快捷键: Ctrl + S)"
        >
          <!-- Unsaved Changes Indicator -->
          <div
            v-show="unsavedChanges"
            class="absolute right-1 h-1.5 w-1.5 rounded-full bg-theme-brand"
          ></div>
        </CustomButton>

        <!-- Creation Mode Exit Button: "返回阅读模式" -->
        <button
          v-if="isCreationMode"
          type="button"
          class="ml-1 flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-600 hover:bg-emerald-500 hover:text-white dark:text-emerald-400 shadow-sm transition cursor-pointer"
          @click="exitCreationModeHandler"
          title="退出创作，返回阅读模式"
        >
          <KeylineIcon name="book-open" size="13" strokeWidth="2.2" />
          <span>返回阅读模式</span>
        </button>

        <!-- Reading Mode Entry Button: "进入创作模式" -->
        <button
          v-if="canModify && !isCreationMode"
          type="button"
          class="ml-1.5 flex items-center gap-1.5 rounded-lg border border-theme-brand/40 bg-theme-brand/10 px-3 py-1.5 text-xs font-semibold text-theme-brand hover:bg-theme-brand hover:text-white shadow-sm transition cursor-pointer"
          @click="enterCreationModeHandler"
          title="进入创作模式 (快捷键: e)"
        >
          <KeylineIcon name="edit" size="13" strokeWidth="2.2" />
          <span>进入创作模式</span>
        </button>

        <!-- Annotations (书签批注) Toggle Button (Reading Mode, Admin Only) -->
        <button
          v-if="canModify && !isCreationMode"
          type="button"
          class="ml-1 flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold shadow-sm transition cursor-pointer"
          :class="showAnchoredAnnotations ? 'border-sky-500/50 bg-sky-500/15 text-sky-600 hover:bg-sky-500 hover:text-white dark:text-sky-400' : 'border-theme-border/60 text-theme-text-muted hover:border-sky-500/50 hover:text-sky-500'"
          @click="toggleAnnotationMode"
          :title="showAnchoredAnnotations ? '收起批注' : '展开右侧页边距批注'"
        >
          <KeylineIcon name="message-square" size="13" strokeWidth="2.2" />
          <span>{{ showAnchoredAnnotations ? '批注' + (annotations.length ? ` (${annotations.length})` : '') : '批注' }}</span>
        </button>
      </div>
    </div>

    <!-- Content Area -->
    <div ref="articleWrapperRef" class="relative flex-1 min-h-[550px] w-full mt-4">
      <!-- Reading Mode: Push Centered Layout with Right Page Margin Annotations -->
      <div v-if="!isCreationMode" class="flex justify-center w-full relative">
        <!-- Center Article Content Area -->
        <div class="flex-1 min-w-0 w-full relative">
          <ToastViewer
            ref="toastViewer"
            :initialValue="note.content"
            class="toast-viewer pb-4"
            @mouseup="onViewerMouseUp"
          />
        </div>

        <!-- Word-Style Right Margin Anchored Annotations (Desktop >= 1024px) -->
        <div
          v-if="annotations.length > 0 && showAnchoredAnnotations"
          class="hidden lg:block w-[240px] shrink-0 ml-6 relative"
        >
          <AnchoredAnnotations
            ref="anchoredAnnotationsRef"
            :annotations="annotations"
            :active-ann-id="activeAnnotationId"
            :article-wrapper="articleWrapperRef"
            :can-modify="canModify"
            @delete="deleteAnnotationHandler"
            @select="onSelectAnnotation"
            @hover="onHoverAnnotation"
            @update-status="updateAnnotationStatusHandler"
          />
        </div>
      </div>

      <!-- Creation Mode: Centered Single Unified Editor -->
      <div v-else class="flex justify-center w-full relative">
        <div class="flex-1 min-w-0 w-full relative">
          <ToastEditor
            ref="toastEditor"
            :initialValue="getInitialEditorValue()"
            :addImageBlobHook="addImageBlobHook"
            @change="startContentChangedTimeout"
            @save="saveHandler(false)"
          />
        </div>
      </div>

      <!-- Annotation Floating Action (Admin, view mode, selection active) -->
      <div
        v-if="annotationAction.visible"
        class="fixed z-[60] w-[280px] rounded-xl border border-indigo-500/40 bg-theme-background-elevated/95 px-3 py-2.5 shadow-xl backdrop-blur-md"
        :style="{ left: annotationAction.x + 'px', top: annotationAction.y + 'px' }"
      >
        <div class="mb-1.5 flex items-start justify-between gap-2">
          <span class="line-clamp-2 text-[11px] italic leading-snug text-indigo-500">“{{ annotationAction.quote }}”</span>
          <button
            class="shrink-0 rounded p-1 text-theme-text-muted transition hover:bg-theme-background hover:text-theme-text"
            title="取消"
            @click="cancelAnnotationAction"
          >
            <KeylineIcon name="x" size="12" />
          </button>
        </div>
        <template v-if="annotationAction.comment">
          <div class="mb-2 rounded-lg bg-indigo-500/10 px-2 py-1.5 text-[11px] leading-relaxed text-theme-text">
            {{ annotationAction.comment }}
          </div>
          <button
            class="flex w-full items-center justify-center gap-1 rounded-lg border border-red-500/40 px-2 py-1.5 text-[11px] font-semibold text-red-500 transition hover:bg-red-500 hover:text-white"
            @click="deleteAnnotationHandler(annotationAction.annId)"
          >
            <KeylineIcon name="trash" size="12" />
            删除此批注
          </button>
        </template>
        <button
          v-else
          class="flex w-full items-center justify-center gap-1 rounded-lg bg-indigo-500 px-2 py-1.5 text-[11px] font-bold text-white shadow transition hover:bg-indigo-600"
          @click="openAnnotationComposer"
        >
          <KeylineIcon name="message-square" size="12" />
          添加批注
        </button>
      </div>

      <!-- Annotation Composer Modal -->
      <div
        v-if="annotationComposer.visible"
        class="fixed inset-0 z-[70] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
        @click.self="closeAnnotationComposer"
      >
        <div class="w-full max-w-md rounded-2xl border border-theme-border bg-theme-background p-5 shadow-2xl">
          <div class="mb-3 flex items-center justify-between">
            <h4 class="flex items-center gap-2 text-sm font-bold text-theme-text">
              <KeylineIcon name="message-square" size="16" className="text-indigo-500" />
              添加书签批注
            </h4>
            <button class="rounded p-1 text-theme-text-muted transition hover:bg-theme-background hover:text-theme-text" @click="closeAnnotationComposer">
              <KeylineIcon name="x" size="14" />
            </button>
          </div>
          <div class="mb-3 max-h-24 overflow-y-auto rounded-lg border-l-2 border-indigo-400 bg-indigo-500/5 px-3 py-2 text-xs leading-relaxed text-theme-text-muted">
            “{{ annotationComposer.quote }}”
          </div>
          <textarea
            v-model.trim="annotationComposer.comment"
            rows="3"
            maxlength="500"
            placeholder="写下您对这段内容的批注或想法..."
            class="w-full rounded-lg border border-theme-border bg-theme-background p-3 text-xs leading-relaxed outline-none transition focus:border-indigo-500"
          ></textarea>
          <div class="mt-3 flex items-center justify-between">
            <span class="text-[10px] text-theme-text-muted">仅管理员可见，跨设备同步</span>
            <div class="flex items-center gap-2">
              <button
                class="rounded-lg border border-theme-border px-3 py-1.5 text-xs font-semibold text-theme-text-muted transition hover:bg-theme-background"
                @click="closeAnnotationComposer"
              >
                取消
              </button>
              <button
                class="flex items-center gap-1 rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-bold text-white shadow transition hover:bg-indigo-600 disabled:opacity-50"
                :disabled="isSavingAnnotation || !annotationComposer.comment"
                @click="saveAnnotationHandler"
              >
                <KeylineIcon name="check" size="12" />
                <span>{{ isSavingAnnotation ? '保存中...' : '保存批注' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

      <!-- Comments Section (Visible in reading mode when note exists) -->
      <div v-if="!isCreationMode && !isNewNote && note.title" class="mt-12 border-t border-theme-border pt-8 pb-10">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-2">
            <KeylineIcon name="message-square" size="18" className="text-theme-brand" />
            <h3 class="text-base font-bold text-theme-text">讨论与留言 ({{ comments.length }})</h3>
          </div>
          <span class="text-xs text-theme-text-muted">访客与讨论交流专区</span>
        </div>

        <!-- Post Comment Box -->
        <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 mb-6 shadow-sm">
          <div class="mb-3 flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-1.5 text-xs font-semibold text-theme-text">
              <KeylineIcon name="user" size="14" />
              <span>您的昵称：<span class="text-red-500">*</span></span>
            </div>
            <div class="relative flex items-center">
              <input
                v-model.trim="visitorNickname"
                type="text"
                maxlength="20"
                placeholder="自定义昵称 (必填，2~20字)..."
                class="rounded-md border bg-theme-background px-3 py-1.5 text-xs outline-none transition w-48 sm:w-56"
                :class="!visitorNickname ? 'border-amber-500/60 focus:border-amber-500' : 'border-theme-border focus:border-theme-brand'"
              />
            </div>
            <span v-if="isAdmin" class="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold text-emerald-500">管理员身份</span>
            <span v-else-if="!visitorNickname" class="text-[11px] text-amber-500 font-medium">⚠️ 请先输入自定义昵称（禁止系统默认名）</span>
            <span v-else class="text-[11px] text-theme-text-muted">（个性化昵称已设置）</span>
          </div>

          <textarea
            v-model="newCommentText"
            rows="3"
            placeholder="对这篇笔记写下您的想法、疑问或补充探讨（文明交流，禁止违规辱骂词汇）..."
            class="w-full rounded-md border border-theme-border bg-theme-background p-3 text-xs leading-relaxed outline-none focus:border-theme-brand"
          ></textarea>

          <div class="mt-2.5 flex items-center justify-between">
            <span class="text-[11px] text-theme-text-muted">文明交流、共同沉淀知识（违规辱骂词汇将被拦截）</span>
            <button
              class="rounded-lg bg-theme-brand px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
              :disabled="isSubmittingComment || !newCommentText.trim() || !visitorNickname.trim() || visitorNickname.trim().length < 2"
              @click="submitCommentHandler"
            >
              <KeylineIcon name="send" size="13" />
              <span>{{ isSubmittingComment ? '发表中...' : '发表留言' }}</span>
            </button>
          </div>
        </div>

        <!-- Comments List -->
        <div class="space-y-3">
          <div v-if="comments.length === 0" class="py-8 text-center text-xs text-theme-text-muted border border-dashed border-theme-border rounded-xl">
            暂无留言讨论，快来发表第一条想法吧！
          </div>
          <div
            v-for="c in comments"
            :key="c.id"
            class="rounded-xl border border-theme-border bg-theme-background-elevated/30 p-3.5 transition hover:bg-theme-background-elevated/60"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="flex h-7 w-7 items-center justify-center rounded-full bg-theme-brand/10 font-bold text-xs text-theme-brand">
                  {{ (c.author || '友')[0] }}
                </div>
                <span class="font-bold text-xs text-theme-text">{{ c.author }}</span>
                <span class="text-[10px] text-theme-text-muted">{{ formatCommentDate(c.created_at) }}</span>
              </div>
              <!-- Admin Delete Comment Button -->
              <button
                v-if="isAdmin"
                class="rounded p-1 text-theme-text-muted hover:text-red-500 hover:bg-red-500/10 transition"
                title="管理员删除此评论"
                @click="deleteCommentHandler(c.id)"
              >
                <KeylineIcon name="trash" size="14" />
              </button>
            </div>
            <div class="pl-9 text-xs text-theme-text leading-relaxed whitespace-pre-wrap">
              {{ c.content }}
            </div>
          </div>
        </div>
      </div>
  </LoadingIndicator>
</template>

<style>
/* Disable checkboxes in view mode. See https://github.com/nhn/tui.editor/issues/1087. */
.toast-viewer li.task-list-item {
  pointer-events: none;
}
.toast-viewer li.task-list-item a {
  pointer-events: auto;
}

/* Annotation (书签批注) highlight styles */
mark.siwan-annotation {
  border-radius: 3px;
  padding: 0 2px;
  cursor: pointer;
  transition: all 0.15s ease;
}

/* User Annotation: Light Blue */
mark.siwan-annotation.siwan-annotation-user,
mark.siwan-annotation:not(.siwan-annotation-ai) {
  background: rgba(56, 189, 248, 0.22);
  border-bottom: 2px solid rgba(2, 132, 199, 0.65);
}
mark.siwan-annotation.siwan-annotation-user:hover,
mark.siwan-annotation.siwan-annotation-user.siwan-annotation-hovered,
mark.siwan-annotation:not(.siwan-annotation-ai):hover,
mark.siwan-annotation:not(.siwan-annotation-ai).siwan-annotation-hovered {
  background: rgba(56, 189, 248, 0.45);
  border-bottom: 2px solid #0284c7;
}

/* AI Annotation: Purple */
mark.siwan-annotation.siwan-annotation-ai {
  background: rgba(168, 85, 247, 0.22);
  border-bottom: 2px solid rgba(139, 92, 246, 0.75);
}
mark.siwan-annotation.siwan-annotation-ai:hover,
mark.siwan-annotation.siwan-annotation-ai.siwan-annotation-hovered {
  background: rgba(168, 85, 247, 0.45);
  border-bottom: 2px solid #8b5cf6;
}

mark.siwan-annotation.siwan-annotation-active {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.35);
}
mark.siwan-annotation.siwan-annotation-flash {
  background: rgba(245, 158, 11, 0.6) !important;
}
</style>

<script setup>
import { mdiNoteOffOutline } from "@mdi/js";
import { mdilContentSave, mdilDelete } from "@mdi/light-js";
import Mousetrap from "mousetrap";
import { useToast } from "primevue/usetoast";
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch } from "vue";
import { useRouter } from "vue-router";

import {
  apiErrorHandler,
  createAttachment,
  createNote,
  deleteNote,
  getNote,
  updateNote,
  getComments,
  postComment,
  deleteComment,
  getSecurityStatus,
  getAnnotations,
  addAnnotation,
  updateAnnotation,
  deleteAnnotation,
  triggerAiReview,
  triggerAiScan,
} from "../api.js";
import { Note } from "../classes.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import KeylineIcon from "../components/KeylineIcon.vue";
import ToastEditor from "../components/toastui/ToastEditor.vue";
import ToastViewer from "../components/toastui/ToastViewer.vue";
import AnchoredAnnotations from "../components/AnchoredAnnotations.vue";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { getToastOptions, formatRelativeTime, formatAbsoluteTime } from "../helpers.js";
import { isCurrentTokenStored } from "../tokenStorage.js";

const props = defineProps({
  title: String,
});

const isAdmin = ref(false);
const canModify = computed(
  () => isAdmin.value && globalStore.config.authType != authTypes.readOnly,
);

// Anchored Annotations refs & state
const articleWrapperRef = ref();
const anchoredAnnotationsRef = ref();
const activeAnnotationId = ref("");
const showAnchoredAnnotations = ref(
  localStorage.getItem("siwan_show_annotations") !== "0"
);

// Comments state
const comments = ref([]);
const newCommentText = ref("");
const visitorNickname = ref(
  localStorage.getItem("siwan_visitor_nickname") || "",
);
const isSubmittingComment = ref(false);

// Annotations (书签批注) state - Admin only
const annotations = ref([]);
const annotationAction = ref({
  visible: false,
  x: 0,
  y: 0,
  quote: "",
  comment: "",
  annId: "",
});
const annotationComposer = ref({ visible: false, quote: "", comment: "" });
const isSavingAnnotation = ref(false);
const toastViewer = ref();

async function checkAdminStatus() {
  try {
    const res = await getSecurityStatus();
    isAdmin.value = res.is_admin === true;
    if (isAdmin.value && !localStorage.getItem("siwan_visitor_nickname")) {
      visitorNickname.value = "管理员 (Admin)";
    }
  } catch {
    isAdmin.value = false;
  }
}

async function loadComments(title) {
  if (!title) {
    comments.value = [];
    return;
  }
  try {
    const res = await getComments(title);
    comments.value = res.comments || [];
  } catch (err) {
    console.warn("Failed to load comments:", err);
  }
}

async function submitCommentHandler() {
  const author = visitorNickname.value.trim();
  const content = newCommentText.value.trim();
  if (!author) {
    toast.add(getToastOptions("请输入您的自定义昵称后再发表留言", "昵称缺失", "warn"));
    return;
  }
  if (author.length < 2) {
    toast.add(getToastOptions("昵称长度至少需要 2 个字符", "昵称过短", "warn"));
    return;
  }
  if (!content) {
    toast.add(getToastOptions("请输入留言内容", "内容缺失", "warn"));
    return;
  }
  isSubmittingComment.value = true;
  try {
    localStorage.setItem("siwan_visitor_nickname", author);
    const res = await postComment(note.value.title, author, content);
    comments.value = res.comments || [];
    newCommentText.value = "";
    toast.add(getToastOptions("留言已成功发表 ✓", "成功", "success"));
  } catch (err) {
    const detail = err.response?.data?.detail || "发表留言失败，请检查昵称或内容是否包含违规敏感词";
    toast.add(getToastOptions(detail, "提示", "error"));
  } finally {
    isSubmittingComment.value = false;
  }
}

async function deleteCommentHandler(commentId) {
  try {
    const res = await deleteComment(note.value.title, commentId);
    comments.value = res.comments || [];
    toast.add(getToastOptions("留言已删除 ✓", "成功", "success"));
  } catch (err) {
    toast.add(getToastOptions("删除留言失败", "错误", "error"));
  }
}

function formatCommentDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("zh-CN", { hour12: false });
  } catch {
    return isoStr;
  }
}

// -------------------- Annotations (书签批注) --------------------
async function loadAnnotations(title) {
  if (!title) {
    annotations.value = [];
    return;
  }
  try {
    const res = await getAnnotations(title);
    annotations.value = res.annotations || [];
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  } catch (err) {
    if (err?.response?.status !== 403) {
      console.warn("Failed to load annotations:", err);
    }
  }
}

function toggleAnnotationMode() {
  showAnchoredAnnotations.value = !showAnchoredAnnotations.value;
  localStorage.setItem("siwan_show_annotations", showAnchoredAnnotations.value ? "1" : "0");
  annotationAction.value = { visible: false, x: 0, y: 0, quote: "" };
  if (showAnchoredAnnotations.value) {
    toast.add(
      getToastOptions("批注已开启，选中正文文字即可添加新批注", "批注模式", "info"),
    );
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  } else {
    toast.add(getToastOptions("批注已收起隐藏", "批注模式", "info"));
    applyAnnotationHighlights();
  }
}

function onSelectAnnotation(annId) {
  activeAnnotationId.value = annId;
  scrollToAnnotation(annId);
}

function onHoverAnnotation(annId) {
  activeAnnotationId.value = annId;
  const viewerEl = toastViewer.value?.$el;
  if (!viewerEl) return;
  viewerEl.querySelectorAll("mark.siwan-annotation").forEach((m) => {
    if (m.dataset.annId === annId) {
      m.classList.add("siwan-annotation-hovered");
    } else {
      m.classList.remove("siwan-annotation-hovered");
    }
  });
}

function onViewerMouseUp(event) {
  if (isCreationMode.value || !canModify.value) return;
  const viewerEl = toastViewer.value?.$el;
  if (!viewerEl) return;
  if (!viewerEl.contains(event.target)) return;
  if (event.target.closest?.("mark.siwan-annotation")) return;

  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) {
    annotationAction.value = { visible: false, x: 0, y: 0, quote: "", comment: "", annId: "" };
    return;
  }
  const quote = selection.toString().trim();
  if (quote.length < 2) {
    annotationAction.value = { visible: false, x: 0, y: 0, quote: "", comment: "", annId: "" };
    return;
  }
  if (!viewerEl.contains(selection.anchorNode) || !viewerEl.contains(selection.focusNode)) {
    return;
  }
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  annotationAction.value = {
    visible: true,
    x: Math.min(Math.max(rect.left, 16), window.innerWidth - 300),
    y: Math.max(10, rect.top - 50),
    quote: quote.slice(0, 500),
    comment: "",
    annId: "",
  };
}

function cancelAnnotationAction() {
  annotationAction.value = { visible: false, x: 0, y: 0, quote: "", comment: "", annId: "" };
}

function openAnnotationComposer() {
  if (!annotationAction.value.quote) return;
  annotationComposer.value = {
    visible: true,
    quote: annotationAction.value.quote,
    comment: "",
  };
  cancelAnnotationAction();
}

function closeAnnotationComposer() {
  annotationComposer.value.visible = false;
}

async function saveAnnotationHandler() {
  if (!note.value?.title || isSavingAnnotation.value) return;
  const quote = annotationComposer.value.quote;
  const comment = annotationComposer.value.comment.trim();
  if (!quote || !comment) {
    toast.add(getToastOptions("请填写批注内容", "内容为空", "warn"));
    return;
  }
  isSavingAnnotation.value = true;
  try {
    const res = await addAnnotation(note.value.title, quote, comment);
    annotations.value = res.annotations || [];
    showAnchoredAnnotations.value = true;
    localStorage.setItem("siwan_show_annotations", "1");
    annotationComposer.value.visible = false;
    toast.add(getToastOptions("批注已成功保存并锚定在正文右侧", "批注成功", "success"));
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  } catch (err) {
    if (err?.response?.data?.detail) {
      toast.add(getToastOptions(err.response.data.detail, "批注失败", "error"));
    } else {
      apiErrorHandler(err, toast);
    }
  } finally {
    isSavingAnnotation.value = false;
  }
}

async function updateAnnotationStatusHandler({ id, status, comment }) {
  if (!note.value?.title) return;
  try {
    const data = { status };
    if (comment !== undefined) {
      data.comment = comment;
    }
    const res = await updateAnnotation(note.value.title, id, data);
    annotations.value = res.annotations || [];
    toast.add(getToastOptions("批注状态已更新 ✓", "成功", "success"));
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  } catch (err) {
    toast.add(getToastOptions("更新批注状态失败", "错误", "error"));
  }
}

async function deleteAnnotationHandler(annId) {
  if (!note.value?.title) return;
  try {
    const res = await deleteAnnotation(note.value.title, annId);
    annotations.value = res.annotations || [];
    toast.add(getToastOptions("批注已删除", "删除成功", "success"));
    cancelAnnotationAction();
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  } catch (err) {
    apiErrorHandler(err, toast);
  }
}

function scrollToAnnotation(annId) {
  if (!annId) return;
  const viewerEl = toastViewer.value?.$el;
  if (!viewerEl) return;
  const marks = viewerEl.querySelectorAll(`mark.siwan-annotation[data-ann-id="${CSS.escape(annId)}"]`);
  if (marks.length) {
    marks[0].scrollIntoView({ behavior: "smooth", block: "center" });
    marks[0].classList.add("siwan-annotation-flash");
    setTimeout(() => marks[0].classList.remove("siwan-annotation-flash"), 1800);
  }
}

function applyAnnotationHighlights() {
  const viewerEl = toastViewer.value?.$el;
  if (!viewerEl) return;

  viewerEl.querySelectorAll("mark.siwan-annotation").forEach((mark) => {
    const parent = mark.parentNode;
    while (mark.firstChild) {
      parent.insertBefore(mark.firstChild, mark);
    }
    parent.removeChild(mark);
    parent.normalize();
  });

  if (!showAnchoredAnnotations.value || !annotations.value.length || isCreationMode.value) {
    nextTick(() => {
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
    return;
  }

  const quoteMap = {};
  annotations.value.forEach((ann) => {
    const q = (ann.quote || "").trim();
    if (!q) return;
    if (!quoteMap[q]) quoteMap[q] = [];
    quoteMap[q].push(ann);
  });

  Object.keys(quoteMap).forEach((quote) => {
    const anns = quoteMap[quote];
    const escaped = quote.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(escaped, "g");

    const walker = document.createTreeWalker(
      viewerEl,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          if (
            parent.closest("pre, code, script, style, .katex, .toastui-editor-md-code")
          ) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        },
      },
    );

    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) textNodes.push(node);

    let idx = 0;
    textNodes.forEach((textNode) => {
      const text = textNode.nodeValue || "";
      regex.lastIndex = 0;
      let match;
      while ((match = regex.exec(text)) !== null) {
        const ann = anns[idx % anns.length];
        idx += 1;
        const annId = ann.id;
        const range = document.createRange();
        range.setStart(textNode, match.index);
        range.setEnd(textNode, match.index + quote.length);
        try {
          const mark = document.createElement("mark");
          mark.className = ann.author_type === "ai"
            ? "siwan-annotation siwan-annotation-ai"
            : "siwan-annotation siwan-annotation-user";
          mark.dataset.annId = annId;
          mark.dataset.quote = quote;
          mark.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onSelectAnnotation(annId);
            if (window.innerWidth < 1024) {
              const targetAnn = annotations.value.find((a) => a.id === annId);
              annotationAction.value = {
                visible: true,
                x: Math.min(e.clientX, window.innerWidth - 300),
                y: e.clientY + 14,
                quote: quote,
                comment: targetAnn ? targetAnn.comment : "",
                annId: annId,
              };
            }
          });
          mark.addEventListener("mouseenter", () => {
            onHoverAnnotation(annId);
          });
          range.surroundContents(mark);
        } catch (err) {
        }
      }
    });
  });

  nextTick(() => {
    anchoredAnnotationsRef.value?.recalculatePositions();
  });
}

let contentChangedTimeout = null;
const globalStore = useGlobalStore();
const isCreationMode = computed(() => globalStore.currentMode === "creation");
const currentMarkdownContent = ref("");

const isSaveChangesModalVisible = ref(false);
const isDeleteModalVisible = ref(false);
const isDraftModalVisible = ref(false);
const isNewNote = computed(() => !props.title);
const loadingIndicator = ref();
const note = ref({});
const reservedFilenameCharacters = /[<>:"/\\|?*]/;
const router = useRouter();
const newTitle = ref();
const toast = useToast();
const toastEditor = ref();
const unsavedChanges = ref(false);

async function triggerAiScanAsync(title, content) {
  if (!title || !content || globalStore.isAiScanning) return;
  globalStore.isAiScanning = true;
  globalStore.aiScanningTitle = title;
  try {
    const res = await triggerAiScan(title, content);
    if (res?.status === "success") {
      annotations.value = res.annotations || [];
      nextTick(() => {
        applyAnnotationHighlights();
        anchoredAnnotationsRef.value?.recalculatePositions();
      });
      if (res.new_annotations_count > 0) {
        toast.add({
          severity: "info",
          summary: "AI 第二读者审阅",
          detail: `AI 已完成深度审阅，生成了 ${res.new_annotations_count} 条批注草稿并更新摘要`,
          life: 5000,
        });
      }
      if (res.reviewed) {
        note.value.reviewed = res.reviewed;
      }
      window.dispatchEvent(
        new CustomEvent("siwan-ai-scan-completed", { detail: res })
      );
    }
  } catch (e) {
    console.debug("[AI Scan] background scan completed or skipped:", e?.message);
  } finally {
    globalStore.isAiScanning = false;
    globalStore.aiScanningTitle = "";
  }
}

function manualTriggerAiScan() {
  if (!note.value?.title || !note.value?.content) return;
  if (globalStore.isAiScanning) return;
  toast.add({
    severity: "info",
    summary: "AI 审阅与总结",
    detail: "已开始对当前文档进行 AI 深度审阅与结构化总结...",
    life: 3000,
  });
  triggerAiScanAsync(note.value.title, note.value.content);
}

function handleExternalScanCompleted(e) {
  const detail = e.detail;
  if (!detail || detail.title !== note.value.title) return;
  if (detail.annotations) {
    annotations.value = detail.annotations;
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  }
  if (detail.reviewed) {
    note.value.reviewed = detail.reviewed;
  }
}

function init() {
  checkAdminStatus();
  // Return if we already have the note e.g. When we rename a note, the route prop would change but we’d already have the note.
  if (props.title && props.title == note.value.title) {
    loadComments(props.title);
    loadAnnotations(props.title);
    return;
  }

  loadingIndicator.value.setLoading();
  if (props.title) {
    loadComments(props.title);
    loadAnnotations(props.title);
    getNote(props.title)
      .then((data) => {
        note.value = data;
        currentMarkdownContent.value = data.content || "";
        globalStore.currentDocTitle = data.title;
        globalStore.currentDocContent = data.content;
        globalStore.currentMode = "reading";
        loadingIndicator.value.setLoaded();
      })
      .catch((error) => {
        if (error.response?.status === 404) {
          loadingIndicator.value.setFailed("未找到该笔记", mdiNoteOffOutline);
        } else if (error.response?.status === 403) {
          loadingIndicator.value.setFailed("无访问权限，请联系管理员开放此笔记");
        } else {
          loadingIndicator.value.setFailed();
          apiErrorHandler(error, toast);
        }
      });
  } else {
    newTitle.value = "";
    note.value = new Note();
    currentMarkdownContent.value = "";
    globalStore.currentMode = "reading";
    nextTick(() => {
      enterCreationModeHandler();
      loadingIndicator.value.setLoaded();
    });
  }
}

function enterCreationModeHandler() {
  const draftContent = loadDraft();
  if (draftContent) {
    isDraftModalVisible.value = true;
  } else {
    setCreationMode();
  }
}

function setCreationMode() {
  newTitle.value = note.value.title;
  unsavedChanges.value = false;
  currentMarkdownContent.value = note.value?.content || "";
  globalStore.currentMode = "creation";
  nextTick(() => {
    window.dispatchEvent(new CustomEvent("siwan-headings-updated"));
  });
}

function exitCreationModeHandler() {
  if (isContentChanged()) {
    isSaveChangesModalVisible.value = true;
  } else {
    closeCreationMode();
  }
}

function closeCreationMode() {
  clearDraft();
  globalStore.currentMode = "reading";
  if (isNewNote.value) {
    router.push({ name: "home" });
  } else {
    nextTick(() => {
      window.dispatchEvent(new CustomEvent("siwan-headings-updated"));
    });
  }
}

function getInitialEditorValue() {
  const draftContent = loadDraft();
  return draftContent ? draftContent : (note.value?.content || "");
}

// Note Deletion
function deleteHandler() {
  isDeleteModalVisible.value = true;
}

function deleteNoteConfirmed() {
  deleteNote(props.title)
    .then(() => {
      clearDraft();
      router.push({ name: "home" }).then(() => {
        toast.add(
          getToastOptions(
            "文档已成功删除",
            "已删除",
            "success",
          ),
        );
      });
    })
    .catch((error) => {
      apiErrorHandler(error, toast);
    });
}

// Note Saving
function saveHandler(close = false) {
  saveConfirmed(close);
}

function saveConfirmed(close = false) {
  if (!newTitle.value) {
    toast.add(
      getToastOptions(
        "文档标题不能为空，请输入标题后重试。",
        "标题缺失",
        "warn",
      ),
    );
    return;
  }

  // Retrieve latest Markdown content
  let newContent = "";
  if (toastEditor.value) {
    newContent = toastEditor.value.getMarkdown();
    currentMarkdownContent.value = newContent;
  } else {
    newContent = currentMarkdownContent.value || note.value.content || "";
  }

  if (isNewNote.value) {
    saveNew(newTitle.value, newContent, close);
  } else {
    saveExisting(newTitle.value, newContent, close);
  }
}

function saveNew(newTitle, newContent, close = false) {
  createNote(newTitle, newContent)
    .then((data) => {
      clearDraft();
      note.value = data;
      currentMarkdownContent.value = data.content || "";
      router
        .push({
          name: "note",
          params: { title: note.value.title },
        })
        .then(() => {
          noteSaveSuccess(close);
        });
    })
    .catch(noteSaveFailure);
}

function saveExisting(newTitle, newContent, close = false) {
  const titleChanged = newTitle != note.value.title;
  const contentChanged = newContent != note.value.content;

  if (!titleChanged && !contentChanged) {
    noteSaveSuccess(close);
    return;
  }

  updateNote(note.value.title, newTitle, newContent)
    .then((data) => {
      clearDraft();
      note.value = data;
      currentMarkdownContent.value = data.content || "";
      router.replace({ name: "note", params: { title: note.value.title } });
      noteSaveSuccess(close);
    })
    .catch(noteSaveFailure);
}

function noteSaveFailure(error) {
  if (error.response?.status === 409) {
    toast.add(
      getToastOptions(
        "已存在同名笔记，请更换标题后重试。",
        "标题冲突",
        "error",
      ),
    );
  } else if (error.response?.status === 413) {
    entityTooLargeToast("note");
  } else {
    apiErrorHandler(error, toast);
  }
}

function noteSaveSuccess(close = false) {
  unsavedChanges.value = false;
  globalStore.currentDocTitle = note.value.title;
  globalStore.currentDocContent = note.value.content;
  window.dispatchEvent(
    new CustomEvent("siwan-note-saved", {
      detail: { title: note.value.title, content: note.value.content },
    }),
  );
  if (close) {
    closeCreationMode();
  }
  // Only trigger AI scan when note is actually updated/saved
  triggerAiScanAsync(note.value.title, note.value.content);
  setBeforeUnloadConfirmation(false);
  toast.add(getToastOptions("笔记已成功保存 ✓", "成功", "success"));
}

function closeNote() {
  closeCreationMode();
}

// Image Upload
function addImageBlobHook(file, callback) {
  const altTextInputValue = document.getElementById(
    "toastuiAltTextInput",
  )?.value;

  postAttachment(file).then(function (data) {
    if (data) {
      const altText = altTextInputValue ? altTextInputValue : data.filename;
      callback(data.url, altText);
    }
  });
}

function postAttachment(file) {
  if (reservedFilenameCharacters.test(file.name)) {
    badFilenameToast("Title");
    return;
  }

  toast.add(getToastOptions("Uploading attachment..."));

  return createAttachment(file)
    .then((data) => {
      toast.add(
        getToastOptions(
          "Attachment uploaded successfully ✓",
          "Success",
          "success",
        ),
      );
      return data;
    })
    .catch((error) => {
      if (error.response?.status === 409) {
        toast.add(
          getToastOptions(
            "An attachment with this filename already exists.",
            "Duplicate",
            "error",
          ),
        );
      } else if (error.response?.status == 413) {
        entityTooLargeToast("attachment");
      } else {
        apiErrorHandler(error, toast);
      }
    });
}

// Content Change Watcher
function startContentChangedTimeout() {
  clearContentChangedTimeout();
  contentChangedTimeout = setTimeout(contentChangedHandler, 1000);
}

function clearContentChangedTimeout() {
  if (contentChangedTimeout != null) {
    clearTimeout(contentChangedTimeout);
  }
}

function contentChangedHandler() {
  if (isContentChanged()) {
    unsavedChanges.value = true;
    setBeforeUnloadConfirmation(true);
    saveDraft();
  } else {
    unsavedChanges.value = false;
    setBeforeUnloadConfirmation(false);
    clearDraft();
  }
}

// Drafts
function saveDraft() {
  let content = toastEditor.value ? toastEditor.value.getMarkdown() : currentMarkdownContent.value;
  const userHasPersistedToken = isCurrentTokenStored();
  if (content) {
    if (userHasPersistedToken) {
      localStorage.setItem(note.value.title, content);
    } else {
      sessionStorage.setItem(note.value.title, content);
    }
  }
}

function clearDraft() {
  localStorage.removeItem(note.value.title);
  sessionStorage.removeItem(note.value.title);
}

function loadDraft() {
  if (!note.value?.title) return null;
  const localDraft = localStorage.getItem(note.value.title);
  const sessionDraft = sessionStorage.getItem(note.value.title);
  const draft = localDraft || sessionDraft;
  if (draft && draft.trim().length > 0) {
    return draft;
  }
  return null;
}

// Keyboard Shortcuts
// 'e' to enter creation mode
Mousetrap.bind("e", () => {
  if (!isCreationMode.value && canModify.value) {
    enterCreationModeHandler();
  }
});

// "Ctrl + S 保存只在进入创作模式时候生效"
function handleEditorKeydown(e) {
  const isCtrl = e.ctrlKey || e.metaKey;
  if (!isCtrl) return;

  // STRICT REQUIREMENT: Only active in 创作模式!
  if (!isCreationMode.value) {
    return;
  }

  if (e.key.toLowerCase() === "s") {
    e.preventDefault();
    e.stopPropagation();
    saveHandler(false);
    return;
  }
}

function keydownHandler(event) {
  if ((event.ctrlKey || event.metaKey) && event.key == "Enter" && isCreationMode.value) {
    saveHandler(false);
  }
  if (event.key == "Escape" && isCreationMode.value) {
    exitCreationModeHandler();
  }
}

// Helpers
function entityTooLargeToast(entityName) {
  toast.add(
    getToastOptions(
      `This ${entityName} is too large. Please try again with a smaller ${entityName} or adjust your server configuration.`,
      "Failure",
      "error",
    ),
  );
}

function badFilenameToast(entityName) {
  toast.add(
    getToastOptions(
      '由于文件名限制，不能包含下列字符：<>:"/\\|?*',
      `无效的${entityName}`,
      "error",
    ),
  );
}

function setBeforeUnloadConfirmation(enable = true) {
  if (enable) {
    window.onbeforeunload = () => {
      return true;
    };
  } else {
    window.onbeforeunload = null;
  }
}

function isContentChanged() {
  if (!isCreationMode.value) return false;
  let content = toastEditor.value ? toastEditor.value.getMarkdown() : (currentMarkdownContent.value || "");
  return (
    newTitle.value != note.value.title ||
    content != (note.value.content || "")
  );
}

function handleInsertSummary(e) {
  const summaryText = e.detail?.summary;
  if (!summaryText || !note.value.title) return;
  const insertBlock = `\n\n> ### 🤖 AI 智能总结\n>\n${summaryText
    .split("\n")
    .map((l) => "> " + l)
    .join("\n")}\n\n`;

  if (isCreationMode.value && toastEditor.value) {
    const current = toastEditor.value.getMarkdown();
    toastEditor.value.setMarkdown(current + insertBlock);
    currentMarkdownContent.value = current + insertBlock;
    toast.add({
      severity: "success",
      summary: "已插入源码",
      detail: "AI 总结已追加至文档末尾，点击「保存」即可生效！",
      life: 3000,
    });
  } else {
    const updatedContent = (note.value.content || "") + insertBlock;
    updateNote(note.value.title, note.value.title, updatedContent)
      .then((data) => {
        note.value = data;
        noteSaveSuccess(false);
        toast.add({
          severity: "success",
          summary: "插入成功",
          detail: "AI 总结已作为标准引用块持久化写入本篇笔记！",
          life: 3000,
        });
      })
      .catch((err) => {
        toast.add({
          severity: "error",
          summary: "插入失败",
          detail: err.message || "未能更新笔记",
          life: 3000,
        });
      });
  }
}

watch(() => props.title, init);

// Watch for annotation panel open/close to load annotations
watch(
  () => globalStore.isAnnotationPanelOpen,
  (isOpen) => {
    if (isOpen && note.value?.title) {
      loadAnnotations(note.value.title);
    }
  }
);

function handleScrollToAnnotation(event) {
  const annId = event.detail?.annId;
  if (annId) {
    scrollToAnnotation(annId);
  }
}

function onViewerRendered() {
  if (!isCreationMode.value && showAnchoredAnnotations.value) {
    nextTick(() => {
      applyAnnotationHighlights();
      anchoredAnnotationsRef.value?.recalculatePositions();
    });
  }
}

onMounted(() => {
  init();
  window.addEventListener("keydown", handleEditorKeydown, true);
  window.addEventListener("siwan-insert-summary", handleInsertSummary);
  window.addEventListener("siwan-auth-changed", checkAdminStatus);
  window.addEventListener("siwan-headings-updated", onViewerRendered);
  window.addEventListener("siwan-scroll-to-annotation", handleScrollToAnnotation);
  window.addEventListener("siwan-ai-scan-completed", handleExternalScanCompleted);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleEditorKeydown, true);
  window.removeEventListener("siwan-insert-summary", handleInsertSummary);
  window.removeEventListener("siwan-auth-changed", checkAdminStatus);
  window.removeEventListener("siwan-headings-updated", onViewerRendered);
  window.removeEventListener("siwan-scroll-to-annotation", handleScrollToAnnotation);
  window.removeEventListener("siwan-ai-scan-completed", handleExternalScanCompleted);
});
</script>
