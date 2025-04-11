<template>
  <div class="server-manager">
    <div class="server-form">
      <h3>Add New Server</h3>
      <form @submit.prevent="addServer">
        <div class="form-group">
          <input 
            v-model="newServer.name" 
            type="text" 
            placeholder="Server Name"
            required
          >
        </div>
        <div class="form-group">
          <input 
            v-model="newServer.url" 
            type="text" 
            placeholder="Server URL (e.g. http://localhost:9002/sse)"
            required
            @input="validateUrl"
          >
          <span class="error-message" v-if="urlError">
            {{ urlError }}
          </span>
        </div>
        <button type="submit" class="btn-add" :disabled="!!urlError">Add Server</button>
      </form>
    </div>

    <div class="server-list">
      <h3>Servers</h3>
      <div 
        v-for="server in servers" 
        :key="server.name" 
        class="server-item"
        :class="{ 
          'selected': selectedServer?.name === server.name,
          'connected': server.status === 'connected',
          'error': server.status === 'error'
        }"
        @click="selectServer(server)"
      >
        <div class="server-info">
          <span class="server-name">{{ server.name }}</span>
          <span class="server-address">{{ server.url }}</span>
          <span class="server-status" :class="server.status">{{ server.status }}</span>
          <span class="server-tools" v-if="server.tools">
            Tools ({{ server.tools.length }}): {{ server.tools.map(t => t.name).slice(0, 3).join(', ') }}
            <div class="tool-list" v-if="server.tools.length > 0">
              <div v-for="tool in server.tools" 
                   :key="tool.name" 
                   class="tool-item"
                   @click.stop="selectTool(server, tool)"
                   :class="{ 'selected': selectedTool?.name === tool.name }">
                <div class="tool-header">
                  <span class="tool-name">{{ tool.name }}</span>
                </div>
                <div class="tool-details">
                  <p class="tool-description">{{ tool.description }}</p>
                  <div class="tool-parameters" v-if="tool.inputSchema?.properties">
                    <h4>Parameters:</h4>
                    <ul>
                      <li v-for="(param, name) in tool.inputSchema.properties" :key="name">
                        {{ name }}: {{ param.title }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </span>
          <span class="server-prompts" v-if="server.prompts">
            Prompts ({{ server.prompts.length }}): {{ server.prompts.map(p => p.name).slice(0, 3).join(', ') }}
            <div class="hover-content" v-if="server.prompts.length > 3">
              {{ server.prompts.map(p => p.name).join(', ') }}
            </div>
          </span>
          <span class="server-resources" v-if="server.resources">
            Resources ({{ server.resources.length }}): {{ server.resources.map(r => r.name).slice(0, 3).join(', ') }}
            <div class="hover-content" v-if="server.resources.length > 3">
              {{ server.resources.map(r => r.name).join(', ') }}
            </div>
          </span>
          <span class="server-resource-templates" v-if="server.resource_templates">
            Resource Templates ({{ server.resource_templates.length }}): {{ server.resource_templates.map(t => t.name).slice(0, 3).join(', ') }}
            <div class="hover-content" v-if="server.resource_templates.length > 3">
              {{ server.resource_templates.map(t => t.name).join(', ') }}
            </div>
          </span>
        </div>
        <div class="server-actions">
          <button 
            @click.stop="toggleConnection(server)"
            :class="{ 'connected': server.status === 'connected' }"
            :disabled="server.status === 'connecting' || server.status === 'disconnecting'"
          >
            {{ getConnectionButtonText(server) }}
          </button>
          <button 
            @click.stop="removeServer(server)"
            class="btn-delete"
            :disabled="server.status === 'connecting' || server.status === 'disconnecting'"
          >
            Remove
          </button>
        </div>
      </div>

      <!-- Tool Parameter Form -->
      <div v-if="selectedTool" class="tool-parameter-form">
        <h3>{{ selectedTool.name }} Parameters</h3>
        <form @submit.prevent="executeTool">
          <div v-for="(param, name) in selectedTool.inputSchema.properties" 
               :key="name" 
               class="param-group">
            <label :for="name">{{ param.title || name }}</label>
            <input 
              :id="name"
              v-model="toolParams[name]"
              :type="getInputType(param)"
              :placeholder="param.description"
              :required="selectedTool.inputSchema.required?.includes(name)"
            >
          </div>
          <button type="submit" class="btn-execute" :disabled="isExecuting">
            {{ isExecuting ? 'Executing...' : 'Execute Tool' }}
          </button>
        </form>

        <!-- Tool Execution Result -->
        <div v-if="toolResult" class="tool-result">
          <h4>Execution Result</h4>
          <div class="result-content">
            <pre>{{ typeof toolResult === 'object' ? JSON.stringify(toolResult, null, 2) : toolResult }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const API_BASE_URL = 'http://localhost:14000/api'

export default {
  name: 'ServerManager',
  data() {
    return {
      servers: [],
      selectedServer: null,
      selectedTool: null,
      toolParams: {},
      toolResult: null,
      isExecuting: false,
      newServer: {
        name: '',
        url: ''
      },
      urlError: ''
    }
  },
  async created() {
    await this.fetchServers()
  },
  methods: {
    validateUrl() {
      try {
        if (!this.newServer.url) {
          this.urlError = ''
          return
        }
        
        const url = new URL(this.newServer.url)
        
        // Check if protocol is http or https
        if (!['http:', 'https:'].includes(url.protocol)) {
          this.urlError = 'URL must use http or https protocol'
          return
        }
        
        this.urlError = ''
      } catch (error) {
        this.urlError = 'Please enter a valid URL'
      }
    },
    async fetchServers() {
      try {
        const response = await fetch(`${API_BASE_URL}/servers`)
        if (!response.ok) throw new Error('Failed to fetch servers')
        this.servers = await response.json()
      } catch (error) {
        console.error('Error fetching servers:', error)
      }
    },
    async addServer() {
      if (this.urlError) {
        return
      }

      try {
  
        const response = await fetch(`${API_BASE_URL}/add_server`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            url: this.newServer.url,
            name: this.newServer.name
          })
        })
        if (!response.ok) {
          throw new Error('Failed to add server')
        }

        // Reset form
        this.newServer.name = ''
        this.newServer.url = ''
        this.urlError = ''

        // Refresh server list
        await this.fetchServers()
      } catch (error) {
        console.error('Error adding server:', error)
      }
    },
    async removeServer(server) {
      try {
        const response = await fetch(`${API_BASE_URL}/remove_server?name=${encodeURIComponent(server.name)}`, {
          method: 'DELETE'
        })

        if (!response.ok) {
          throw new Error('Failed to remove server')
        }

        if (this.selectedServer?.name === server.name) {
          this.selectedServer = null
        }

        // Refresh server list
        await this.fetchServers()
      } catch (error) {
        console.error('Error removing server:', error)
      }
    },
    selectServer(server) {
      this.selectedServer = server
      this.$emit('server-selected', server)
    },
    async toggleConnection(server) {
      try {
        // Set temporary connecting status
        const isDisconnecting = server.status === 'connected'
        server.status = isDisconnecting ? 'disconnecting' : 'connecting'

        if (isDisconnecting) {
          const response = await fetch(`${API_BASE_URL}/disconnect_server?name=${server.name}`, {
            method: 'POST'
          })

          if (!response.ok) {
            throw new Error('Failed to disconnect from server')
          }

          const result = await response.json()
          if (result.status === 'success') {
            // Refresh the server list to get updated information
            await this.fetchServers()
            
            // Find and select the updated server from the refreshed list
            const updatedServer = this.servers.find(s => s.name === server.name)
            if (updatedServer) {
              this.selectServer(updatedServer)
            }
          } else {
            throw new Error(result.message || 'Failed to disconnect from server')
          }
        } else {
          const response = await fetch(`${API_BASE_URL}/connect_server?name=${server.name}`, {
            method: 'POST'
          })

          if (!response.ok) {
            throw new Error('Failed to connect to server')
          }

          const result = await response.json()
          if (result.status === 'success') {
            // Refresh the server list to get updated information
            await this.fetchServers()
            
            // Find and select the updated server from the refreshed list
            const updatedServer = this.servers.find(s => s.name === server.name)
            if (updatedServer) {
              this.selectServer(updatedServer)
            }
          } else {
            throw new Error(result.message || 'Failed to connect to server')
          }
        }
      } catch (error) {
        console.error('Connection error:', error)
        server.status = 'error'
      }
    },
    getConnectionButtonText(server) {
      switch (server.status) {
        case 'connected':
          return 'Disconnect'
        case 'connecting':
          return 'Connecting...'
        case 'disconnecting':
          return 'Disconnecting...'
        case 'error':
          return 'Retry Connection'
        default:
          return 'Connect'
      }
    },
    selectTool(server, tool) {
      this.selectedTool = tool;
      this.toolParams = {};  // Reset parameters
    },
    getInputType(param) {
      // Determine input type based on parameter type
      switch (param.type) {
        case 'number':
        case 'integer':
          return 'number';
        case 'boolean':
          return 'checkbox';
        default:
          return 'text';
      }
    },
    async executeTool() {
      try {
        this.isExecuting = true;
        this.toolResult = null;
        
        const response = await fetch(`${API_BASE_URL}/execute_tool`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            server: this.selectedServer.name,
            tool: this.selectedTool.name,
            parameters: this.toolParams
          })
        });

        if (!response.ok) {
          throw new Error('Failed to execute tool');
        }

        const result = await response.json();
        this.toolResult = result;
      } catch (error) {
        console.error('Error executing tool:', error);
        this.toolResult = { error: error.message };
      } finally {
        this.isExecuting = false;
      }
    }
  }
}
</script>

