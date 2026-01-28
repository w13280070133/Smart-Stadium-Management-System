<template>
  <div class="chat-widget">
    <!-- 聊天窗口 -->
    <transition name="slide-up">
      <div v-if="isOpen" class="chat-window">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="header-content">
            <span class="bot-icon">🤖</span>
            <div class="header-text">
              <h3>智能助手</h3>
              <p class="status">{{ isLoading ? '正在输入...' : '在线' }}</p>
            </div>
          </div>
          <button class="close-btn" @click="toggleChat" title="关闭">
            ✕
          </button>
        </div>

        <!-- 消息列表 -->
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-message">
            <span class="welcome-icon">👋</span>
            <h4>您好！我是智能助手</h4>
            <p>我可以帮您查询场地、了解规则等。请问有什么可以帮您的吗？</p>
          </div>

          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              {{ message.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-bubble">
              <div class="message-content" v-html="renderMarkdown(message.content)"></div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>

          <!-- 加载动画 -->
          <div v-if="isLoading" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入框 -->
        <div class="chat-input">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="输入消息..."
            @keypress.enter="sendMessage"
            :disabled="isLoading"
          />
          <button
            class="send-btn"
            @click="sendMessage"
            :disabled="isLoading || !inputMessage.trim()"
          >
            <span v-if="!isLoading">发送</span>
            <span v-else class="loading-spinner">⏳</span>
          </button>
        </div>
      </div>
    </transition>

    <!-- 悬浮按钮 -->
    <button class="chat-fab" @click="toggleChat" :class="{ active: isOpen }">
      <span class="fab-icon">{{ isOpen ? '✕' : '💬' }}</span>
      <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

// ============================================================================
// 状态管理
// ============================================================================

const isOpen = ref(false)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const sessionId = ref('')
const messagesContainer = ref(null)
const unreadCount = ref(0)

// ============================================================================
// 初始化
// ============================================================================

onMounted(() => {
  // 从 localStorage 读取或生成 session_id
  let storedSessionId = localStorage.getItem('chat_session_id')
  if (!storedSessionId) {
    storedSessionId = generateUUID()
    localStorage.setItem('chat_session_id', storedSessionId)
  }
  sessionId.value = storedSessionId

  // 从 sessionStorage 读取历史消息（更安全）
  const storedMessages = sessionStorage.getItem('chat_messages')
  if (storedMessages) {
    try {
      messages.value = JSON.parse(storedMessages)
    } catch (e) {
      console.error('Failed to parse stored messages:', e)
    }
  }
})

// 监听消息变化，保存到 sessionStorage（更安全，关闭浏览器后自动清除）
// 限制存储的消息数量，避免存储过多敏感信息
const MAX_STORED_MESSAGES = 20

watch(messages, (newMessages) => {
  // 只保存最近的消息，过滤敏感内容
  const messagesToStore = newMessages.slice(-MAX_STORED_MESSAGES).map(msg => ({
    role: msg.role,
    // 不存储可能包含敏感信息的完整内容，只存储前100个字符
    content: msg.content ? msg.content.substring(0, 500) + (msg.content.length > 500 ? '...' : '') : '',
    timestamp: msg.timestamp
  }))
  sessionStorage.setItem('chat_messages', JSON.stringify(messagesToStore))
}, { deep: true })

// ============================================================================
// 工具函数
// ============================================================================

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// 安全的 Markdown 渲染（加强 XSS 防护）
function renderMarkdown(text) {
  if (!text) return ''
  
  // 完整转义 HTML 特殊字符，防止 XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
  
  // 换行
  html = html.replace(/\n/g, '<br>')
  
  // 粗体（只允许安全的文本内容）
  html = html.replace(/\*\*([^*<>]+)\*\*/g, '<strong>$1</strong>')
  
  // 列表项（只处理安全的文本内容）
  html = html.replace(/^- ([^<>]+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>[^<>]*<\/li>)/s, '<ul>$1</ul>')
  
  // 数字列表
  html = html.replace(/^\d+\. ([^<>]+)$/gm, '<li>$1</li>')
  
  return html
}

// ============================================================================
// 聊天功能
// ============================================================================

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    unreadCount.value = 0
    nextTick(() => {
      scrollToBottom()
    })
  }
}

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message,
    timestamp: Date.now()
  })

  inputMessage.value = ''
  isLoading.value = true

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 创建一个空的 assistant 消息占位
  const assistantMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    timestamp: Date.now()
  })

  try {
    // 获取当前登录用户的 member_id
    const userInfoStr = localStorage.getItem('user_info') || localStorage.getItem('member_info')
    const memberId = userInfoStr ? JSON.parse(userInfoStr).id : null
    
    // 调用后端 API（流式）
    const response = await fetch('/api/agent/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId.value,
        member_id: memberId
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 使用 ReadableStream 读取流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    // 循环读取流
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        console.log('[ChatWidget] 流式响应完成')
        break
      }

      // 解码并追加到 assistant 消息
      const chunk = decoder.decode(value, { stream: true })
      messages.value[assistantMessageIndex].content += chunk

      // 实时滚动到底部
      await nextTick()
      scrollToBottom()
    }

    // 如果窗口未打开，增加未读计数
    if (!isOpen.value) {
      unreadCount.value++
    }

  } catch (error) {
    console.error('Failed to send message:', error)
    
    // 更新错误消息
    messages.value[assistantMessageIndex].content = '抱歉，发送消息时出现错误，请稍后再试。'
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 清空聊天记录
function clearChat() {
  if (confirm('确定要清空聊天记录吗？')) {
    messages.value = []
    localStorage.removeItem('chat_messages')
  }
}
</script>

<style scoped>
/* ============================================================================
   聊天组件容器
   ============================================================================ */
.chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* ============================================================================
   悬浮按钮
   ============================================================================ */
.chat-fab {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.chat-fab.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.fab-icon {
  font-size: 28px;
  line-height: 1;
}

.unread-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ff4757;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

/* ============================================================================
   聊天窗口
   ============================================================================ */
.chat-window {
  position: absolute;
  bottom: 80px;
  right: 0;
  width: 380px;
  height: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* ============================================================================
   头部
   ============================================================================ */
.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bot-icon {
  font-size: 32px;
  line-height: 1;
}

.header-text h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.header-text .status {
  margin: 2px 0 0 0;
  font-size: 12px;
  opacity: 0.9;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* ============================================================================
   消息列表
   ============================================================================ */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f7f8fc;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #4a5568;
}

.welcome-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.welcome-message h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #2d3748;
}

.welcome-message p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

/* 消息 */
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  position: relative;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: white;
  color: #2d3748;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 4px;
}

/* 输入中动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e0;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* ============================================================================
   输入框
   ============================================================================ */
.chat-input {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 12px;
}

.chat-input input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input input:focus {
  border-color: #667eea;
}

.chat-input input:disabled {
  background: #f7fafc;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* ============================================================================
   响应式
   ============================================================================ */
@media (max-width: 480px) {
  .chat-window {
    width: calc(100vw - 40px);
    height: calc(100vh - 100px);
    bottom: 80px;
    right: 20px;
  }
}
</style>
