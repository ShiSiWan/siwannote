<template>
  <div>
    <!-- Backdrop for Settings Drawer -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm transition-opacity"
      @click="closePanel"
    ></div>

    <!-- Settings Drawer Container -->
    <aside
      class="fixed bottom-0 right-0 top-0 z-50 flex w-full max-w-[460px] flex-col border-l border-theme-border bg-theme-background shadow-2xl transition-transform duration-250 ease-in-out dark:bg-slate-900"
      :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-theme-border px-5 py-4">
        <div class="flex items-center gap-2.5 font-bold text-theme-brand">
          <KeylineIcon name="settings" size="20" strokeWidth="2.2" />
          <span class="text-base tracking-wide text-theme-text">系统设置中心</span>
        </div>
        <button
          class="rounded-md p-1.5 text-theme-text-muted transition hover:bg-theme-background-elevated hover:text-theme-text"
          title="关闭设置"
          @click="closePanel"
        >
          <KeylineIcon name="x" size="18" />
        </button>
      </div>

      <!-- Tab Navigation -->
      <div class="flex border-b border-theme-border bg-theme-background-elevated/40 p-2 gap-1.5">
        <button
          class="flex-1 rounded-lg py-2 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="activeTab === 'page' ? 'bg-theme-brand text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="activeTab = 'page'"
        >
          <KeylineIcon name="sliders" size="14" />
          <span>页面与偏好</span>
        </button>
        <button
          v-if="isAdmin"
          class="flex-1 rounded-lg py-2 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="activeTab === 'ai' ? 'bg-theme-brand text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="activeTab = 'ai'"
        >
          <KeylineIcon name="sparkles" size="14" />
          <span>AI 助手配置</span>
        </button>
        <button
          class="flex-1 rounded-lg py-2 text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="activeTab === 'admin' ? 'bg-theme-brand text-white shadow-sm' : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-background-elevated'"
          @click="activeTab = 'admin'"
        >
          <KeylineIcon name="shield" size="14" />
          <span>权限与管理</span>
        </button>
      </div>

      <!-- Tab 1: Page & Appearance Settings -->
      <div v-show="activeTab === 'page'" class="flex-1 overflow-y-auto p-5 space-y-6 text-xs leading-relaxed">
        <!-- Page Width Setting -->
        <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 font-semibold text-theme-text">
              <KeylineIcon name="sliders" size="16" />
              <span>页面显示宽度</span>
            </div>
            <span class="rounded bg-theme-brand/15 px-2 py-0.5 text-[11px] font-bold text-theme-brand">
              {{ pageWidthLabel }}
            </span>
          </div>
          <p class="text-[11px] text-theme-text-muted">
            调整笔记正文及工作区的最大渲染宽度，适合不同分辨率屏幕。
          </p>
          <div class="grid grid-cols-3 gap-2 pt-1">
            <button
              v-for="opt in pageWidthOptions"
              :key="opt.value"
              class="rounded-lg border px-3 py-2 text-center text-xs font-medium transition"
              :class="currentPageWidth === opt.value ? 'border-theme-brand bg-theme-brand/10 font-bold text-theme-brand' : 'border-theme-border hover:bg-theme-background-elevated text-theme-text-muted'"
              @click="setPageWidth(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- Theme Mode Setting -->
        <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
          <div class="flex items-center gap-2 font-semibold text-theme-text">
            <KeylineIcon name="sun" size="16" />
            <span>界面主题风格</span>
          </div>
          <p class="text-[11px] text-theme-text-muted">
            选择极简浅色、柔和护眼纸感、夜间深色或跟随系统自动切换。
          </p>
          <div class="grid grid-cols-2 gap-2 pt-1 sm:grid-cols-4">
            <button
              class="flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition"
              :class="currentThemeMode === 'light' ? 'border-theme-brand bg-theme-brand/10 font-bold text-theme-brand shadow-sm' : 'border-theme-border hover:bg-theme-background-elevated text-theme-text-muted'"
              @click="setTheme('light')"
            >
              <KeylineIcon name="sun" size="14" />
              <span>浅色模式</span>
            </button>
            <button
              class="flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition"
              :class="currentThemeMode === 'eye-care' ? 'border-amber-500 bg-amber-500/15 font-bold text-amber-700 dark:text-amber-300 shadow-sm' : 'border-theme-border hover:bg-theme-background-elevated text-theme-text-muted'"
              @click="setTheme('eye-care')"
            >
              <KeylineIcon name="eye" size="14" />
              <span>柔和护眼</span>
            </button>
            <button
              class="flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition"
              :class="currentThemeMode === 'dark' ? 'border-theme-brand bg-theme-brand/10 font-bold text-theme-brand shadow-sm' : 'border-theme-border hover:bg-theme-background-elevated text-theme-text-muted'"
              @click="setTheme('dark')"
            >
              <KeylineIcon name="moon" size="14" />
              <span>深色模式</span>
            </button>
            <button
              class="flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-medium transition"
              :class="currentThemeMode === 'system' ? 'border-theme-brand bg-theme-brand/10 font-bold text-theme-brand shadow-sm' : 'border-theme-border hover:bg-theme-background-elevated text-theme-text-muted'"
              @click="setTheme('system')"
            >
              <KeylineIcon name="monitor" size="14" />
              <span>跟随系统</span>
            </button>
          </div>
        </div>

        <!-- Editor Preferences -->
        <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
          <div class="flex items-center gap-2 font-semibold text-theme-text">
            <KeylineIcon name="edit" size="16" />
            <span>编辑体验设置</span>
          </div>
          <div class="flex items-center justify-between pt-1">
            <div>
              <div class="font-medium text-theme-text">隐藏格式快捷键提醒浮层</div>
              <div class="text-[11px] text-theme-text-muted">编辑时关闭悬浮格式提示，适合熟悉 Markdown 语法的用户</div>
            </div>
            <input
              v-model="hideFormatTooltips"
              type="checkbox"
              class="h-4 w-4 rounded text-theme-brand focus:ring-0 cursor-pointer"
              @change="updateEditorPreferences"
            />
          </div>
        </div>
      </div>

      <!-- Tab 2: AI Configuration (Form + ccSwitch Raw JSON Mode) -->
      <div v-show="activeTab === 'ai'" class="flex-1 overflow-y-auto p-5 space-y-4 text-xs leading-relaxed">
        <!-- Sub Mode Switch: Form vs JSON -->
        <div class="flex items-center justify-between border-b border-theme-border pb-3">
          <span class="font-bold text-theme-text">AI 接入模型与网络代理</span>
          <div class="flex rounded-md border border-theme-border p-0.5 bg-theme-background-elevated/60">
            <button
              class="rounded px-2.5 py-1 text-[11px] font-semibold transition"
              :class="aiConfigMode === 'form' ? 'bg-theme-brand text-white' : 'text-theme-text-muted hover:text-theme-text'"
              @click="switchToFormMode"
            >
              表单视图
            </button>
            <button
              class="rounded px-2.5 py-1 text-[11px] font-semibold transition flex items-center gap-1"
              :class="aiConfigMode === 'json' ? 'bg-theme-brand text-white' : 'text-theme-text-muted hover:text-theme-text'"
              @click="switchToJsonMode"
            >
              <KeylineIcon name="code" size="12" />
              <span>ccSwitch JSON</span>
            </button>
          </div>
        </div>

        <!-- Form Mode View -->
        <div v-if="aiConfigMode === 'form'" class="space-y-4">
          <!-- API Base URL -->
          <div>
            <label class="block font-semibold text-theme-text mb-1">
              API 接口地址 (Base URL)
            </label>
            <input
              v-model="aiForm.api_base"
              type="text"
              placeholder="https://api.openai.com/v1"
              class="w-full rounded-md border border-theme-border bg-theme-background-elevated/70 px-3 py-2 text-xs outline-none focus:border-theme-brand"
            />
            <!-- Quick Provider Presets -->
            <div class="mt-1.5 flex flex-wrap gap-1 text-[10px]">
              <span class="text-theme-text-muted py-0.5">常用预设:</span>
              <button
                v-for="p in providerPresets"
                :key="p.name"
                class="rounded bg-theme-background-elevated px-2 py-0.5 text-theme-text-muted hover:text-theme-brand"
                @click="applyProviderPreset(p)"
              >
                {{ p.name }}
              </button>
            </div>
          </div>

          <!-- API Key -->
          <div>
            <label class="block font-semibold text-theme-text mb-1">
              API Key 密钥
            </label>
            <div class="relative">
              <input
                v-model="aiForm.api_key"
                :type="showApiKey ? 'text' : 'password'"
                :placeholder="hasExistingKey ? '已就绪 (输入新密钥可覆盖)' : 'sk-********************************'"
                class="w-full rounded-md border border-theme-border bg-theme-background-elevated/70 px-3 py-2 pr-8 text-xs outline-none focus:border-theme-brand"
              />
              <button
                type="button"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-theme-text-muted hover:text-theme-text"
                @click="showApiKey = !showApiKey"
              >
                {{ showApiKey ? '🙈' : '👁️' }}
              </button>
            </div>
            <div v-if="hasExistingKey" class="mt-1 text-[11px] text-emerald-500 font-medium">
              ✓ 密钥已就绪 ({{ maskedKey }})
            </div>
          </div>

          <!-- Model Selection -->
          <div>
            <label class="block font-semibold text-theme-text mb-1">
              模型名称 (Model)
            </label>
            <input
              v-model="aiForm.model"
              type="text"
              placeholder="deepseek-chat 或 gpt-4o-mini"
              class="w-full rounded-md border border-theme-border bg-theme-background-elevated/70 px-3 py-2 text-xs outline-none focus:border-theme-brand"
            />
            <div class="mt-1.5 flex flex-wrap gap-1 text-[10px]">
              <button
                v-for="m in ['deepseek-chat', 'deepseek-reasoner', 'gpt-4o-mini', 'gpt-4o', 'qwen-plus']"
                :key="m"
                class="rounded bg-theme-background-elevated px-2 py-0.5 text-theme-text-muted hover:text-theme-brand"
                @click="aiForm.model = m"
              >
                {{ m }}
              </button>
            </div>
          </div>

          <!-- Proxy Settings -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="font-semibold text-theme-text">
                网络代理地址 (Proxy URL)
              </label>
              <span class="text-[10px] text-emerald-500 font-medium">已支持 socks5/http 协议</span>
            </div>
            <input
              v-model="aiForm.proxy_url"
              type="text"
              placeholder="http://127.0.0.1:7890 (留空为直连)"
              class="w-full rounded-md border border-theme-border bg-theme-background-elevated/70 px-3 py-2 text-xs outline-none focus:border-theme-brand"
            />
            <div class="mt-1.5 flex flex-wrap gap-1 text-[10px]">
              <button
                class="rounded bg-theme-background-elevated px-2 py-0.5 text-theme-text-muted hover:text-theme-brand"
                @click="aiForm.proxy_url = 'http://127.0.0.1:7890'"
              >
                本地地址 (7890)
              </button>
              <button
                class="rounded bg-theme-background-elevated px-2 py-0.5 text-theme-text-muted hover:text-theme-brand"
                @click="aiForm.proxy_url = ''"
              >
                直连 (不使用代理)
              </button>
            </div>
          </div>

          <!-- Summary Template Setting -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="font-semibold text-theme-text">
                文档智能总结预设要求 (提示词结构模板)
              </label>
              <button
                type="button"
                class="text-[10px] text-theme-brand hover:underline cursor-pointer"
                @click="aiForm.summary_template = defaultSummaryTemplate"
              >
                恢复默认结构
              </button>
            </div>
            <textarea
              v-model="aiForm.summary_template"
              rows="6"
              placeholder="设置 AI 生成摘要时的章节结构、字数要求或关注侧重点..."
              class="w-full rounded-md border border-theme-border bg-theme-background-elevated/70 px-3 py-2 text-xs outline-none focus:border-theme-brand font-mono text-[11px] leading-relaxed"
            ></textarea>
            <div class="mt-1 text-[10px] text-theme-text-muted">
              💡 提示：每次打开文档或点击“重新总结”时，AI 将按此预设规则与 Markdown 结构提炼核心内容与数学公式。
            </div>
          </div>

          <!-- Auto Summarize Toggle -->
          <div class="flex items-center justify-between pt-1 border-t border-theme-border pt-3">
            <div>
              <div class="font-semibold text-theme-text">自动生成文档深度总结</div>
              <div class="text-[11px] text-theme-text-muted">保存或打开文档时自动调用 AI 生成摘要</div>
            </div>
            <input
              v-model="aiForm.auto_summarize"
              type="checkbox"
              class="h-4 w-4 rounded text-theme-brand focus:ring-0 cursor-pointer"
            />
          </div>

          <!-- Connection Test Button & Actions -->
          <div class="flex items-center justify-between pt-3 border-t border-theme-border">
            <button
              type="button"
              class="rounded-md border border-theme-border bg-theme-background-elevated px-3 py-1.5 text-xs font-medium text-theme-text hover:border-theme-brand disabled:opacity-50 flex items-center gap-1.5"
              :disabled="isTesting"
              @click="runTestConnection"
            >
              <KeylineIcon :name="isTesting ? 'refresh' : 'check'" size="14" :class="isTesting ? 'animate-spin' : ''" />
              <span>{{ isTesting ? '测试中...' : '测试连通性' }}</span>
            </button>
            <button
              class="rounded-md bg-theme-brand px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-orange-600 disabled:opacity-50"
              :disabled="isSaving"
              @click="saveAiForm"
            >
              {{ isSaving ? '保存中...' : '保存配置' }}
            </button>
          </div>
          <div v-if="testResult" class="rounded-lg p-2.5 text-xs" :class="testResult.success ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'">
            {{ testResult.message }}
          </div>
        </div>

        <!-- Raw JSON Mode View (ccSwitch style) -->
        <div v-else-if="aiConfigMode === 'json'" class="space-y-3">
          <div class="text-[11px] text-theme-text-muted">
            支持直接粘贴 ccSwitch、OneAPI 或标准 OpenAI 格式的 JSON 配置。
          </div>
          <textarea
            v-model="rawJsonContent"
            rows="14"
            spellcheck="false"
            class="w-full font-mono text-[11.5px] rounded-lg border border-theme-border bg-theme-background-elevated/70 p-3 outline-none focus:border-theme-brand leading-relaxed"
          ></textarea>
          <div class="flex items-center justify-between pt-1">
            <button
              class="rounded border border-theme-border px-3 py-1 text-xs text-theme-text-muted hover:text-theme-text"
              @click="formatRawJson"
            >
              格式化 JSON
            </button>
            <button
              class="rounded-md bg-theme-brand px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-orange-600 disabled:opacity-50"
              :disabled="isSaving"
              @click="saveRawJson"
            >
              {{ isSaving ? '应用中...' : '保存并应用 JSON' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tab 3: Admin & Permissions (权限与管理) -->
      <div v-show="activeTab === 'admin'" class="flex-1 overflow-y-auto p-5 space-y-5 text-xs leading-relaxed">
        <!-- If Not Logged In as Admin (Visitor Mode) -->
        <div v-if="!isAdmin" class="space-y-4">
          <!-- Visitor Notice Card -->
          <div class="rounded-xl border border-sky-500/20 bg-sky-500/10 p-4 text-sky-800 dark:text-sky-300 space-y-2">
            <div class="flex items-center gap-2 font-bold text-sm">
              <KeylineIcon name="user" size="18" />
              <span>当前身份：访客模式 (Visitor)</span>
            </div>
            <p class="text-[11.5px] leading-relaxed opacity-90">
              访客无需注册登录，仅能浏览管理员设为公开的笔记，并在文末发表讨论与留言；无法编辑或删除文档。如需管理笔记权限或黑名单，请登录管理员账号。
            </p>
          </div>

          <!-- Admin Login Card -->
          <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3.5">
            <div class="flex items-center gap-2 font-bold text-sm text-theme-text">
              <KeylineIcon name="lock" size="16" />
              <span>管理员登录 (Admin Login)</span>
            </div>
            
            <div class="space-y-2.5 pt-1">
              <div>
                <label class="block text-[11px] font-semibold text-theme-text mb-1">管理员账号</label>
                <input
                  v-model="loginForm.username"
                  type="text"
                  placeholder="admin"
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-3 py-2 text-xs outline-none focus:border-theme-brand"
                />
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-theme-text mb-1">管理员密码</label>
                <input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="输入管理员密码..."
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-3 py-2 text-xs outline-none focus:border-theme-brand"
                  @keydown.enter="handleAdminLogin"
                />
              </div>

              <div class="flex items-center justify-between pt-1">
                <label class="flex items-center gap-2 cursor-pointer select-none text-theme-text-muted hover:text-theme-text">
                  <input
                    v-model="loginForm.rememberMe"
                    type="checkbox"
                    class="h-4 w-4 rounded text-theme-brand focus:ring-0 cursor-pointer"
                  />
                  <span>记住登录状态 (持久保存免反复输入)</span>
                </label>
              </div>

              <button
                class="w-full mt-2 rounded-lg bg-theme-brand py-2 text-xs font-bold text-white shadow-md shadow-orange-500/20 hover:bg-orange-600 disabled:opacity-50 transition"
                :disabled="isLoggingIn || !loginForm.username || !loginForm.password"
                @click="handleAdminLogin"
              >
                {{ isLoggingIn ? '登录中...' : '登录管理员账号' }}
              </button>
            </div>
          </div>
        </div>

        <!-- If Logged In as Admin -->
        <div v-else class="space-y-5">
          <!-- Admin Status Header -->
          <div class="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-emerald-800 dark:text-emerald-300">
            <div class="flex items-center gap-2">
              <span class="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span class="font-bold text-xs">已登录为管理员 (拥有全部权限)</span>
            </div>
            <button
              class="rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-[11px] font-bold text-red-500 hover:bg-red-500 hover:text-white transition"
              @click="handleAdminLogout"
            >
              退出登录
            </button>
          </div>

          <!-- Section 1: 对外开放文档选择 (直接多选) -->
          <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 font-bold text-theme-text">
                <KeylineIcon name="book-open" size="16" />
                <span>对外开放文档选择</span>
              </div>
              <div class="flex items-center gap-1.5 text-[11px]">
                <button
                  type="button"
                  class="rounded bg-theme-brand/10 border border-theme-brand/30 px-2.5 py-0.5 font-semibold text-theme-brand hover:bg-theme-brand hover:text-white transition"
                  @click="selectAllPublic(true)"
                >
                  全选
                </button>
                <button
                  type="button"
                  class="rounded border border-theme-border bg-theme-background px-2.5 py-0.5 text-theme-text-muted hover:text-theme-text transition"
                  @click="selectAllPublic(false)"
                >
                  全不选
                </button>
              </div>
            </div>

            <p class="text-[11px] text-theme-text-muted leading-relaxed">
              直接勾选允许访客浏览与留言的文档。未勾选的文档将自动隐藏，仅管理员登录后可见。
            </p>

            <!-- Document List with Checkboxes -->
            <div
              v-if="allFolderNotes.length === 0"
              class="py-6 text-center text-xs text-theme-text-muted"
            >
              当前数据库文件夹内暂无 Markdown 文档
            </div>
            <div
              v-else
              class="max-h-64 overflow-y-auto rounded-lg border border-theme-border bg-theme-background-elevated/60 divide-y divide-theme-border/40"
            >
              <label
                v-for="n in allFolderNotes"
                :key="n.title"
                class="flex items-center justify-between p-2.5 hover:bg-theme-background-elevated cursor-pointer transition select-none"
              >
                <div class="flex items-center gap-2.5 min-w-0 pr-2">
                  <input
                    type="checkbox"
                    :value="n.title"
                    v-model="selectedPublicNotes"
                    class="h-4 w-4 rounded text-theme-brand focus:ring-0 cursor-pointer shrink-0"
                  />
                  <span class="truncate text-xs font-medium text-theme-text" :title="n.title">{{ n.title }}</span>
                </div>
                <span
                  class="shrink-0 text-[10px] px-1.5 py-0.5 rounded font-semibold"
                  :class="selectedPublicNotes.includes(n.title) ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-slate-500/15 text-theme-text-muted'"
                >
                  {{ selectedPublicNotes.includes(n.title) ? '公开' : '私密' }}
                </span>
              </label>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="text-[11px] text-theme-text-muted">
                已选公开 <strong class="text-theme-brand">{{ selectedPublicNotes.length }}</strong> / {{ allFolderNotes.length }} 篇文档
              </span>
              <button
                type="button"
                class="rounded-lg bg-theme-brand px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-orange-600 transition disabled:opacity-50"
                :disabled="isSavingPublicNotes"
                @click="savePublicNotes"
              >
                {{ isSavingPublicNotes ? '保存中...' : '保存对外设置' }}
              </button>
            </div>
          </div>

          <!-- Section 2: IP Tracking & Blacklist -->
          <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 font-bold text-theme-text">
                <KeylineIcon name="network" size="16" />
                <span>访客 IP 监控与拉黑管理</span>
              </div>
              <button
                class="flex items-center gap-1 rounded bg-theme-background-elevated px-2 py-0.5 text-[10px] text-theme-text-muted hover:text-theme-text"
                @click="loadSecurityData"
              >
                <KeylineIcon name="refresh" size="11" />
                <span>刷新</span>
              </button>
            </div>
            <p class="text-[11px] text-theme-text-muted">
              记录访问来源 IP、频次及活跃时间。被拉黑的 IP 将被系统全局 403 阻断访问。
            </p>

            <!-- Manual Blacklist Input -->
            <div class="flex gap-1.5 pt-1">
              <input
                v-model="manualBlacklistIp"
                type="text"
                placeholder="输入要拉黑的 IP 地址 (如 192.168.1.100)..."
                class="flex-1 rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs outline-none focus:border-red-500"
                @keydown.enter="handleManualBlacklist"
              />
              <button
                class="rounded-md bg-red-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-red-700 disabled:opacity-50"
                :disabled="!manualBlacklistIp.trim()"
                @click="handleManualBlacklist"
              >
                手动拉黑
              </button>
            </div>

            <!-- IP List / Table -->
            <div class="max-h-60 overflow-y-auto rounded-lg border border-theme-border bg-theme-background-elevated/60">
              <div v-if="ipStatsList.length === 0" class="py-8 text-center text-theme-text-muted">
                暂无访问记录
              </div>
              <div
                v-for="item in ipStatsList"
                :key="item.ip"
                class="flex items-center justify-between border-b border-theme-border/50 p-2.5 last:border-0"
              >
                <div class="space-y-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-mono font-bold text-theme-text">{{ item.ip }}</span>
                    <span
                      v-if="item.is_blacklisted"
                      class="rounded bg-red-500/15 px-1.5 py-0.2 text-[10px] font-bold text-red-500"
                    >
                      已拉黑
                    </span>
                    <span
                      v-else
                      class="rounded bg-emerald-500/15 px-1.5 py-0.2 text-[10px] font-bold text-emerald-500"
                    >
                      正常
                    </span>
                  </div>
                  <div class="text-[10px] text-theme-text-muted">
                    访问次数: <strong class="text-theme-text">{{ item.count }}</strong> 次 · 最近活跃: {{ formatTime(item.last_visit) }}
                  </div>
                </div>

                <button
                  class="rounded px-2.5 py-1 text-[11px] font-semibold transition"
                  :class="item.is_blacklisted ? 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500 hover:text-white' : 'border border-red-500/30 bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white'"
                  @click="handleToggleIpBlacklist(item.ip, !item.is_blacklisted)"
                >
                  {{ item.is_blacklisted ? '解除拉黑' : '拉黑此 IP' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Section 3: Database / Storage Directory Setting -->
          <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 font-bold text-theme-text">
                <KeylineIcon name="folder-open" size="16" />
                <span>数据库存储目录设置 (设备任意文件夹)</span>
              </div>
              <button
                class="flex items-center gap-1 rounded bg-theme-background-elevated px-2 py-0.5 text-[10px] text-theme-text-muted hover:text-theme-text"
                @click="loadStorageInfo"
              >
                <KeylineIcon name="refresh" size="11" />
                <span>刷新</span>
              </button>
            </div>
            <p class="text-[11px] text-theme-text-muted">
              指定设备宿主机本地的任意文件夹作为笔记数据存储库（Markdown 文件存储）。切换后即刻生效，系统配置将自动保存并在重启后保留。
            </p>

            <!-- Current Active Directory Info -->
            <div class="rounded-lg border border-theme-border/70 bg-theme-background-elevated/70 p-2.5 space-y-2">
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-theme-text-muted">当前数据存储路径:</span>
                <span class="rounded bg-theme-brand/10 px-1.5 py-0.5 text-[10px] font-semibold text-theme-brand">
                  {{ storageInfo.notes_count ?? 0 }} 篇笔记
                </span>
              </div>
              <div class="font-mono text-xs font-semibold text-theme-text break-all bg-theme-background px-2 py-1 rounded border border-theme-border/50">
                {{ storageInfo.current_path || '加载中...' }}
              </div>
              <div class="flex items-center justify-between pt-1">
                <span class="text-[10px] text-theme-text-muted">如直接在主机上增删了 Markdown 文件，可点击立即同步：</span>
                <button
                  type="button"
                  class="flex items-center gap-1.5 rounded-md bg-theme-brand/10 border border-theme-brand/30 px-2.5 py-1 text-xs font-bold text-theme-brand hover:bg-theme-brand hover:text-white transition disabled:opacity-50"
                  :disabled="isSyncingStorage"
                  @click="handleManualSyncStorage"
                >
                  <KeylineIcon :name="isSyncingStorage ? 'refresh' : 'check'" size="13" :class="isSyncingStorage ? 'animate-spin' : ''" />
                  <span>{{ isSyncingStorage ? '全库同步重构中...' : '一键同步并重建索引' }}</span>
                </button>
              </div>
            </div>

            <!-- Path Input & Action Buttons -->
            <div class="space-y-2 pt-1">
              <label class="block text-[11px] font-bold text-theme-text-muted">指定新的数据库目录路径：</label>
              <div class="flex gap-1.5">
                <input
                  v-model="newStoragePathInput"
                  type="text"
                  placeholder="输入或浏览选择设备绝对路径 (如 /home/user/my_notes)..."
                  class="flex-1 rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs font-mono outline-none focus:border-theme-brand"
                  @keydown.enter="handleSwitchStorage"
                />
                <button
                  type="button"
                  class="rounded-md border border-theme-border bg-theme-background-elevated px-2.5 py-1.5 text-xs font-medium text-theme-text hover:border-theme-brand hover:text-theme-brand transition flex items-center gap-1 shrink-0"
                  @click="toggleDirBrowser"
                >
                  <KeylineIcon :name="isBrowsingDir ? 'chevron-down' : 'folder'" size="13" />
                  <span>{{ isBrowsingDir ? '收起浏览' : '浏览设备' }}</span>
                </button>
                <button
                  class="rounded-md bg-theme-brand px-3 py-1.5 text-xs font-bold text-white hover:bg-orange-600 disabled:opacity-50 transition shrink-0"
                  :disabled="isSwitchingStorage || !newStoragePathInput.trim() || newStoragePathInput.trim() === storageInfo.current_path"
                  @click="handleSwitchStorage"
                >
                  {{ isSwitchingStorage ? '切换中...' : '确认切换' }}
                </button>
              </div>

              <!-- Sync Migrate Checkbox -->
              <label class="flex items-center gap-2 cursor-pointer text-[11.5px] text-theme-text font-medium select-none pt-0.5">
                <input
                  v-model="copyExistingOnSwitch"
                  type="checkbox"
                  class="h-4 w-4 rounded text-theme-brand focus:ring-0 cursor-pointer"
                />
                <span>同时将当前库的所有笔记与附件完整同步复制到新目录 (推荐保留勾选)</span>
              </label>
            </div>

            <!-- Embedded Directory Browser -->
            <div
              v-if="isBrowsingDir"
              class="rounded-lg border border-theme-border bg-theme-background-elevated p-2.5 space-y-2"
            >
              <div class="flex items-center justify-between border-b border-theme-border pb-2 text-[11px]">
                <div class="flex items-center gap-1 text-theme-text-muted truncate max-w-[70%]">
                  <span class="font-bold">浏览位置:</span>
                  <span class="font-mono text-theme-text truncate" :title="browseCurrentPath">{{ browseCurrentPath || '/' }}</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <button
                    v-if="browseParentPath"
                    type="button"
                    class="rounded border border-theme-border bg-theme-background px-2 py-0.5 text-[10px] hover:border-theme-brand text-theme-text transition"
                    @click="fetchBrowseDir(browseParentPath)"
                  >
                    上级目录 ↑
                  </button>
                  <button
                    type="button"
                    class="rounded bg-theme-brand/10 border border-theme-brand/30 px-2 py-0.5 text-[10px] text-theme-brand font-semibold hover:bg-theme-brand hover:text-white transition"
                    @click="selectBrowsedDir(browseCurrentPath)"
                  >
                    选用当前目录
                  </button>
                </div>
              </div>

              <div v-if="isLoadingBrowse" class="py-4 text-center text-xs text-theme-text-muted">
                读取设备目录中...
              </div>
              <div
                v-else-if="browseSubdirs.length === 0"
                class="py-4 text-center text-xs text-theme-text-muted"
              >
                当前目录下无子文件夹或无访问权限
              </div>
              <div
                v-else
                class="max-h-48 overflow-y-auto divide-y divide-theme-border/40 text-xs"
              >
                <div
                  v-for="sub in browseSubdirs"
                  :key="sub.path"
                  class="flex items-center justify-between py-1.5 px-2 rounded hover:bg-theme-background-elevated/80 group transition"
                >
                  <div
                    class="flex items-center gap-2 cursor-pointer truncate max-w-[75%]"
                    @click="fetchBrowseDir(sub.path)"
                    :title="sub.path"
                  >
                    <KeylineIcon name="folder" size="13" className="text-amber-500 shrink-0" />
                    <span class="font-mono text-theme-text group-hover:text-theme-brand truncate">{{ sub.name }}</span>
                  </div>
                  <button
                    type="button"
                    class="rounded border border-theme-border px-1.5 py-0.5 text-[10px] text-theme-text-muted hover:border-theme-brand hover:text-theme-brand opacity-80 group-hover:opacity-100 transition"
                    @click="selectBrowsedDir(sub.path)"
                  >
                    选择
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Section 4: Change Admin Password -->
          <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
            <div class="flex items-center gap-2 font-bold text-theme-text">
              <KeylineIcon name="lock" size="16" />
              <span>修改管理员密码</span>
            </div>
            <p class="text-[11px] text-theme-text-muted">
              更新系统管理模式登录密码，修改后立即生效并持久化。下次登录请使用新密码。
            </p>

            <div class="space-y-2.5 pt-1">
              <div>
                <label class="block text-[11px] font-bold text-theme-text-muted mb-1">当前原密码</label>
                <input
                  v-model="pwdForm.oldPassword"
                  type="password"
                  placeholder="输入当前管理员密码..."
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs outline-none focus:border-theme-brand"
                />
              </div>
              <div>
                <label class="block text-[11px] font-bold text-theme-text-muted mb-1">新管理员密码</label>
                <input
                  v-model="pwdForm.newPassword"
                  type="password"
                  placeholder="输入新密码 (至少 6 位)..."
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs outline-none focus:border-theme-brand"
                />
              </div>
              <div>
                <label class="block text-[11px] font-bold text-theme-text-muted mb-1">确认新密码</label>
                <input
                  v-model="pwdForm.confirmPassword"
                  type="password"
                  placeholder="再次输入新密码以确认..."
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs outline-none focus:border-theme-brand"
                  @keydown.enter="handleChangePassword"
                />
              </div>

              <div class="pt-1">
                <button
                  class="w-full rounded-md bg-theme-brand py-2 text-xs font-bold text-white hover:bg-orange-600 disabled:opacity-50 transition"
                  :disabled="isChangingPassword || !pwdForm.oldPassword || !pwdForm.newPassword || !pwdForm.confirmPassword"
                  @click="handleChangePassword"
                >
                  {{ isChangingPassword ? '正在保存密码...' : '确认更新管理员密码' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Section 5: Custom Site Title & Branding -->
          <div class="rounded-xl border border-theme-border bg-theme-background-elevated/40 p-4 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 font-bold text-theme-text">
                <KeylineIcon name="edit" size="16" />
                <span>自定义网页名称与平台标题</span>
              </div>
              <button
                type="button"
                class="text-[10px] text-theme-brand hover:underline cursor-pointer"
                @click="resetSiteBrandingDefaults"
              >
                恢复默认名称
              </button>
            </div>
            <p class="text-[11px] text-theme-text-muted">
              自定义左上角主图标旁的网站名称与副标题，保存后将同步更新浏览器标签页标题与全站品牌标识。
            </p>

            <div class="space-y-2.5 pt-1">
              <div>
                <label class="block text-[11px] font-bold text-theme-text-muted mb-1">主标题 (如 siwannote 或 我的知识库)</label>
                <input
                  v-model.trim="siteBrandingForm.title"
                  type="text"
                  placeholder="输入网页名称..."
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs font-mono outline-none focus:border-theme-brand"
                />
              </div>
              <div>
                <label class="block text-[11px] font-bold text-theme-text-muted mb-1">副标题 (如 SLAM & KNOWLEDGE LAB)</label>
                <input
                  v-model.trim="siteBrandingForm.subtitle"
                  type="text"
                  placeholder="输入副标题..."
                  class="w-full rounded-md border border-theme-border bg-theme-background-elevated/80 px-2.5 py-1.5 text-xs outline-none focus:border-theme-brand"
                />
              </div>

              <!-- Live Preview -->
              <div class="rounded-lg border border-theme-border/60 bg-theme-background p-2.5 space-y-1">
                <span class="text-[10px] text-theme-text-muted font-bold block">实时预览效果：</span>
                <div class="flex items-center gap-2">
                  <span class="font-bold text-base text-theme-text font-mono">{{ siteBrandingForm.title || 'siwannote' }}</span>
                  <span v-if="siteBrandingForm.subtitle" class="text-[10px] text-theme-brand font-semibold px-1.5 py-0.5 rounded bg-theme-brand/10">
                    {{ siteBrandingForm.subtitle }}
                  </span>
                </div>
              </div>

              <div class="pt-1">
                <button
                  class="w-full rounded-md bg-theme-brand py-2 text-xs font-bold text-white hover:bg-orange-600 disabled:opacity-50 transition"
                  :disabled="isSavingSiteBranding || !siteBrandingForm.title"
                  @click="handleSaveSiteBranding"
                >
                  {{ isSavingSiteBranding ? '正在保存...' : '保存网页名称配置' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>


    </aside>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import KeylineIcon from "./KeylineIcon.vue";
import { authTypes, params, searchSortOptions } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { applyTheme as setGlobalTheme, getSavedTheme } from "../helpers.js";
import { storeToken, getStoredToken, clearStoredToken } from "../tokenStorage.js";
import {
  getAiConfig,
  updateAiConfig,
  getAiRawJson,
  updateAiRawJson,
  testAiConnection,
  loginAdmin,
  getSecurityStatus,
  getPublicNotes,
  updatePublicNotes,
  getIpStats,
  toggleIpBlacklist,
  getNotes,
  changeAdminPassword,
  getStorageInfo,
  setStoragePath,
  browseDirectory,
  getSiteConfig,
  updateSiteConfig,
  syncStorageIndex,
} from "../api.js";

const props = defineProps({
  modelValue: Boolean,
});

const emit = defineEmits(["update:modelValue", "toggleSearchModal"]);

const globalStore = useGlobalStore();
const router = useRouter();
const toast = useToast();

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const activeTab = ref("page");
const aiConfigMode = ref("form"); // 'form' | 'json'

// Page Width: 3 presets (紧凑, 标准, 全宽)
function normalizeWidth(width) {
  if (width === "100%") return "100%";
  if (width === "1024px" || width === "1120px" || width === "1180px") return "1180px";
  return "1440px";
}

const currentPageWidth = ref(normalizeWidth(localStorage.getItem("siwan_page_width")));
const pageWidthOptions = [
  { label: "紧凑 (1180px)", value: "1180px" },
  { label: "标准 (1440px)", value: "1440px" },
  { label: "全宽 (100%)", value: "100%" },
];

const pageWidthLabel = computed(() => {
  const match = pageWidthOptions.find((o) => o.value === currentPageWidth.value);
  return match ? match.label : currentPageWidth.value;
});

function setPageWidth(width) {
  const normalized = normalizeWidth(width);
  currentPageWidth.value = normalized;
  localStorage.setItem("siwan_page_width", normalized);
  applyPageWidthToDom(normalized);
  // Sync with App.vue's responsive width binding
  window.dispatchEvent(new CustomEvent("siwan-page-width-changed", { detail: normalized }));
}

function applyPageWidthToDom(width) {
  const contentContainers = document.querySelectorAll("[data-app-content]");
  contentContainers.forEach((el) => {
    if (el.classList.contains("min-h-screen") && !el.classList.contains("mx-auto")) {
      el.style.maxWidth = "";
      return;
    }
    el.style.maxWidth = width;
  });
  // Clean up any stale inline maxWidth on outer root container if present
  const appRoot = document.querySelector("#app > div");
  if (appRoot && !appRoot.classList.contains("mx-auto") && appRoot.style.maxWidth) {
    appRoot.style.maxWidth = "";
  }
}

// Theme
const currentThemeMode = ref(getSavedTheme() || "eye-care");
function setTheme(mode) {
  currentThemeMode.value = mode;
  setGlobalTheme(mode);
}

// Editor Tooltip Preferences
const hideFormatTooltips = ref(true);
function updateEditorPreferences() {
  localStorage.setItem("siwan_hide_tooltips", hideFormatTooltips.value ? "1" : "0");
  applyTooltipStyle();
}

function applyTooltipStyle() {
  let styleEl = document.getElementById("siwan-editor-tooltip-style");
  if (!styleEl) {
    styleEl = document.createElement("style");
    styleEl.id = "siwan-editor-tooltip-style";
    document.head.appendChild(styleEl);
  }
  if (hideFormatTooltips.value) {
    styleEl.innerHTML = `
      .toastui-editor-tooltip { display: none !important; }
      .toastui-editor-popup-add-heading { font-size: 12px; }
    `;
  } else {
    styleEl.innerHTML = "";
  }
}

// AI Form
const isSaving = ref(false);
const isTesting = ref(false);
const hasExistingKey = ref(false);
const maskedKey = ref("");
const showApiKey = ref(false);
const testResult = ref(null);

const defaultSummaryTemplate = `请严格按以下格式输出，内容紧凑、重点突出，包含：
📌 核心主旨与背景（1~2 句话概括定位）

⚙️ 核心技术架构与算法机制（提炼 2-3 条要点）

📊 关键实验指标与对标结论（若文档包含实验实测数据，重点提炼）

💡 关键价值与后续启发（1~2 条）`;

const aiForm = ref({
  api_base: "https://api.openai.com/v1",
  api_key: "",
  model: "gpt-4o-mini",
  proxy_url: "",
  auto_summarize: true,
  summary_template: defaultSummaryTemplate,
});

const rawJsonContent = ref("");

const providerPresets = [
  { name: "DeepSeek 官方", api_base: "https://api.deepseek.com/v1", model: "deepseek-chat" },
  { name: "OpenAI 官方", api_base: "https://api.openai.com/v1", model: "gpt-4o-mini" },
  { name: "EdgeFn (ccSwitch)", api_base: "https://api.edgefn.net/v1", model: "DeepSeek-R1-0528-Qwen3-8B" },
  { name: "硅基流动", api_base: "https://api.siliconflow.cn/v1", model: "deepseek-ai/DeepSeek-V3" },
  { name: "Ollama 本地", api_base: "http://127.0.0.1:11434/v1", model: "qwen2.5:7b" },
];

function applyProviderPreset(p) {
  aiForm.value.api_base = p.api_base;
  aiForm.value.model = p.model;
}

async function loadAiData() {
  try {
    const data = await getAiConfig();
    if (data) {
      aiForm.value.api_base = data.api_base || "https://api.openai.com/v1";
      aiForm.value.model = data.model || "gpt-4o-mini";
      aiForm.value.proxy_url = data.proxy_url ?? "";
      aiForm.value.auto_summarize = data.auto_summarize ?? true;
      aiForm.value.summary_template = data.summary_template || defaultSummaryTemplate;
      hasExistingKey.value = data.has_key;
      maskedKey.value = data.masked_key || "";
    }
    const raw = await getAiRawJson();
    if (raw?.raw_json) {
      rawJsonContent.value = raw.raw_json;
    }
  } catch (err) {
    console.warn("[SettingsPanel] Load AI error:", err);
  }
}

function switchToFormMode() {
  aiConfigMode.value = "form";
  loadAiData();
}

async function switchToJsonMode() {
  aiConfigMode.value = "json";
  try {
    const raw = await getAiRawJson();
    if (raw?.raw_json) {
      rawJsonContent.value = raw.raw_json;
    }
  } catch (_) {}
}

async function runTestConnection() {
  isTesting.value = true;
  testResult.value = null;
  try {
    // First save form so test uses latest
    await updateAiConfig({
      api_base: aiForm.value.api_base,
      api_key: aiForm.value.api_key || undefined,
      model: aiForm.value.model,
      proxy_url: aiForm.value.proxy_url,
      auto_summarize: aiForm.value.auto_summarize,
      summary_template: aiForm.value.summary_template,
    });
    const res = await testAiConnection();
    testResult.value = { success: true, message: `✓ ${res.message}` };
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || "测试失败";
    testResult.value = { success: false, message: `❌ 连接失败: ${msg}` };
  } finally {
    isTesting.value = false;
  }
}

async function saveAiForm() {
  isSaving.value = true;
  try {
    await updateAiConfig({
      api_base: aiForm.value.api_base,
      api_key: aiForm.value.api_key || undefined,
      model: aiForm.value.model,
      proxy_url: aiForm.value.proxy_url,
      auto_summarize: aiForm.value.auto_summarize,
      summary_template: aiForm.value.summary_template,
    });
    toast.add({
      severity: "success",
      summary: "保存成功",
      detail: "AI 助手与网络代理配置已更新！",
      life: 2500,
    });
    aiForm.value.api_key = "";
    loadAiData();
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "保存失败",
      detail: err.message || "未能保存配置",
      life: 3000,
    });
  } finally {
    isSaving.value = false;
  }
}

function formatRawJson() {
  try {
    const parsed = JSON.parse(rawJsonContent.value);
    rawJsonContent.value = JSON.stringify(parsed, null, 2);
  } catch (err) {
    toast.add({ severity: "warn", summary: "JSON 格式错误", detail: err.message, life: 2500 });
  }
}

async function saveRawJson() {
  isSaving.value = true;
  try {
    await updateAiRawJson(rawJsonContent.value);
    toast.add({
      severity: "success",
      summary: "应用成功",
      detail: "ccSwitch 风格 JSON 配置已更新并加载！",
      life: 2500,
    });
    loadAiData();
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || "保存失败";
    toast.add({
      severity: "error",
      summary: "保存失败",
      detail: msg,
      life: 3500,
    });
  } finally {
    isSaving.value = false;
  }
}

// Admin & Security Management
const isAdmin = ref(false);
const isLoggingIn = ref(false);
const loginForm = ref({
  username: "admin",
  password: "",
  rememberMe: true,
});

// Public Document Selection
const allFolderNotes = ref([]);
const selectedPublicNotes = ref([]);
const isSavingPublicNotes = ref(false);

async function loadPublicNotesData() {
  try {
    const notesData = await getNotes("*", "title", "asc", 500);
    allFolderNotes.value = (notesData || []).sort((a, b) =>
      a.title.localeCompare(b.title, "zh-Hans-CN", { numeric: true, sensitivity: "base" })
    );

    const pubData = await getPublicNotes();
    const stored = pubData?.public_notes;
    if (Array.isArray(stored)) {
      const allTitles = new Set(allFolderNotes.value.map((n) => n.title));
      selectedPublicNotes.value = stored.filter((t) => allTitles.has(t));
    } else {
      selectedPublicNotes.value = allFolderNotes.value.map((n) => n.title);
    }
  } catch (err) {
    console.warn("[SettingsPanel] loadPublicNotesData error:", err);
  }
}

function selectAllPublic(select) {
  if (select) {
    selectedPublicNotes.value = allFolderNotes.value.map((n) => n.title);
  } else {
    selectedPublicNotes.value = [];
  }
}

async function savePublicNotes() {
  isSavingPublicNotes.value = true;
  try {
    const res = await updatePublicNotes(selectedPublicNotes.value);
    toast.add({
      severity: "success",
      summary: "设置已保存",
      detail: res.message || `已成功配置 ${selectedPublicNotes.value.length} 篇对外开放文档`,
      life: 3000,
    });
    window.dispatchEvent(new CustomEvent("siwan-storage-changed", { detail: { path: storageInfo.value.current_path } }));
    window.dispatchEvent(new CustomEvent("siwan-auth-changed"));
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "保存失败",
      detail: err.response?.data?.detail || "无法保存对外文档设置",
      life: 4000,
    });
  } finally {
    isSavingPublicNotes.value = false;
  }
}

const ipStatsList = ref([]);
const manualBlacklistIp = ref("");

// Storage Directory Management
const storageInfo = ref({
  current_path: "",
  source: "",
  total_notes: 0,
  total_attachments: 0,
});
const newStoragePathInput = ref("");
const isSwitchingStorage = ref(false);
const isSyncingStorage = ref(false);
const copyExistingOnSwitch = ref(false);
const isBrowsingDir = ref(false);
const browseCurrentPath = ref("");
const browseParentPath = ref(null);
const browseSubdirs = ref([]);
const isLoadingBrowse = ref(false);

// Admin Password Management
const pwdForm = ref({
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
});
const isChangingPassword = ref(false);

async function checkSecurityStatus() {
  try {
    const res = await getSecurityStatus();
    isAdmin.value = res.is_admin === true;
    if (isAdmin.value) {
      loadSecurityData();
    }
  } catch (err) {
    isAdmin.value = false;
  }
}

async function handleAdminLogin() {
  if (!loginForm.value.username || !loginForm.value.password) return;
  isLoggingIn.value = true;
  try {
    const res = await loginAdmin(
      loginForm.value.username,
      loginForm.value.password,
      loginForm.value.rememberMe
    );
    storeToken(res.access_token, loginForm.value.rememberMe);
    isAdmin.value = true;
    loginForm.value.password = "";
    toast.add({
      severity: "success",
      summary: "登录成功",
      detail: `欢迎回来，管理员 ${res.username}！`,
      life: 3000,
    });
    loadSecurityData();
    // Notify sidebar to reload notes with full admin view
    window.dispatchEvent(new CustomEvent("siwan-auth-changed"));
  } catch (err) {
    const detail = err.response?.data?.detail || "登录失败，请检查用户名和密码";
    toast.add({
      severity: "error",
      summary: "登录失败",
      detail,
      life: 4000,
    });
  } finally {
    isLoggingIn.value = false;
  }
}

function handleAdminLogout() {
  clearStoredToken();
  isAdmin.value = false;
  toast.add({
    severity: "info",
    summary: "已注销",
    detail: "已退出管理员模式，当前处于访客模式",
    life: 3000,
  });
  window.dispatchEvent(new CustomEvent("siwan-auth-changed"));
}

async function loadSecurityData() {
  loadStorageInfo();
  loadSiteBrandingSettings();
  loadPublicNotesData();
  try {
    const ipData = await getIpStats();
    const rawStats = ipData?.stats || (Array.isArray(ipData) ? ipData : []);
    const blacklistSet = new Set(ipData?.blacklist || []);
    ipStatsList.value = rawStats.map((item) => ({
      ...item,
      is_blacklisted: item.is_blacklisted !== undefined ? item.is_blacklisted : blacklistSet.has(item.ip),
      count: item.visits ?? item.count ?? 1,
      last_visit: item.last_seen || item.last_visit || "",
    }));
  } catch (err) {
    console.warn("[SettingsPanel] loadSecurityData ipData error:", err);
  }
}

async function handleToggleIpBlacklist(ip, blacklist) {
  try {
    const res = await toggleIpBlacklist(ip, blacklist);
    toast.add({
      severity: blacklist ? "warn" : "success",
      summary: blacklist ? "已拉黑 IP" : "已解除拉黑",
      detail: res.message || `${ip} 黑名单状态已更新`,
      life: 3000,
    });
    const updated = await getIpStats();
    const rawStats = updated?.stats || (Array.isArray(updated) ? updated : []);
    const blacklistSet = new Set(updated?.blacklist || []);
    ipStatsList.value = rawStats.map((item) => ({
      ...item,
      is_blacklisted: item.is_blacklisted !== undefined ? item.is_blacklisted : blacklistSet.has(item.ip),
      count: item.visits ?? item.count ?? 1,
      last_visit: item.last_seen || item.last_visit || "",
    }));
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "操作失败",
      detail: err.response?.data?.detail || "更改 IP 黑名单状态出错",
      life: 4000,
    });
  }
}

async function handleManualBlacklist() {
  const ip = manualBlacklistIp.value.trim();
  if (!ip) return;
  await handleToggleIpBlacklist(ip, true);
  manualBlacklistIp.value = "";
}

function formatTime(isoStr) {
  if (!isoStr) return "-";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("zh-CN", { hour12: false });
  } catch {
    return isoStr;
  }
}

// Storage Directory Methods
async function loadStorageInfo() {
  try {
    const data = await getStorageInfo();
    storageInfo.value = data;
    if (!newStoragePathInput.value) {
      newStoragePathInput.value = data.current_path;
    }
  } catch (err) {
    console.warn("[SettingsPanel] loadStorageInfo error:", err);
  }
}

async function fetchBrowseDir(path = "") {
  isLoadingBrowse.value = true;
  try {
    const res = await browseDirectory(path);
    browseCurrentPath.value = res.current || res.current_path || "";
    browseParentPath.value = res.parent !== undefined ? res.parent : res.parent_path;
    browseSubdirs.value = res.subdirs || res.subdirectories || [];
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "浏览目录失败",
      detail: err.response?.data?.detail || "无法读取指定设备目录",
      life: 3000,
    });
  } finally {
    isLoadingBrowse.value = false;
  }
}

