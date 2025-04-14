<template>
  <div class="chat-view">
    <div class="page-header">
      <h1 class="text-3xl font-bold">Chat</h1>
      <p class="text-gray-600 mt-2">Interact with the AI assistant</p>
    </div>
    <div class="chat-container">
      <div class="messages" ref="messagesContainer">
        <div v-for="(message, index) in messages" :key="index" class="message" :class="message.type">
          <div class="message-content">
            <div class="message-header">
              <span class="sender">{{ message.sender }}</span>
              <span class="timestamp">{{ formatTimestamp(message.timestamp) }}</span>
            </div>
            <div class="message-text" v-html="formatMessage(message.text)"></div>
          </div>
        </div>
      </div>
      
      <div class="input-container">
        <textarea 
          v-model="newMessage" 
          @keydown.enter.prevent="sendMessage"
          placeholder="Type your message here..."
          rows="3"
          class="message-input"
        ></textarea>
        <button @click="sendMessage" class="send-button" :disabled="!newMessage.trim()">
          Send
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import marked from 'marked'

export default {
  name: 'ChatView',
  setup() {
    const messages = ref([])
    const newMessage = ref('')
    const messagesContainer = ref(null)

    const sendMessage = async () => {
      if (!newMessage.value.trim()) return

      const message = {
        text: newMessage.value,
        sender: 'You',
        timestamp: new Date(),
        type: 'user'
      }

      messages.value.push(message)
      newMessage.value = ''

      // Simulate AI response (replace with actual API call)
      setTimeout(() => {
        messages.value.push({
          text: 'This is a simulated response. Replace with actual API integration.',
          sender: 'AI',
          timestamp: new Date(),
          type: 'ai'
        })
        scrollToBottom()
      }, 1000)
    }

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    const formatTimestamp = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }

    const formatMessage = (text) => {
      return marked(text)
    }

    onMounted(() => {
      scrollToBottom()
    })

    return {
      messages,
      newMessage,
      messagesContainer,
      sendMessage,
      formatTimestamp,
      formatMessage
    }
  }
}
</script>

<style scoped>
.chat-view {
  padding: 2rem;
  min-height: calc(100vh - 64px);
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.chat-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
}

.messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  margin-bottom: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
}

.message.user {
  background-color: #e3f2fd;
  margin-left: 20%;
}

.message.ai {
  background-color: #f5f5f5;
  margin-right: 20%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.sender {
  font-weight: bold;
}

.timestamp {
  color: #666;
}

.message-text {
  white-space: pre-wrap;
}

.input-container {
  padding: 1rem;
  border-top: 1px solid #eee;
  background: white;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.message-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  resize: none;
  font-size: 1rem;
}

.message-input:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1);
}

.send-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}

.send-button:hover:not(:disabled) {
  background-color: #1565c0;
}

.send-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

:deep(.message-text) {
  line-height: 1.5;
}

:deep(.message-text p) {
  margin: 0.5rem 0;
}

:deep(.message-text code) {
  background-color: #f8f9fa;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
}

:deep(.message-text pre) {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}
</style> 