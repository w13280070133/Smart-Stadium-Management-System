import { computed, ref } from "vue";
import { defineStore } from "pinia";

type ContrastMode = "light" | "dark" | "auto";

type NotificationPanelState = "closed" | "peek" | "open";

const CONTRAST_MODE_KEY = "gs-admin-contrast-mode";
const SIDEBAR_STATE_KEY = "gs-admin-sidebar-collapsed";

const readContrastPref = (): ContrastMode => {
  if (typeof window === "undefined") return "auto";
  const value = window.localStorage.getItem(CONTRAST_MODE_KEY) as ContrastMode | null;
  return value === "light" || value === "dark" || value === "auto" ? value : "auto";
};

const readSidebarPref = (): boolean => {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(SIDEBAR_STATE_KEY) === "collapsed";
};

export const useLayoutStore = defineStore("layout", () => {
  const sidebarCollapsed = ref(readSidebarPref());
  const contrastMode = ref<ContrastMode>(readContrastPref());
  const notificationState = ref<NotificationPanelState>("closed");
  const unreadCount = ref(0);

  const isDarkPreferred = computed(() => {
    if (contrastMode.value === "light") return false;
    if (contrastMode.value === "dark") return true;
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  const persistSidebar = (collapsed: boolean) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(SIDEBAR_STATE_KEY, collapsed ? "collapsed" : "expanded");
  };

  const persistContrast = (mode: ContrastMode) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(CONTRAST_MODE_KEY, mode);
  };

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value;
    persistSidebar(sidebarCollapsed.value);
  };

  const setSidebar = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed;
    persistSidebar(collapsed);
  };

  const setContrastMode = (mode: ContrastMode) => {
    contrastMode.value = mode;
    persistContrast(mode);
  };

  const openNotificationPanel = () => {
    notificationState.value = "open";
  };

  const closeNotificationPanel = () => {
    notificationState.value = "closed";
  };

  const peekNotificationPanel = () => {
    notificationState.value = "peek";
  };

  const setUnreadCount = (count: number) => {
    unreadCount.value = count;
  };

  return {
    // state
    sidebarCollapsed,
    contrastMode,
    notificationState,
    unreadCount,
    // getters
    isDarkPreferred,
    // actions
    toggleSidebar,
    setSidebar,
    setContrastMode,
    openNotificationPanel,
    closeNotificationPanel,
    peekNotificationPanel,
    setUnreadCount,
  };
});
