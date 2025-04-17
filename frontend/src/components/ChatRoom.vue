<template>
	<div class="chat-room">
		<div class="chat-room-header">
			<div class="header-left">
				<h2>{{ room.name }}</h2>
				<div class="participants">
					<span v-for="participant in room.participant_names" :key="participant" class="participant">
						{{ participant }}
					</span>
				</div>
			</div>
			<div class="header-right">
				<div class="connection-status" :class="{ 'connected': isConnected, 'disconnected': !isConnected }">
					{{ isConnected ? 'Connected' : 'Disconnected' }}
				</div>
				<button class="invite-button" @click="showInviteModal = true" :disabled="!isConnected">
					Invite User
				</button>
			</div>
		</div>

		<div class="chat-messages" ref="messagesContainer">
			<div v-if="isLoading" class="loading-messages">
				Loading messages...
			</div>
			<div v-else-if="messages.length === 0" class="no-messages">
				No messages yet. Start the conversation!
			</div>
			<div v-else v-for="message in messages" :key="message.id" class="message" :class="message.type">
				<div class="message-header">
					<span class="sender">{{ message.sender_username }}</span>
					<span class="timestamp">{{ formatTimestamp(message.created_at) }}</span>
				</div>
				<div class="message-content" v-html="formatMessageContent(message)"></div>
			</div>
		</div>

		<div class="chat-input">
			<div class="input-wrapper">
				<textarea 
					v-model="newMessage" 
					@keydown.enter="handleEnterKey"
					@input="handleInput"
					@keydown="handleKeyDown"
					placeholder="Type your message..." 
					rows="3" 
					:disabled="isSending || !isConnected"
				></textarea>
				<!-- Mention suggestions -->
				<div v-if="showMentionSuggestions" class="mention-suggestions">
					<div 
						v-for="user in filteredParticipants" 
						:key="user.id"
						class="mention-item"
						:class="{ 'selected': selectedMentionIndex === filteredParticipants.indexOf(user) }"
						@click="selectMention(user)"
					>
						{{ user.username }}
					</div>
				</div>
			</div>
			<button @click="sendMessage" :disabled="!newMessage.trim() || isSending || !isConnected" :class="{ 'sending': isSending }">
				<span v-if="isSending">...</span>
				<span v-else>↑</span>
			</button>
		</div>

		<!-- Invite Modal -->
		<div v-if="showInviteModal" class="modal-overlay" @click="showInviteModal = false">
			<div class="modal-content" @click.stop>
				<h3>Invite User</h3>
				<div class="invite-form">
					<input v-model="inviteUsername" type="text" placeholder="Enter username" :disabled="isInviting">
					<div class="modal-buttons">
						<button @click="inviteUser" :disabled="!inviteUsername.trim() || isInviting" :class="{ 'sending': isInviting }">
							<span v-if="isInviting">Inviting...</span>
							<span v-else>Invite</span>
						</button>
						<button @click="showInviteModal = false" :disabled="isInviting">Cancel</button>
					</div>
				</div>
				<div v-if="inviteError" class="error-message">
					{{ inviteError }}
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { httpClient } from '../utils/http-client'
import { API_URLS } from '../api/config'

