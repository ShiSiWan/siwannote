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
    @confirm="setEditMode()"
    @reject="
      clearDraft();
      setEditMode();
    "
  />

  <LoadingIndicator ref="loadingIndicator" class="flex h-full flex-col">
    <!-- Header -->
    <div class="flex flex-col-reverse md:flex-row md:items-baseline">
      <!-- Title -->
      <div class="grow truncate text-3xl leading-[1.6em]">
        <span v-show="!editMode" :title="note.title">{{ note.title }}</span>
        <input
          v-show="editMode"
          v-model.trim="newTitle"
          class="w-full bg-theme-background outline-none"
          placeholder="输入笔记标题..."
        />
      </div>

      <!-- Buttons -->
      <div class="flex shrink-0 self-end md:self-baseline print:hidden">
        <!-- Delete Button -->
        <CustomButton
          v-show="canModify && !isNewNote"
          label="删除"
          :iconPath="mdilDelete"
          @click="deleteHandler"
        />
        <!-- Save Button -->
        <CustomButton
          v-show="editMode"
          label="保存"
          :iconPath="mdilContentSave"
          @click="saveHandler((close = false))"
          class="relative ml-1"
        >
          <!-- Unsaved Changes Indicator -->
          <div
            v-show="unsavedChanges"
            class="absolute right-1 h-1.5 w-1.5 rounded-full bg-theme-brand"
          ></div>
        </CustomButton>
        <!-- Edit / Preview Button -->
        <button
          v-if="canModify"
          type="button"
          class="ml-1.5 flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold shadow-sm transition cursor-pointer"
          :class="editMode ? 'border-amber-500/40 bg-amber-500/10 text-amber-600 hover:bg-amber-500 hover:text-white dark:text-amber-400' : 'border-theme-brand/40 bg-theme-brand/10 text-theme-brand hover:bg-theme-brand hover:text-white'"
          @click="toggleEditModeHandler"
          :title="editMode ? '完成编辑并查看预览' : '开启文档编辑'"
        >
          <KeylineIcon :name="editMode ? 'eye' : 'edit'" size="13" strokeWidth="2.2" />
          <span>{{ editMode ? '完成预览' : '编辑文档' }}</span>
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 min-h-[550px]">
      <ToastViewer
        v-if="!editMode"
        :initialValue="note.content"
        class="toast-viewer pb-4"
      />
      <ToastEditor
        v-if="editMode"
        ref="toastEditor"
        :initialValue="getInitialEditorValue()"
        :addImageBlobHook="addImageBlobHook"
        @change="startContentChangedTimeout"
        @keydown="keydownHandler"
      />
    </div>

      <!-- Comments Section (Visible when not editing and note exists) -->
      <div v-if="!editMode && !isNewNote && note.title" class="mt-12 border-t border-theme-border pt-8 pb-10">
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
} from "../api.js";
import { Note } from "../classes.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import KeylineIcon from "../components/KeylineIcon.vue";
import ToastEditor from "../components/toastui/ToastEditor.vue";
import ToastViewer from "../components/toastui/ToastViewer.vue";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { getToastOptions } from "../helpers.js";
import { isCurrentTokenStored } from "../tokenStorage.js";

const props = defineProps({
  title: String,
});

const isAdmin = ref(false);
const canModify = computed(
  () => isAdmin.value && globalStore.config.authType != authTypes.readOnly,
);

// Comments state
const comments = ref([]);
const newCommentText = ref("");
const visitorNickname = ref(
  localStorage.getItem("siwan_visitor_nickname") || "",
);
const isSubmittingComment = ref(false);

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

let contentChangedTimeout = null;
const editMode = ref(false);
const globalStore = useGlobalStore();
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

