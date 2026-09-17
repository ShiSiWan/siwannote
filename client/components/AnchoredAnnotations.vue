<template>
  <div ref="containerRef" class="anchored-annotations-layer absolute inset-0 pointer-events-none">
    <!-- SVG Connector Lines pointing from marks in article (on the left) to cards in right margin -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none overflow-visible z-10">
      <g v-for="item in positionedItems" :key="`line-${item.id}`">
        <path
          :d="getConnectorPath(item)"
          fill="none"
          :stroke="getLineStroke(item)"
          :stroke-width="activeId === item.id || hoveredId === item.id ? 2.2 : 1.4"
          :stroke-dasharray="activeId === item.id || hoveredId === item.id ? '' : '3 3'"
          class="transition-all duration-150"
          :opacity="activeId === item.id || hoveredId === item.id ? 1 : 0.7"
        />
        <!-- Target dot on the text highlight right edge -->
        <circle
          :cx="item.targetX + 2"
          :cy="item.targetY"
          r="3"
          :fill="getDotFill(item)"
          class="transition-colors duration-150"
        />
        <!-- Origin dot on the card left border -->
        <circle
          :cx="item.cardLeftX"
          :cy="item.cardCenterY"
          r="2.5"
          :fill="getDotFill(item)"
          class="transition-colors duration-150"
        />
      </g>
    </svg>

    <!-- Anchored Cards in Right Margin -->
    <div
      v-for="item in positionedItems"
      :key="item.id"
      :ref="(el) => setCardRef(item.id, el)"
      class="anchored-bubble pointer-events-auto absolute left-0 w-[240px] rounded-xl border border-dashed backdrop-blur-md p-3 shadow-md transition-all duration-150 cursor-pointer select-text"
      :class="[
        item.author_type === 'ai'
          ? 'border-purple-400/60 dark:border-purple-500/50 bg-purple-50/90 dark:bg-purple-950/40 text-purple-950 dark:text-purple-100 shadow-purple-500/5'
          : 'border-sky-400/60 dark:border-sky-500/50 bg-sky-50/90 dark:bg-sky-950/40 text-sky-950 dark:text-sky-100 shadow-sky-500/5',
        activeId === item.id || hoveredId === item.id
          ? item.author_type === 'ai'
            ? 'border-purple-500 shadow-purple-500/20 ring-2 ring-purple-500/25 z-20 scale-[1.01]'
            : 'border-sky-500 shadow-sky-500/20 ring-2 ring-sky-500/25 z-20 scale-[1.01]'
          : 'hover:border-current z-10'
      ]"
      :style="{ top: `${item.top}px` }"
      @click="onCardClick(item)"
      @mouseenter="onCardMouseEnter(item.id)"
      @mouseleave="onCardMouseLeave"
    >
      <!-- Card Header -->
      <div class="flex items-center justify-between gap-1.5 pb-1.5 mb-1.5 border-b border-current/15">
        <div class="flex items-center gap-1.5 min-w-0 flex-wrap">
          <!-- Author badge -->
          <div
            class="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10.5px] font-bold shrink-0"
            :class="item.author_type === 'ai' ? 'bg-purple-500/15 text-purple-600 dark:text-purple-300' : 'bg-sky-500/15 text-sky-600 dark:text-sky-300'"
          >
            <KeylineIcon :name="item.author_type === 'ai' ? 'sparkles' : 'message-square'" size="11" strokeWidth="2.2" />
            <span>{{ item.author_type === 'ai' ? 'AI 读者' : '用户批注' }}</span>
          </div>

          <!-- Type tag (e.g. 事实存疑, 建议补充) -->
          <span
            v-if="item.comment_type"
            class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-500/10 text-purple-700 dark:text-purple-300 shrink-0"
          >
            {{ item.comment_type }}
          </span>

          <span
            class="text-[10px] opacity-60 shrink-0 cursor-help hover:opacity-100"
            :title="formatAbsoluteTime(item.createdAt || item.created_at)"
          >
            {{ formatRelativeTime(item.createdAt || item.created_at) }}
          </span>

          <span
            v-if="item.model"
            class="text-[9.5px] font-mono opacity-50 px-1 py-0.2 rounded bg-current/5 shrink-0"
            :title="`生成模型: ${item.model}`"
          >
            {{ item.model }}
          </span>
        </div>

        <!-- Action: Delete (Admin Only) -->
        <button
          v-if="canModify"
          class="shrink-0 rounded p-1 text-current/50 hover:bg-red-500/15 hover:text-red-500 transition"
          title="删除此批注"
          @click.stop="$emit('delete', item.id)"
        >
          <KeylineIcon name="trash" size="12" />
        </button>
      </div>

      <!-- Quote preview -->
      <div
        class="mb-2 line-clamp-2 border-l-2 pl-1.5 text-[11px] italic leading-tight"
        :class="item.author_type === 'ai' ? 'border-purple-400 text-purple-700 dark:text-purple-300' : 'border-sky-400 text-sky-700 dark:text-sky-300'"
      >
        “{{ item.quote }}”
      </div>

      <!-- Comment body / Inline edit -->
      <div v-if="editingCardId === item.id" class="space-y-1.5 mb-2" @click.stop>
        <textarea
          v-model="editCommentDraft"
          rows="2"
          maxlength="200"
          class="w-full text-[11.5px] rounded-lg border border-purple-400 bg-white/90 dark:bg-slate-900/90 p-2 text-slate-800 dark:text-slate-100 outline-none leading-relaxed"
          placeholder="修改建议内容后采纳..."
        ></textarea>
        <div class="flex items-center justify-end gap-1.5">
          <button
            class="px-2 py-0.5 rounded text-[11px] text-slate-500 hover:bg-slate-200/50 dark:hover:bg-slate-800"
            @click.stop="cancelEditCard"
          >
            取消
          </button>
          <button
            class="px-2.5 py-0.5 rounded text-[11px] font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-sm"
            @click.stop="saveModifiedAccept(item.id)"
          >
            保存并采纳
          </button>
        </div>
      </div>
      <div
        v-else
        class="text-[11.5px] leading-relaxed font-normal whitespace-pre-wrap break-words mb-2"
        :class="item.author_type === 'ai' ? 'text-purple-950 dark:text-purple-50' : 'text-sky-950 dark:text-sky-50'"
      >
        {{ item.comment }}
      </div>

      <!-- Status badge & Actions for AI annotations -->
      <div class="pt-1.5 border-t border-current/10 flex items-center justify-between gap-1 flex-wrap text-[10.5px]">
        <!-- Current Status Badge -->
        <div class="flex items-center gap-1">
          <span
            v-if="item.status === 'accepted'"
            class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md font-semibold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
          >
            <KeylineIcon name="check" size="10" strokeWidth="2.5" />
            <span>已采纳</span>
          </span>
          <span
            v-else-if="item.status === 'modified_accepted'"
            class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md font-semibold bg-blue-500/15 text-blue-700 dark:text-blue-300"
          >
            <KeylineIcon name="edit" size="10" strokeWidth="2.5" />
            <span>修改采纳</span>
          </span>
          <span
            v-else-if="item.status === 'rejected'"
            class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md font-semibold bg-slate-500/15 text-slate-600 dark:text-slate-400"
          >
            <KeylineIcon name="x" size="10" strokeWidth="2.5" />
            <span>已驳回</span>
          </span>
          <span
            v-else-if="item.author_type === 'ai'"
            class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md font-semibold bg-purple-500/15 text-purple-700 dark:text-purple-300"
          >
            <span>待处理</span>
          </span>
        </div>

        <!-- Action Buttons for Admin on AI annotations -->
        <div v-if="canModify && item.author_type === 'ai'" class="flex items-center gap-1 shrink-0 ml-auto">
          <template v-if="!item.status || item.status === 'proposed'">
            <button
              class="px-2 py-0.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-[10.5px] shadow-sm transition active:scale-95 flex items-center gap-0.5"
              title="采纳此建议"
              @click.stop="handleAccept(item.id)"
            >
              <KeylineIcon name="check" size="10" strokeWidth="2.5" />
              <span>采纳</span>
            </button>
            <button
              class="px-1.5 py-0.5 rounded-md border border-purple-400/80 hover:bg-purple-500/15 text-purple-700 dark:text-purple-200 font-semibold text-[10.5px] transition active:scale-95"
              title="修改并采纳"
              @click.stop="startEditCard(item)"
            >
              <span>修改</span>
            </button>
            <button
              class="px-1.5 py-0.5 rounded-md text-current/60 hover:bg-red-500/15 hover:text-red-500 font-semibold text-[10.5px] transition active:scale-95"
              title="驳回此建议"
              @click.stop="handleReject(item.id)"
            >
              <span>驳回</span>
            </button>
          </template>
          <button
            v-else
            class="text-[10px] text-current/50 hover:text-current underline transition"
            title="撤销当前状态，重新处理"
            @click.stop="handleReset(item.id)"
          >
            重新处理
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import KeylineIcon from "./KeylineIcon.vue";
import { formatRelativeTime, formatAbsoluteTime } from "../helpers.js";

