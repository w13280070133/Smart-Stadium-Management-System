<template>
  <router-view />
  
  <!-- 智能助手聊天组件 -->
  <ChatWidget />
</template>

<script setup lang="ts">
import ChatWidget from './components/ChatWidget.vue'
</script>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  background: #f3f4f6;
}

/* 确保聊天组件的 z-index 不被覆盖 */
* {
  position: relative;
  z-index: auto;
}

/* 保持聊天组件在最上层 */
.chat-widget {
  z-index: 9999 !important;
}
</style>
