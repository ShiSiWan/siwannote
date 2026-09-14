<template>
  <div ref="viewerElement"></div>
</template>

<script setup>
import Viewer from "@toast-ui/editor/dist/toastui-editor-viewer";
import { onMounted, ref, watch } from "vue";
import "katex/dist/katex.min.css";

import baseOptions from "./baseOptions.js";
import extendedAutolinks from "./extendedAutolinks.js";
import { preprocessMath, renderMathInDOM } from "./mathRenderer.js";

const props = defineProps({
  initialValue: String,
  enableTocSync: {
    type: Boolean,
    default: true,
  },
});

const viewerElement = ref();
let viewerInstance = null;

// Generate heading IDs for TOC jumping
function processHeadings() {
  if (!props.enableTocSync || !viewerElement.value) return;
  const headings = viewerElement.value.querySelectorAll("h1, h2, h3, h4, h5, h6");
  const existingIds = new Set();

  headings.forEach((h, idx) => {
    const text = h.textContent.trim();
    if (!text) return;

    let primaryId = text.toLowerCase()
      .replace(/[^\w\u4e00-\u9fa5]+/g, "-")
      .replace(/^-+|-+$/g, "");
    if (!primaryId) primaryId = `section-${idx}`;

    let uniqueId = primaryId;
    let counter = 1;
    while (existingIds.has(uniqueId)) {
      uniqueId = `${primaryId}-${counter++}`;
    }
    existingIds.add(uniqueId);
    h.id = uniqueId;
  });

  // Emit event so left sidebar outline updates
  window.dispatchEvent(new CustomEvent("siwan-headings-updated"));
}

function updateContent(content) {
  if (!viewerInstance) return;
  viewerInstance.setMarkdown(preprocessMath(content));
  setTimeout(() => {
    processHeadings();
    renderMathInDOM(viewerElement.value);
  }, 50);
}

onMounted(() => {
  viewerInstance = new Viewer({
    ...baseOptions,
    extendedAutolinks,
    el: viewerElement.value,
    initialValue: preprocessMath(props.initialValue || ""),
  });

  setTimeout(() => {
    processHeadings();
    renderMathInDOM(viewerElement.value);
  }, 100);
});

watch(
  () => props.initialValue,
  (newVal) => {
    updateContent(newVal || "");
  }
);
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor-viewer.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "./toastui-editor-overrides.scss";

.katex-display-wrapper {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.5em 0;
  margin: 0.8em 0;
  text-align: center;
}
.toastui-editor-contents h1,
.toastui-editor-contents h2,
.toastui-editor-contents h3,
.toastui-editor-contents h4,
.toastui-editor-contents h5,
.toastui-editor-contents h6 {
  scroll-margin-top: 85px;
}
</style>