function toggleDirBrowser() {
  isBrowsingDir.value = !isBrowsingDir.value;
  if (isBrowsingDir.value) {
    fetchBrowseDir(newStoragePathInput.value || storageInfo.value.current_path || "");
  }
}

function selectBrowsedDir(dirPath) {
  newStoragePathInput.value = dirPath;
}

async function handleManualSyncStorage() {
  isSyncingStorage.value = true;
  try {
    const res = await syncStorageIndex();
    toast.add({
      severity: "success",
      summary: "数据库同步成功",
      detail: res.message || "文档索引已全面重新扫描与重建！",
      life: 3500,
    });
    await loadStorageInfo();
    await loadSecurityData();
    window.dispatchEvent(new CustomEvent("siwan-storage-changed", { detail: { path: storageInfo.value.current_path } }));
    window.dispatchEvent(new CustomEvent("siwan-auth-changed"));
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "同步失败",
      detail: err.response?.data?.detail || "无法同步数据库索引",
      life: 4000,
    });
  } finally {
    isSyncingStorage.value = false;
  }
}

async function handleSwitchStorage() {
  const target = newStoragePathInput.value.trim();
  if (!target) {
    toast.add({
      severity: "warn",
      summary: "路径为空",
      detail: "请输入有效的本地设备目录路径",
      life: 3000,
    });
    return;
  }

  isSwitchingStorage.value = true;
  try {
    const res = await setStoragePath(target, true, copyExistingOnSwitch.value);
    toast.add({
      severity: "success",
      summary: "数据库目录已切换",
      detail: res.message || `存储目录已成功更改为: ${res.current_path}`,
      life: 4000,
    });
    await loadStorageInfo();
    await loadSecurityData();
    window.dispatchEvent(new CustomEvent("siwan-storage-changed", { detail: { path: res.current_path } }));
    window.dispatchEvent(new CustomEvent("siwan-auth-changed"));
    router.push({ name: "home" });
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "切换存储目录失败",
      detail: err.response?.data?.detail || "无法应用指定的存储目录，请检查权限或路径",
      life: 5000,
    });
  } finally {
    isSwitchingStorage.value = false;
  }
}

