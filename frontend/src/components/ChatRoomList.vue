<template>
	<div class="chat-room-list">
		<div class="header">
			<h2>Chat Rooms</h2>
			<button @click="showCreateRoomModal = true" class="create-room-btn">Create Room</button>
		</div>

		<div class="rooms">
			<div v-for="room in rooms" :key="room.id" class="room-card" @click="enterRoom(room)">
				<h3>{{ room.name }}</h3>
				<div class="room-info">
					<span class="participants-count">{{ room.participants.length }} participants</span>
					<span class="created-at">{{ formatDate(room.created_at) }}</span>
				</div>
			</div>
		</div>

		<!-- Create Room Modal -->
		<div v-if="showCreateRoomModal" class="modal-overlay" @click="showCreateRoomModal = false">
			<div class="modal-content" @click.stop>
				<h3>Create New Room</h3>
				<div class="form-group">
					<label for="roomName">Room Name</label>
					<input id="roomName" v-model="newRoomName" type="text" placeholder="Enter room name" @keyup.enter="createRoom" />
				</div>
				<div class="modal-actions">
					<button @click="showCreateRoomModal = false" class="cancel-btn">Cancel</button>
					<button @click="createRoom" :disabled="!newRoomName.trim()" class="create-btn">
						Create
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
	name: 'ChatRoomList',
	setup() {
		const router = useRouter()
		const rooms = ref([])
		const showCreateRoomModal = ref(false)
		const newRoomName = ref('')

		const fetchRooms = async () => {
			try {
				const response = await fetch('http://localhost:14000/api/chat-rooms', {
					headers: {
						'Authorization': `Bearer ${localStorage.getItem('token')}`
					}
				})
				if (response.ok) {
					rooms.value = await response.json()
				}
			} catch (error) {
				console.error('Error fetching rooms:', error)
			}
		}

		const createRoom = async () => {
			if (!newRoomName.value.trim()) return

			try {
				const response = await fetch('http://localhost:14000/api/chat-rooms', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'Authorization': `Bearer ${localStorage.getItem('token')}`
					},
					body: JSON.stringify({
						name: newRoomName.value.trim()
					})
				})

				if (response.ok) {
					const newRoom = await response.json()
					rooms.value.push(newRoom)
					showCreateRoomModal.value = false
					newRoomName.value = ''
					enterRoom(newRoom)
				}
			} catch (error) {
				console.error('Error creating room:', error)
			}
		}

		const enterRoom = (room) => {
			router.push(`/chat/${room.id}`)
		}

		const formatDate = (dateString) => {
			return new Date(dateString).toLocaleDateString()
		}

		onMounted(() => {
			fetchRooms()
		})

		return {
			rooms,
			showCreateRoomModal,
			newRoomName,
			createRoom,
			enterRoom,
			formatDate
		}
	}
}
</script>

<style scoped>
.chat-room-list {
	padding: 20px;
	max-width: 800px;
	margin: 0 auto;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.create-room-btn {
	padding: 8px 16px;
	background-color: #1976d2;
	color: white;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	transition: background-color 0.2s;
}

.create-room-btn:hover {
	background-color: #1565c0;
}

.rooms {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
	gap: 20px;
}

.room-card {
	background: white;
	border-radius: 8px;
	padding: 15px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	cursor: pointer;
	transition: transform 0.2s, box-shadow 0.2s;
}

.room-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.room-card h3 {
	margin: 0 0 10px 0;
	color: #333;
}

.room-info {
	display: flex;
	justify-content: space-between;
	font-size: 0.9em;
	color: #666;
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
}

.modal-content {
	background: white;
	padding: 20px;
	border-radius: 8px;
	width: 400px;
	max-width: 90%;
}

.modal-content h3 {
	margin: 0 0 20px 0;
}

.form-group {
	margin-bottom: 20px;
}

.form-group label {
	display: block;
	margin-bottom: 5px;
	color: #333;
}

.form-group input {
	width: 100%;
	padding: 8px;
	border: 1px solid #ddd;
	border-radius: 4px;
	font-size: 1em;
}

.modal-actions {
	display: flex;
	justify-content: flex-end;
	gap: 10px;
}

.cancel-btn {
	padding: 8px 16px;
	background-color: #f5f5f5;
	color: #333;
	border: none;
	border-radius: 4px;
	cursor: pointer;
}

.create-btn {
	padding: 8px 16px;
	background-color: #1976d2;
	color: white;
	border: none;
	border-radius: 4px;
	cursor: pointer;
}

.create-btn:disabled {
	background-color: #ccc;
	cursor: not-allowed;
}
</style>