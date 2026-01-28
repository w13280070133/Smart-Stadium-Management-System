import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { pinia } from "./stores";
import { initTheme } from "./theme";

import ElementPlus from "element-plus";
import "element-plus/dist/index.css";

import zhCn from "element-plus/dist/locale/zh-cn.mjs"; // ★ 引入中文语言包

import "./theme/tokens.css";
import "./theme/element-plus.css";
import "./assets/main.css";

const app = createApp(App);

app.use(pinia);
initTheme(pinia);
app.use(router);
app.use(ElementPlus, { locale: zhCn }); // ★ 使用中文

app.mount("#app");