<style scoped>
.server-manager {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.server-form {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

input.error {
  border-color: #f44336;
}

.error-message {
  color: #f44336;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.server-list {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.server-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.server-item:hover {
  background-color: #f9f9f9;
}

.server-item.selected {
  background-color: #e3f2fd;
}

.server-info {
  display: flex;
  flex-direction: column;
}

.server-name {
  font-weight: bold;
  margin-bottom: 4px;
}

.server-address {
  color: #666;
  font-size: 14px;
}

.server-actions {
  display: flex;
  gap: 10px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-add {
  background-color: #4caf50;
  color: white;
  width: 100%;
  margin-top: 10px;
}

.btn-add:hover:not(:disabled) {
  background-color: #45a049;
}

button.connected {
  background-color: #f44336;
  color: white;
}

button:not(.connected):not(.btn-delete) {
  background-color: #2196f3;
  color: white;
}

.btn-delete {
  background-color: #ff5722;
  color: white;
}

button:hover:not(:disabled) {
  opacity: 0.9;
}

.server-status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 3px;
  margin-top: 4px;
  display: inline-block;
}

.server-status.connected {
  background-color: #4caf50;
  color: white;
}

.server-status.disconnected {
  background-color: #9e9e9e;
  color: white;
}

.server-status.error {
  background-color: #f44336;
  color: white;
}

.server-status.connecting {
  background-color: #2196f3;
  color: white;
}

.server-tools,
.server-prompts,
.server-resources,
.server-resource-templates {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  display: block;
  position: relative;
}

.hover-content {
  display: none;
  position: absolute;
  left: 0;
  top: 100%;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px;
  margin-top: 4px;
  min-width: 200px;
  max-width: 400px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
  white-space: normal;
  word-wrap: break-word;
}

.server-tools:hover .hover-content,
.server-prompts:hover .hover-content,
.server-resources:hover .hover-content,
.server-resource-templates:hover .hover-content {
  display: block;
}

.server-item.connected {
  border-left: 4px solid #4caf50;
}

.server-item.error {
  border-left: 4px solid #f44336;
}

.tool-list {
  position: absolute;
  left: 0;
  top: 100%;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 1000;
  min-width: 300px;
  max-width: 500px;
  display: none;
}

.server-tools:hover .tool-list {
  display: block;
}

.tool-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.tool-item:last-child {
  border-bottom: none;
}

.tool-item:hover {
  background-color: #f5f5f5;
}

.tool-item.selected {
  background-color: #e3f2fd;
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tool-name {
  font-weight: bold;
  color: #2196f3;
}

.tool-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.tool-parameters {
  font-size: 12px;
}

.tool-parameters h4 {
  margin: 8px 0;
  color: #333;
}

.tool-parameters ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tool-parameters li {
  margin: 4px 0;
  color: #666;
}

.tool-parameter-form {
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.param-group {
  margin-bottom: 15px;
}

.param-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.param-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.btn-execute {
  background-color: #2196f3;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  width: 100%;
}

.btn-execute:hover {
  background-color: #1976d2;
}

.tool-result {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
}

.tool-result h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.result-content {
  max-height: 300px;
  overflow-y: auto;
  background: #fff;
  padding: 10px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.result-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 14px;
  color: #333;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style> 