function init() {
  checkAdminStatus();
  // Return if we already have the note e.g. When we rename a note, the route prop would change but we’d already have the note.
  if (props.title && props.title == note.value.title) {
    loadComments(props.title);
    return;
  }

  loadingIndicator.value.setLoading();
  if (props.title) {
    loadComments(props.title);
    getNote(props.title)
      .then((data) => {
        note.value = data;
        globalStore.currentDocTitle = data.title;
        globalStore.currentDocContent = data.content;
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
    // Set the editMode to false to close any existing editors.
    // This ensures the editor is cleanly reinitialised in an empty state.
    // Simple fix for #266 without requiring a full re-work of the logic.
    editMode.value = false;
    nextTick(() => {
      editHandler();
      loadingIndicator.value.setLoaded();
    });
  }
}

// Note Editing
function toggleEditModeHandler() {
  if (editMode.value) {
    closeHandler();
  } else {
    editHandler();
  }
}

function editHandler() {
  const draftContent = loadDraft();
  if (draftContent) {
    isDraftModalVisible.value = true;
  } else {
    setEditMode();
  }
}

function setEditMode() {
  newTitle.value = note.value.title;
  unsavedChanges.value = false;
  editMode.value = true;
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

  // Save Note
  let newContent = toastEditor.value.getMarkdown();
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
    closeNote();
  }
  setBeforeUnloadConfirmation(false);
  toast.add(getToastOptions("笔记已成功保存 ✓", "成功", "success"));
}

// Note Closure
function closeHandler() {
  if (isContentChanged()) {
    isSaveChangesModalVisible.value = true;
  } else {
    closeNote();
  }
}

function closeNote() {
  clearDraft();
  editMode.value = false;
  if (isNewNote.value) {
    router.push({ name: "home" });
  } else {
    editMode.value = false;
  }
}

// Image Upload
function addImageBlobHook(file, callback) {
  const altTextInputValue = document.getElementById(
    "toastuiAltTextInput",
  )?.value;

  // Upload the image then use the callback to insert the URL into the editor
  postAttachment(file).then(function (data) {
    if (data) {
      // If the user has entered an alt text, use it. Otherwise, use the filename returned by the API.
      const altText = altTextInputValue ? altTextInputValue : data.filename;
      callback(data.url, altText);
    }
  });
}

function postAttachment(file) {
  // Invalid Character Validation
  if (reservedFilenameCharacters.test(file.name)) {
    badFilenameToast("Title");
    return;
  }

  // Uploading Toast
  toast.add(getToastOptions("Uploading attachment..."));

  // Upload the attachment
  return createAttachment(file)
    .then((data) => {
      // Success Toast
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
        // Note: The current implementation will append a datetime to the filename if it already exists.
        // Error Toast
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
  const content = toastEditor.value.getMarkdown();
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
// 'e' to edit
Mousetrap.bind("e", () => {
  if (editMode.value === false && canModify.value) {
    editHandler();
  }
});

function keydownHandler(event) {
  // Ctrl + Enter to save
  if ((event.ctrlKey || event.metaKey) && event.key == "Enter") {
    saveHandler((close = false));
  }
  // Escape to exit edit mode
  if (event.key == "Escape") {
    closeHandler();
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
  return (
    newTitle.value != note.value.title ||
    toastEditor.value.getMarkdown() != note.value.content
  );
}

function handleInsertSummary(e) {
  const summaryText = e.detail?.summary;
  if (!summaryText || !note.value.title) return;
  const insertBlock = `\n\n> ### 🤖 AI 智能总结\n>\n${summaryText
    .split("\n")
    .map((l) => "> " + l)
    .join("\n")}\n\n`;

  if (editMode.value && toastEditor.value) {
    const current = toastEditor.value.getMarkdown();
    toastEditor.value.setMarkdown(current + insertBlock);
    toast.add({
      severity: "success",
      summary: "已插入编辑器",
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

onMounted(() => {
  init();
  window.addEventListener("siwan-insert-summary", handleInsertSummary);
  window.addEventListener("siwan-auth-changed", checkAdminStatus);
});

onBeforeUnmount(() => {
  window.removeEventListener("siwan-insert-summary", handleInsertSummary);
  window.removeEventListener("siwan-auth-changed", checkAdminStatus);
});
</script>