// Password Change Methods
async function handleChangePassword() {
  const { oldPassword, newPassword, confirmPassword } = pwdForm.value;
  if (!oldPassword) {
    toast.add({
      severity: "warn",
      summary: "表单不完整",
      detail: "请输入原管理员密码",
      life: 3000,
    });
    return;
  }
  if (!newPassword || newPassword.length < 6) {
    toast.add({
      severity: "warn",
      summary: "新密码太短",
      detail: "新密码长度至少需要 6 个字符",
      life: 3000,
    });
    return;
  }
  if (newPassword !== confirmPassword) {
    toast.add({
      severity: "error",
      summary: "密码不一致",
      detail: "两次输入的新密码不一致，请核对",
      life: 3000,
    });
    return;
  }

  isChangingPassword.value = true;
  try {
    const res = await changeAdminPassword(oldPassword, newPassword);
    toast.add({
      severity: "success",
      summary: "密码修改成功",
      detail: res.message || "管理员密码已更新，配置已保存",
      life: 3000,
    });
    pwdForm.value = {
      oldPassword: "",
      newPassword: "",
      confirmPassword: "",
    };
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "修改密码失败",
      detail: err.response?.data?.detail || "原密码错误或保存失败",
      life: 4000,
    });
  } finally {
    isChangingPassword.value = false;
  }
}

