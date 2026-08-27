import { ref, computed } from 'vue'

const STORAGE_KEY = 'app-sidebar-collapsed'
const ICON_ONLY_QUERY = '(max-width: 1023px)'

// Shared sidebar state (singleton pattern — same shape as useFilters/useI18n:
// refs live at module scope so every importer sees one instance).

// The user's *manual* preference. Persisted, restored on load.
const savedCollapsed = typeof localStorage !== 'undefined'
  ? localStorage.getItem(STORAGE_KEY) === 'true'
  : false
const isCollapsed = ref(savedCollapsed)

// Viewport-forced icon-only mode. Deliberately NOT persisted and deliberately a
// *separate* boolean from isCollapsed: if the two were merged, resizing the
// window below 1024px would overwrite (and permanently destroy) the user's
// manual preference. Keeping them independent means a trip below the breakpoint
// and back restores exactly what the user chose.
const isIconOnly = ref(false)

// matchMedia rather than a CSS @media query because icon-only mode renders
// *different DOM* — the label element is omitted entirely and a title tooltip is
// added — which CSS cannot express. A CSS-hidden label would still occupy the
// accessibility tree and the tab order.
if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
  const mql = window.matchMedia(ICON_ONLY_QUERY)
  isIconOnly.value = mql.matches
  // Registered once at module level (not per-component) so the listener count
  // stays at one no matter how many components consume this composable.
  mql.addEventListener('change', (event) => {
    isIconOnly.value = event.matches
  })
}

// What components actually render against: either reason collapses the sidebar.
const collapsedVisual = computed(() => isCollapsed.value || isIconOnly.value)

export function useSidebar() {
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
    }
  }

  return {
    isCollapsed,
    isIconOnly,
    collapsedVisual,
    toggleSidebar
  }
}