export default {
	name: 'ChatRoom',
	setup() {
		const route = useRoute()
		const room = ref({})
		const messages = ref([])
		const newMessage = ref('')
		const messagesContainer = ref(null)
		const eventSource = ref(null)
		const isConnected = ref(false)
		const isSending = ref(false)
		const isLoading = ref(false)
		const reconnectAttempts = ref(0)
		const maxReconnectAttempts = 5
		const reconnectTimeout = 3000 // 3 seconds

		// Invite related state
		const showInviteModal = ref(false)
		const inviteUsername = ref('')
		const isInviting = ref(false)
		const inviteError = ref('')

		// Mention related state
		const mentionSearch = ref('')
		const showMentionSuggestions = ref(false)
		const selectedMentionIndex = ref(0)
		const mentionStartIndex = ref(-1)

		const filteredParticipants = computed(() => {
			const participants = []
			if (!room.value.participant_users) return participants
			
			for (const [id, username] of Object.entries(room.value.participant_users)) {
				if (!mentionSearch.value || username.toLowerCase().includes(mentionSearch.value.toLowerCase())) {
					participants.push({ id, username })
				}
			}
			return participants
		})

		const connectSSE = () => {
			const token = localStorage.getItem('access_token')
			if (!token) {
				console.error('No authentication token found')
				return
			}

			eventSource.value = new EventSource(
				`${API_URLS.chat.events(route.params.roomId)}?token=${token}`,
			)

			eventSource.value.onopen = () => {
				isConnected.value = true
				reconnectAttempts.value = 0
			}

			eventSource.value.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data)
					if (data.type === 'message') {
						messages.value.push(data.data)
					} else if (data.type === 'system') {
						messages.value.push({
							type: 'system',
							content: data.data,
							created_at: new Date().toISOString()
						})
					}
					scrollToBottom()
				} catch (error) {
					console.error('Error parsing message:', error)
				}
			}

			eventSource.value.onerror = (error) => {
				console.error('SSE error:', error)
				isConnected.value = false
				eventSource.value.close()

				if (reconnectAttempts.value < maxReconnectAttempts) {
					reconnectAttempts.value++
					setTimeout(connectSSE, reconnectTimeout)
				}
			}
		}

		const fetchRoomInfo = async () => {
			try {
				const response = await httpClient.get(API_URLS.chat.roomInfo(route.params.roomId))
				if (response.ok) {
					const roomData = await response.json()
					room.value = {
						...roomData,
						participant_names: Object.values(roomData.participant_users || {})
					}
				} else {
					console.error('Failed to fetch room info')
				}
			} catch (error) {
				console.error('Error fetching room info:', error)
			}
		}

		const fetchMessages = async () => {
			isLoading.value = true
			try {
				const response = await httpClient.get(API_URLS.chat.messages(route.params.roomId))
				if (response.ok) {
					messages.value = await response.json()
					scrollToBottom()
				} else {
					console.error('Failed to fetch messages')
				}
			} catch (error) {
				console.error('Error fetching messages:', error)
			} finally {
				isLoading.value = false
			}
		}

		const handleInput = (event) => {
			const text = event.target.value
			const lastAtIndex = text.lastIndexOf('@')
			
			if (lastAtIndex !== -1) {
				const afterAt = text.slice(lastAtIndex + 1)
				const spaceAfterAt = afterAt.indexOf(' ')
				
				if (spaceAfterAt === -1) {
					mentionSearch.value = afterAt
					showMentionSuggestions.value = true
					mentionStartIndex.value = lastAtIndex
					selectedMentionIndex.value = 0
					return
				}
			}
			
			showMentionSuggestions.value = false
			mentionStartIndex.value = -1
		}

		const handleKeyDown = (event) => {
			if (!showMentionSuggestions.value) return

			if (event.key === 'ArrowDown') {
				event.preventDefault()
				selectedMentionIndex.value = (selectedMentionIndex.value + 1) % filteredParticipants.value.length
			} else if (event.key === 'ArrowUp') {
				event.preventDefault()
				selectedMentionIndex.value = (selectedMentionIndex.value - 1 + filteredParticipants.value.length) % filteredParticipants.value.length
			} else if (event.key === 'Enter' && showMentionSuggestions.value) {
				event.preventDefault()
				const selectedUser = filteredParticipants.value[selectedMentionIndex.value]
				if (selectedUser) {
					selectMention(selectedUser)
				}
			} else if (event.key === 'Escape') {
				showMentionSuggestions.value = false
			}
		}

		const selectMention = (user) => {
			const beforeMention = newMessage.value.slice(0, mentionStartIndex.value)
			const afterMention = newMessage.value.slice(mentionStartIndex.value + mentionSearch.value.length + 1)
			newMessage.value = `${beforeMention}@${user.username} ${afterMention}`
			showMentionSuggestions.value = false
			mentionStartIndex.value = -1
		}

		const extractMentions = (text) => {
			const mentions = []
			const regex = /@(\w+)/g
			let match
			
			while ((match = regex.exec(text)) !== null) {
				const username = match[1]
				const entry = Object.entries(room.value.participant_users || {})
					.find(([, name]) => name === username)
				
				if (entry) {
					const [userId] = entry
					mentions.push({
						user_id: userId,
						username: username,
						index: match.index
					})
				}
			}
			
			return mentions
		}

		const handleEnterKey = (event) => {
			if (showMentionSuggestions.value) {
				event.preventDefault()
				const selectedUser = filteredParticipants.value[selectedMentionIndex.value]
				if (selectedUser) {
					selectMention(selectedUser)
				}
			} else if (event.shiftKey) {
				// 如果按住Shift+Enter，插入换行符
				return
			} else {
				// 如果没有显示@用户建议，则发送消息
				event.preventDefault()
				sendMessage()
			}
		}

		const sendMessage = async () => {
			if (!newMessage.value.trim() || isSending.value || !isConnected.value) return

			const mentions = extractMentions(newMessage.value)
			isSending.value = true
			
			try {
				const response = await httpClient.post(API_URLS.chat.messages(route.params.roomId), {
					content: newMessage.value.trim(),
					mentions: mentions
				})

				if (response.ok) {
					newMessage.value = ''
				} else {
					console.error('Failed to send message')
				}
			} catch (error) {
				console.error('Error sending message:', error)
			} finally {
				isSending.value = false
			}
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

		const inviteUser = async () => {
			if (!inviteUsername.value.trim() || isInviting.value) return

			isInviting.value = true
			inviteError.value = ''

			try {
				const response = await httpClient.post(API_URLS.chat.invite(route.params.roomId), {
					username: inviteUsername.value.trim()
				})

				if (response.ok) {
					showInviteModal.value = false
					inviteUsername.value = ''
					// Refresh room info to show new participant
					await fetchRoomInfo()
				} else {
					const error = await response.json()
					throw new Error(error.detail || 'Failed to invite user')
				}
			} catch (error) {
				inviteError.value = error.message
			} finally {
				isInviting.value = false
			}
		}

		const formatMessageContent = (message) => {
			if (!message.mentions || message.mentions.length === 0) {
				return escapeHtml(message.content)
			}

			let content = message.content
			// Sort mentions by index in descending order to replace from end to start
			const sortedMentions = [...message.mentions].sort((a, b) => b.index - a.index)
			
			for (const mention of sortedMentions) {
				const mentionText = `@${mention.username}`
				content = content.slice(0, mention.index) + `<span class="mention" data-user-id="${mention.user_id}">${mentionText}</span>` + content.slice(mention.index + mentionText.length)
			}
			
			return content
		}

		const escapeHtml = (text) => {
			const div = document.createElement('div')
			div.textContent = text
			return div.innerHTML
		}

		onMounted(() => {
			fetchRoomInfo()
			fetchMessages()
			connectSSE()
		})

		onUnmounted(() => {
			if (eventSource.value) {
				eventSource.value.close()
			}
		})

		return {
			room,
			messages,
			newMessage,
			messagesContainer,
			sendMessage,
			formatTimestamp,
			isConnected,
			isSending,
			isLoading,
			// Invite related
			showInviteModal,
			inviteUsername,
			isInviting,
			inviteError,
			inviteUser,
			handleInput,
			handleKeyDown,
			handleEnterKey,
			showMentionSuggestions,
			filteredParticipants,
			selectedMentionIndex,
			selectMention,
			formatMessageContent
		}
	}
}
</script>