// Site Branding Customization
const siteBrandingForm = ref({
  title: globalStore.siteTitle || "siwannote",
  subtitle: globalStore.siteSubtitle || "SLAM & KNOWLEDGE LAB",
});
const isSavingSiteBranding = ref(false);

async function loadSiteBrandingSettings() {
  try {
    const data = await getSiteConfig();
    if (data.site_title) {
      siteBrandingForm.value.title = data.site_title;
      siteBrandingForm.value.subtitle = data.site_subtitle || "";
    }
  } catch (err) {
    console.warn("[SettingsPanel] loadSiteBranding error:", err);
  }
}

function resetSiteBrandingDefaults() {
  siteBrandingForm.value.title = "siwannote";
  siteBrandingForm.value.subtitle = "SLAM & KNOWLEDGE LAB";
}

async function handleSaveSiteBranding() {
  const title = siteBrandingForm.value.title.trim();
  if (!title) {
    toast.add({
      severity: "warn",
      summary: "标题为空",
      detail: "请输入有效的网站主标题",
      life: 3000,
    });
    return;
  }

  isSavingSiteBranding.value = true;
  try {
    const res = await updateSiteConfig(title, siteBrandingForm.value.subtitle.trim());
    globalStore.setSiteBranding(res.site_title, res.site_subtitle);
    toast.add({
      severity: "success",
      summary: "配置已更新",
      detail: res.message || "网页名称与副标题已保存",
      life: 3000,
    });
  } catch (err) {
    toast.add({
      severity: "error",
      summary: "保存失败",
      detail: err.response?.data?.detail || "无法保存网页名称配置",
      life: 4000,
    });
  } finally {
    isSavingSiteBranding.value = false;
  }
}

