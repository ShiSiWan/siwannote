<template>
  <div ref="editorElement" class="w-full min-h-[550px]"></div>
</template>

<script setup>
import Editor from "@toast-ui/editor";
import "@toast-ui/editor/dist/i18n/zh-cn";
import { onMounted, onBeforeUnmount, ref, watch } from "vue";

import baseOptions from "./baseOptions.js";
import { renderMathInDOM } from "./mathRenderer.js";

const props = defineProps({
  initialValue: {
    type: String,
    default: "",
  },
  addImageBlobHook: Function,
});

const emit = defineEmits(["change", "save"]);

const editorElement = ref();
let toastEditor;
let mathTimer = null;

function refreshEditorMath() {
  if (mathTimer) clearTimeout(mathTimer);
  mathTimer = setTimeout(() => {
    if (!editorElement.value) return;
    const preview = editorElement.value.querySelector(".toastui-editor-md-preview");
    if (preview) {
      renderMathInDOM(preview);
    }
  }, 150);
}

// Capture-phase keydown for editor shortcuts.
// Intercept before toast-ui's own handlers (Ctrl+S saves)
function handleShortcut(event) {
  const isCtrl = event.ctrlKey || event.metaKey;
  if (!isCtrl) return;

  if (event.key.toLowerCase() === "s") {
    event.preventDefault();
    event.stopPropagation();
    emit("save");
    return;
  }
  if (event.key === "Enter") {
    event.preventDefault();
    event.stopPropagation();
    emit("save");
  }
}

onMounted(() => {
  const initial = props.initialValue || "";
  toastEditor = new Editor({
    ...baseOptions,
    language: "zh-CN",
    el: editorElement.value,
    initialValue: initial,
    initialEditType: "markdown",
    previewStyle: "tab",
    hideModeSwitch: true,
    minHeight: "500px",
    height: "auto",
    events: {
      change: () => {
        emit("change");
        refreshEditorMath();
      },
    },
    hooks: props.addImageBlobHook
      ? { addImageBlobHook: props.addImageBlobHook }
      : {},
  });

  editorElement.value.addEventListener("keydown", handleShortcut, true);

  // Ensure content is explicitly loaded if initial was provided
  if (initial && (!toastEditor.getMarkdown() || !toastEditor.getMarkdown().trim())) {
    toastEditor.setMarkdown(initial);
  }

  setTimeout(refreshEditorMath, 200);
});

onBeforeUnmount(() => {
  if (editorElement.value) {
    editorElement.value.removeEventListener("keydown", handleShortcut, true);
  }
});

watch(
  () => props.initialValue,
  (newVal) => {
    if (toastEditor && newVal !== undefined) {
      const current = toastEditor.getMarkdown();
      if ((!current || !current.trim()) && newVal) {
        toastEditor.setMarkdown(newVal);
      }
    }
  }
);

function getMarkdown() {
  return toastEditor ? toastEditor.getMarkdown() : "";
}

function setMarkdown(val) {
  if (toastEditor) {
    toastEditor.setMarkdown(val || "");
  }
}

defineExpose({ getMarkdown, setMarkdown });
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "./toastui-editor-overrides.scss";

/* 隐藏右侧与浮动的格式提醒/快捷键气泡 (针对熟悉 Markdown 的用户) */
.toastui-editor-tooltip {
  display: none !important;
}
</style>