<style scoped>
.chat-room {
	display: flex;
	flex-direction: column;
	height: 80vh;
	padding: 20px;
	max-width: 1200px;
	margin: 0 auto;
}

.chat-room-header {
	margin-bottom: 20px;
	padding-bottom: 10px;
	border-bottom: 1px solid #eee;
	position: relative;
}

.chat-room-header h2 {
	margin: 0 0 10px 0;
}

.participants {
	display: flex;
	gap: 10px;
	flex-wrap: wrap;
	margin-bottom: 10px;
}

.participant {
	background-color: #e3f2fd;
	padding: 4px 8px;
	border-radius: 12px;
	font-size: 0.9em;
}

.connection-status {
	position: absolute;
	top: 10px;
	right: 10px;
	padding: 4px 8px;
	border-radius: 12px;
	font-size: 0.8em;
}

.connection-status.connected {
	background-color: #4caf50;
	color: white;
}

.connection-status.disconnected {
	background-color: #f44336;
	color: white;
}

.chat-messages {
	flex: 1;
	overflow-y: auto;
	padding: 20px;
	background-color: #f9f9f9;
	border-radius: 8px;
	margin-bottom: 15px;
	position: relative;
}

.loading-messages,
.no-messages {
	text-align: center;
	color: #666;
	padding: 20px;
}

.message {
	margin-bottom: 15px;
	max-width: 80%;
	opacity: 0;
	transform: translateY(20px);
	animation: messageAppear 0.3s ease forwards;
}