// Navigation Actions
function triggerSearch() {
  closePanel();
  emit("toggleSearchModal");
}

function triggerAllNotes() {
  closePanel();
  router.push({
    name: "search",
    query: {
      [params.searchTerm]: "*",
      [params.sortBy]: searchSortOptions.title,
    },
  });
}

function triggerNewNote() {
  closePanel();
  router.push({ name: "new" });
}

function logOut() {
  handleAdminLogout();
  closePanel();
}

function closePanel() {
  isOpen.value = false;
}

const showNewButton = computed(() => {
  return isAdmin.value && globalStore.config.authType !== authTypes.readOnly;
});

const showLogOutButton = computed(() => {
  return isAdmin.value;
});

onMounted(() => {
  const savedWidth = normalizeWidth(localStorage.getItem("siwan_page_width"));
  currentPageWidth.value = savedWidth;
  applyPageWidthToDom(savedWidth);

  const savedTooltips = localStorage.getItem("siwan_hide_tooltips");
  hideFormatTooltips.value = savedTooltips !== "0"; // default true
  applyTooltipStyle();

  loadAiData();
  checkSecurityStatus();

  window.addEventListener("siwan-storage-changed", loadPublicNotesData);
});

onBeforeUnmount(() => {
  window.removeEventListener("siwan-storage-changed", loadPublicNotesData);
});

watch(isOpen, (val) => {
  if (val) {
    loadAiData();
    checkSecurityStatus();
    const savedWidth = normalizeWidth(localStorage.getItem("siwan_page_width"));
    applyPageWidthToDom(savedWidth);
  }
});

watch(activeTab, (tab) => {
  if (tab === "admin") {
    checkSecurityStatus();
  }
});
</script>
