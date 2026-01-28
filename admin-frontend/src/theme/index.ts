import { watch } from "vue";
import type { Pinia } from "pinia";
import { useLayoutStore } from "../stores/layout";

type CleanupFn = () => void;

const setThemeOnDocument = (isDark: boolean) => {
  const themeValue = isDark ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", themeValue);
  document.documentElement.style.setProperty("color-scheme", themeValue);
};

const setSidebarState = (collapsed: boolean) => {
  document.body.dataset.sidebar = collapsed ? "collapsed" : "expanded";
};

export const initTheme = (pinia: Pinia): CleanupFn => {
  const layoutStore = useLayoutStore(pinia);
  const media = window.matchMedia?.("(prefers-color-scheme: dark)");

  const computeIsDark = () => {
    if (layoutStore.contrastMode === "dark") return true;
    if (layoutStore.contrastMode === "light") return false;
    return media?.matches ?? false;
  };

  const applyTheme = () => {
    setThemeOnDocument(computeIsDark());
  };

  const stopThemeWatch = watch(
    () => layoutStore.contrastMode,
    () => {
      applyTheme();
    },
    { immediate: true }
  );

  const mediaHandler = () => {
    if (layoutStore.contrastMode === "auto") {
      applyTheme();
    }
  };

  media?.addEventListener("change", mediaHandler);

  const stopSidebarWatch = watch(
    () => layoutStore.sidebarCollapsed,
    (collapsed) => {
      setSidebarState(collapsed);
    },
    { immediate: true }
  );

  return () => {
    stopThemeWatch();
    stopSidebarWatch();
    media?.removeEventListener("change", mediaHandler);
  };
};
