const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:14000'

export const API_URLS = {
  auth: {
    register: `${API_BASE_URL}/api/auth/register`,
    login: `${API_BASE_URL}/api/auth/login`,
    logout: `${API_BASE_URL}/api/auth/logout`,
    me: `${API_BASE_URL}/api/auth/me`
  },
  chat: {
    rooms: `${API_BASE_URL}/api/chat_room/room_list`,
    roomInfo: (roomId) => `${API_BASE_URL}/api/chat_room/room_info/${roomId}`,
    messages: (roomId) => `${API_BASE_URL}/api/chat_room/room_messages/${roomId}`,
    events: (roomId) => `${API_BASE_URL}/api/chat_room/room_events/${roomId}`,
    invite: (roomId) => `${API_BASE_URL}/api/chat_room/invite_user/${roomId}`,
    userSearch: `${API_BASE_URL}/api/chat_room/user/search`
  },
  mcp: {
    servers: `${API_BASE_URL}/api/mcp/servers`,
    addServer: `${API_BASE_URL}/api/mcp/add_server`,
    removeServer: `${API_BASE_URL}/api/mcp/remove_server`,
    connectServer: `${API_BASE_URL}/api/mcp/connect_server`,
    disconnectServer: `${API_BASE_URL}/api/mcp/disconnect_server`,
    executeTool: `${API_BASE_URL}/api/mcp/execute_tool`,
    getPrompt: `${API_BASE_URL}/api/mcp/get_prompt`,
    fetchResource: `${API_BASE_URL}/api/mcp/fetch_resource`,
    listToolOfChat: `${API_BASE_URL}/api/mcp/list_tool_of_chat`
  }
}

export default API_URLS
export { API_BASE_URL }