@keyframes messageAppear {
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.message.user {
	margin-left: auto;
}

.message.system {
	text-align: center;
	color: #666;
	font-style: italic;
}

.message-header {
	display: flex;
	justify-content: space-between;
	margin-bottom: 5px;
	font-size: 0.9em;
}

.sender {
	font-weight: bold;
}

.timestamp {
	color: #666;
}

.message-content {
	padding: 10px 15px;
	border-radius: 8px;
	background-color: #fff;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
	background-color: #e3f2fd;
}

/* 聊天输入框容器样式 */
.chat-input {
	position: relative;     /* 相对定位,作为子元素的定位参考 */
	display: flex;         /* 弹性布局 */
	gap: 10px;            /* 子元素之间的间距为10px */
	width: 100%;          /* 宽度占满父容器 */
	max-width: 1100px;    /* 最大宽度限制在1100px */
	margin: 0 auto;       /* 水平居中 */
}

/* 文本输入框样式 */
.chat-input textarea {
	width: 100%;          /* 宽度占满父容器 */
	min-width: 0;         /* 最小宽度为0,防止溢出 */
	padding: 10px;        /* 内边距10px */
	padding-right: 60px;  /* 右侧内边距60px,为发送按钮预留空间 */
	border: 1px solid #ddd; /* 灰色边框 */
	border-radius: 4px;    /* 圆角边框 */
	resize: none;          /* 禁止手动调整大小 */
	font-family: inherit;  /* 继承父元素字体 */
	transition: border-color 0.2s; /* 边框颜色变化动画 */
}

.chat-input textarea:focus {
	outline: none;
	border-color: #1976d2;
}

.chat-input textarea:disabled {
	background-color: #f5f5f5;
	cursor: not-allowed;
}

.chat-input button {
	position: absolute;
	right: 10px;
	bottom: 10px;
	width: 40px;
	height: 40px;
	padding: 0;
	border: none;
	border-radius: 50%;
	background-color: #1976d2;
	color: white;
	cursor: pointer;
	transition: all 0.2s;
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1;
}

.chat-input button:hover:not(:disabled) {
	background-color: #1565c0;
	transform: scale(1.05);
}

.chat-input button:disabled {
	background-color: #ccc;
	cursor: not-allowed;
}

.chat-input button.sending {
	background-color: #1976d2;
	opacity: 0.7;
}

.header-left {
	flex: 1;
}

.header-right {
	display: flex;
	align-items: center;
	gap: 10px;
}

.invite-button {
	padding: 6px 12px;
	background-color: #4caf50;
	color: white;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	transition: all 0.2s;
}

.invite-button:hover:not(:disabled) {
	background-color: #388e3c;
}

.invite-button:disabled {
	background-color: #ccc;
	cursor: not-allowed;
}

.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 1000;
}

.modal-content {
	background-color: white;
	padding: 20px;
	border-radius: 8px;
	width: 90%;
	max-width: 400px;
}

.modal-content h3 {
	margin-top: 0;
	margin-bottom: 20px;
}

.invite-form {
	display: flex;
	flex-direction: column;
	gap: 15px;
}

.invite-form input {
	padding: 8px 12px;
	border: 1px solid #ddd;
	border-radius: 4px;
	font-size: 1em;
}

.invite-form input:focus {
	outline: none;
	border-color: #1976d2;
}

.modal-buttons {
	display: flex;
	gap: 10px;
	justify-content: flex-end;
}

.modal-buttons button {
	padding: 8px 16px;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	transition: all 0.2s;
}

.modal-buttons button:first-child {
	background-color: #4caf50;
	color: white;
}

.modal-buttons button:first-child:hover:not(:disabled) {
	background-color: #388e3c;
}

.modal-buttons button:last-child {
	background-color: #f5f5f5;
}

.modal-buttons button:last-child:hover:not(:disabled) {
	background-color: #e0e0e0;
}

.modal-buttons button:disabled {
	opacity: 0.7;
	cursor: not-allowed;
}

.error-message {
	color: #f44336;
	margin-top: 10px;
	font-size: 0.9em;
}

.input-wrapper {
	position: relative;
	flex: 1;
	min-width: 0;
}

.mention-suggestions {
	position: absolute;
	bottom: 100%;
	left: 0;
	width: 100%;
	max-height: 200px;
	overflow-y: auto;
	background: white;
	border: 1px solid #ddd;
	border-radius: 4px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	z-index: 1000;
}

.mention-item {
	padding: 8px 12px;
	cursor: pointer;
	transition: background-color 0.2s;
}

.mention-item:hover,
.mention-item.selected {
	background-color: #e3f2fd;
}

.message-content .mention {
	color: #1976d2;
	font-weight: 500;
}
</style>