const props = defineProps({
  annotations: {
    type: Array,
    default: () => [],
  },
  activeAnnId: {
    type: String,
    default: "",
  },
  articleWrapper: {
    type: Object,
    default: null,
  },
  canModify: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["delete", "select", "hover", "update-status"]);

const containerRef = ref();
const cardRefs = new Map();
const cardHeights = ref({});
const positionedItems = ref([]);
const hoveredId = ref("");
const activeId = ref(props.activeAnnId);

const editingCardId = ref("");
const editCommentDraft = ref("");

function setCardRef(id, el) {
  if (el) {
    cardRefs.set(id, el);
  } else {
    cardRefs.delete(id);
  }
}

watch(
  () => props.activeAnnId,
  (val) => {
    activeId.value = val;
  }
);

function onCardClick(item) {
  activeId.value = item.id;
  emit("select", item.id);
}

function onCardMouseEnter(id) {
  hoveredId.value = id;
  emit("hover", id);
  const wrapper = getWrapperElement();
  if (wrapper) {
    const mark = wrapper.querySelector(`mark.siwan-annotation[data-ann-id="${CSS.escape(id)}"]`);
    if (mark) mark.classList.add("siwan-annotation-hovered");
  }
}

function onCardMouseLeave() {
  const oldId = hoveredId.value;
  hoveredId.value = "";
  emit("hover", "");
  const wrapper = getWrapperElement();
  if (wrapper && oldId) {
    const mark = wrapper.querySelector(`mark.siwan-annotation[data-ann-id="${CSS.escape(oldId)}"]`);
    if (mark) mark.classList.remove("siwan-annotation-hovered");
  }
}

function getWrapperElement() {
  if (!props.articleWrapper) return null;
  return props.articleWrapper.$el || props.articleWrapper;
}

function updateCardHeights() {
  let changed = false;
  cardRefs.forEach((el, id) => {
    if (el) {
      const h = el.offsetHeight;
      if (cardHeights.value[id] !== h) {
        cardHeights.value[id] = h;
        changed = true;
      }
    }
  });
  return changed;
}

function recalculatePositions() {
  const container = containerRef.value;
  const wrapper = getWrapperElement();
  if (!container || !wrapper || !props.annotations.length) {
    positionedItems.value = [];
    return;
  }

  const containerRect = container.getBoundingClientRect();
  updateCardHeights();

  // Measure anchor target positions for each annotation
  const rawList = [];
  props.annotations.forEach((ann) => {
    const mark = wrapper.querySelector(`mark.siwan-annotation[data-ann-id="${CSS.escape(ann.id)}"]`);
    if (mark) {
      const markRect = mark.getBoundingClientRect();
      const targetY = (markRect.top - containerRect.top) + markRect.height / 2;
      // Mark is to the left of the container on the right margin
      const targetX = markRect.right - containerRect.left;
      rawList.push({
        ...ann,
        naturalTop: Math.max(0, markRect.top - containerRect.top),
        targetY: targetY,
        targetX: targetX,
        height: cardHeights.value[ann.id] || 95,
      });
    } else {
      // Fallback if mark not rendered yet
      rawList.push({
        ...ann,
        naturalTop: 0,
        targetY: 20,
        targetX: -20,
        height: cardHeights.value[ann.id] || 95,
      });
    }
  });

  // Sort by vertical position
  rawList.sort((a, b) => a.naturalTop - b.naturalTop);

  // Collision resolution algorithm (push down overlapping cards)
  const GAP = 12; // px
  let currentBottom = 0;
  const positioned = [];

  for (let i = 0; i < rawList.length; i++) {
    const item = rawList[i];
    const top = Math.max(item.naturalTop, currentBottom);
    const cardHeight = item.height;
    const cardLeftX = 0; // Card sits at left: 0 of the right margin container
    const cardCenterY = top + cardHeight / 2;

    positioned.push({
      ...item,
      top: top,
      cardLeftX: cardLeftX,
      cardCenterY: cardCenterY,
    });

    currentBottom = top + cardHeight + GAP;
  }

  positionedItems.value = positioned;
}

function getConnectorPath(item) {
  const x1 = item.targetX;
  const y1 = item.targetY;
  const x2 = item.cardLeftX;
  const y2 = item.cardCenterY;

  // Smooth cubic Bezier curve from article text right edge to card left edge
  const midX = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
}

function getLineStroke(item) {
  const isActive = activeId.value === item.id || hoveredId.value === item.id;
  if (item.author_type === "ai") {
    return isActive ? "#8b5cf6" : "#c084fc";
  } else {
    return isActive ? "#0284c7" : "#38bdf8";
  }
}

function getDotFill(item) {
  const isActive = activeId.value === item.id || hoveredId.value === item.id;
  if (item.author_type === "ai") {
    return isActive ? "#8b5cf6" : "#a855f7";
  } else {
    return isActive ? "#0284c7" : "#0ea5e9";
  }
}

function handleAccept(id) {
  emit("update-status", { id, status: "accepted" });
}

function handleReject(id) {
  emit("update-status", { id, status: "rejected" });
}

function handleReset(id) {
  emit("update-status", { id, status: "proposed" });
}

function startEditCard(item) {
  editingCardId.value = item.id;
  editCommentDraft.value = item.comment || "";
  nextTick(() => {
    recalculatePositions();
  });
}

function cancelEditCard() {
  editingCardId.value = "";
  editCommentDraft.value = "";
  nextTick(() => {
    recalculatePositions();
  });
}

function saveModifiedAccept(id) {
  const newComment = editCommentDraft.value.trim();
  emit("update-status", { id, status: "modified_accepted", comment: newComment });
  editingCardId.value = "";
  editCommentDraft.value = "";
}

function formatShortDate(isoStr) {
  if (!isoStr) return "";
  try {
    const parts = isoStr.split(" ");
    if (parts.length > 1) {
      return parts[1].slice(0, 5); // HH:MM
    }
    const d = new Date(isoStr);
    return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
  } catch {
    return isoStr;
  }
}

let resizeObserver = null;

onMounted(() => {
  nextTick(() => {
    recalculatePositions();
  });

  const wrapper = getWrapperElement();
  if (wrapper && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      recalculatePositions();
    });
    resizeObserver.observe(wrapper);
  }

  window.addEventListener("resize", recalculatePositions);
  window.addEventListener("siwan-sidebar-resize", recalculatePositions);
  window.addEventListener("siwan-sidebar-toggle", recalculatePositions);
  window.addEventListener("siwan-headings-updated", () => {
    setTimeout(recalculatePositions, 200);
  });
});

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  window.removeEventListener("resize", recalculatePositions);
  window.removeEventListener("siwan-sidebar-resize", recalculatePositions);
  window.removeEventListener("siwan-sidebar-toggle", recalculatePositions);
});

watch(
  () => props.annotations,
  () => {
    nextTick(() => {
      setTimeout(recalculatePositions, 80);
    });
  },
  { deep: true }
);

defineExpose({ recalculatePositions });
</script>

<style scoped>
.anchored-bubble {
  box-shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.07), 0 2px 6px -1px rgba(0, 0, 0, 0.04);
}
</style>
