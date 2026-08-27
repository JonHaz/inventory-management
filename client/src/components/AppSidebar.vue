<script setup>
import { computed } from 'vue'
import {
  LayoutDashboard,
  Boxes,
  ShoppingCart,
  Wallet,
  TrendingUp,
  FileText,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-vue-next'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'

const { t } = useI18n()
const { collapsedVisual, toggleSidebar } = useSidebar()

// Route table drives the nav. Adding a route means adding a row here rather than
// hand-copying another <router-link>. Note the deliberate mismatches carried over
// from the previous nav: /spending is labelled "Finance" and /demand is labelled
// "Demand Forecast" — the paths and the label keys are not meant to match.
const navItems = [
  { path: '/', labelKey: 'nav.overview', icon: LayoutDashboard },
  { path: '/inventory', labelKey: 'nav.inventory', icon: Boxes },
  { path: '/orders', labelKey: 'nav.orders', icon: ShoppingCart },
  { path: '/spending', labelKey: 'nav.finance', icon: Wallet },
  { path: '/demand', labelKey: 'nav.demandForecast', icon: TrendingUp },
  { path: '/reports', labelKey: 'nav.reports', icon: FileText }
]

// Compact mark that stands in for the full company name when collapsed. Words
// are only space-separated in English; Japanese collapses to its first glyph,
// which is the intended fallback rather than a bug.
const brandMark = computed(() => {
  const name = t('nav.companyName').trim()
  const words = name.split(/\s+/).filter(Boolean)
  if (words.length > 1) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
})
</script>

<template>
  <aside class="sidebar" :class="{ 'is-collapsed': collapsedVisual }">
    <div class="sidebar-brand">
      <template v-if="!collapsedVisual">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </template>
      <span v-else class="brand-mark" :title="t('nav.companyName')">{{ brandMark }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'is-active': $route.path === item.path }"
        :title="collapsedVisual ? t(item.labelKey) : null"
      >
        <component :is="item.icon" class="nav-icon" :size="20" aria-hidden="true" />
        <!-- The label is omitted from the DOM when collapsed, not merely hidden:
             a visually-hidden span still lands in the accessibility tree, so the
             :title tooltip above carries the name instead. -->
        <span v-if="!collapsedVisual" class="nav-label">{{ t(item.labelKey) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button
        type="button"
        class="collapse-toggle"
        :aria-label="collapsedVisual ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        @click="toggleSidebar"
      >
        <component
          :is="collapsedVisual ? ChevronsRight : ChevronsLeft"
          :size="18"
          aria-hidden="true"
        />
        <span v-if="!collapsedVisual">{{ t('nav.collapseSidebar') }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  flex: 0 0 var(--sidebar-width-expanded);
  width: var(--sidebar-width-expanded);
  height: 100vh;
  position: sticky;
  top: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  transition: flex-basis 0.2s ease, width 0.2s ease;
}

.sidebar.is-collapsed {
  flex-basis: var(--sidebar-width-collapsed);
  width: var(--sidebar-width-collapsed);
}

/* Brand block matches the top bar's height so the sidebar and the main column
   share one horizontal rule across the whole shell. */
.sidebar-brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-1);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-border);
  overflow: hidden;
}

.sidebar.is-collapsed .sidebar-brand {
  align-items: center;
  padding: 0 var(--space-2);
}

.brand-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
  white-space: nowrap;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--space-8);
  height: var(--space-8);
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 0.813rem;
  font-weight: 700;
  letter-spacing: 0.025em;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.938rem;
  font-weight: 500;
  white-space: nowrap;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.sidebar.is-collapsed .nav-item {
  justify-content: center;
  padding: var(--space-2);
}

.nav-item:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-subtle);
}

.nav-item:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.nav-item.is-active {
  color: var(--color-accent);
  background: var(--color-accent-soft);
}

/* Active state is a left accent bar. The old nav used a bottom underline, which
   reads as a tab strip rather than a sidebar once rotated into a column. */
.nav-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-1);
  bottom: var(--space-1);
  width: 3px;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
}

.nav-icon {
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 0.813rem;
  font-weight: 500;
  font-family: inherit;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}

.collapse-toggle:hover {
  color: var(--color-text-primary);
  border-color: var(--color-border-hover);
  background: var(--color-surface-subtle);
}

.collapse-toggle:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
</style>
