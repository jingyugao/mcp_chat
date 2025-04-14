<template>
	<div class="chat-room">
		<div class="chat-room-header">
			<div class="header-left">
				<h2>{{ room.name }}</h2>
				<div class="participants">
					<span v-for="participant in room.participants" :key="participant" class="participant">
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
				<div class="message-content">{{ message.content }}</div>
			</div>
		</div>

		<div class="chat-input">
			<textarea v-model="newMessage" @keydown.enter.prevent="sendMessage" placeholder="Type your message..." rows="3" :disabled="isSending || !isConnected"></textarea>
			<button @click="sendMessage" :disabled="!newMessage.trim() || isSending || !isConnected" :class="{ 'sending': isSending }">
				<span v-if="isSending">Sending...</span>
				<span v-else>Send</span>
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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'

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

		const connectSSE = () => {
			const token = localStorage.getItem('token')
			if (!token) {
				console.error('No token found')
				return
			}

			eventSource.value = new EventSource(`http://localhost:14000/api/chat-rooms/${route.params.roomId}/events?token=${token}`)

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
				const token = localStorage.getItem('token')
				if (!token) {
					console.error('No token found')
					return
				}

				const response = await fetch(`http://localhost:14000/api/chat-rooms/${route.params.roomId}`, {
					headers: {
						'Authorization': `Bearer ${token}`
					}
				})
				if (response.ok) {
					room.value = await response.json()
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
				const token = localStorage.getItem('token')
				if (!token) {
					console.error('No token found')
					return
				}

				const response = await fetch(`http://localhost:14000/api/chat-rooms/${route.params.roomId}/messages`, {
					headers: {
						'Authorization': `Bearer ${token}`
					}
				})
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

		const sendMessage = async () => {
			if (!newMessage.value.trim() || isSending.value || !isConnected.value) return

			isSending.value = true
			try {
				const token = localStorage.getItem('token')
				if (!token) {
					console.error('No token found')
					return
				}

				const response = await fetch(`http://localhost:14000/api/chat-rooms/${route.params.roomId}/messages`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'Authorization': `Bearer ${token}`
					},
					body: JSON.stringify({
						content: newMessage.value.trim()
					})
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
				const token = localStorage.getItem('token')
				if (!token) {
					throw new Error('No token found')
				}

				const response = await fetch(`http://localhost:14000/api/chat-rooms/${route.params.roomId}/invite`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'Authorization': `Bearer ${token}`
					},
					body: JSON.stringify({
						username: inviteUsername.value.trim()
					})
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
			inviteUser
		}
	}
}
</script>

<style scoped>
.chat-room {
	display: flex;
	flex-direction: column;
	height: 100vh;
	padding: 20px;
	max-width: 800px;
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
	margin-bottom: 20px;
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

.chat-input {
	display: flex;
	gap: 10px;
}

.chat-input textarea {
	flex: 1;
	padding: 10px;
	border: 1px solid #ddd;
	border-radius: 4px;
	resize: none;
	font-family: inherit;
	transition: border-color 0.2s;
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
	padding: 10px 20px;
	background-color: #1976d2;
	color: white;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	transition: all 0.2s;
	min-width: 80px;
}

.chat-input button:hover:not(:disabled) {
	background-color: #1565c0;
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
</style>