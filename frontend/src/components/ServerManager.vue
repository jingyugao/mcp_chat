<template>
  <div class="server-manager">
    <div class="main-container">
      <div class="left-tabs">
        <div class="tab-item" :class="{ active: activeTab === 'server' }" @click="activeTab = 'server'">
          Server Manage
        </div>
        <div class="tab-item" :class="{ active: activeTab === 'tool' }" @click="activeTab = 'tool'">
          Tool
        </div>
      </div>

      <div class="content-area">
        <!-- Server Manage Content -->
        <div v-if="activeTab === 'server'" class="tab-content">
          <div class="server-form">
            <h3>Add New Server</h3>
            <form @submit.prevent="addServer">
              <div class="form-group">
                <input v-model="newServer.name" type="text" placeholder="Server Name" required>
              </div>
              <div class="form-group">
                <input v-model="newServer.url" type="text" placeholder="Server URL (e.g. http://localhost:9002/sse)" required @input="validateUrl">
                <span class="error-message" v-if="urlError">
                  {{ urlError }}
                </span>
              </div>
              <button type="submit" class="btn-add" :disabled="!!urlError">Add Server</button>
            </form>
          </div>

          <div class="server-list">
            <div class="server-list-header">
              <h3>Servers</h3>
              <button @click="fetchServers" class="btn-refresh" :disabled="isExecuting" title="Refresh servers">
                <span class="refresh-icon">↻</span>
              </button>
            </div>
            <div v-for="server in servers" :key="server.name" class="server-item" :class="{
              'selected': selectedServer?.name === server.name,
              'connected': server.status === 'connected',
              'error': server.status === 'error'
            }" @click="selectServer(server)">
              <div class="server-info">
                <span class="server-name">{{ server.name }}</span>
                <span class="server-address">{{ server.url }}</span>
                <span class="server-status" :class="server.status">{{ server.status }}</span>
                <span class="server-tools" v-if="server.tools">
                  Tools ({{ server.tools.length }}): {{server.tools.map(t => t.name).slice(0, 3).join(', ')}}
                  <div class="tool-list" v-if="server.tools.length > 0">
                    <div v-for="tool in server.tools" :key="tool.name" class="tool-item" @click.stop="selectTool(server, tool)" :class="{ 'selected': selectedTool?.name === tool.name }">
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
                  Prompts ({{ server.prompts.length }}): {{server.prompts.map(p => p.name).slice(0, 3).join(', ')}}
                  <div class="prompt-list" v-if="server.prompts.length > 0">
                    <div v-for="prompt in server.prompts" :key="prompt.name" class="item-details" @click.stop="selectPrompt(server, prompt)" :class="{ 'selected': selectedPrompt?.name === prompt.name }">
                      <div class="item-header">
                        <span class="item-name">{{ prompt.name }}</span>
                      </div>
                      <div class="item-content">
                        <p class="item-description">{{ prompt.description }}</p>
                        <div class="item-parameters" v-if="prompt.parameters">
                          <h4>Parameters:</h4>
                          <ul>
                            <li v-for="param in prompt.parameters" :key="param.name">
                              {{ param.name }}: {{ param.description }}
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </span>
                <span class="server-resources" v-if="server.resources">
                  Resources ({{ server.resources.length }}): {{server.resources.map(r => r.name).slice(0, 3).join(', ')}}
                  <div class="resource-list" v-if="server.resources.length > 0">
                    <div v-for="resource in server.resources" :key="resource.name" class="item-details" @click.stop="selectResource(server, resource)" :class="{ 'selected': selectedResource?.name === resource.name }">
                      <div class="item-header">
                        <span class="item-name">{{ resource.name }}</span>
                      </div>
                      <div class="item-content">
                        <p class="item-description">{{ resource.description }}</p>
                        <div class="item-type" v-if="resource.type">
                          <h4>Type:</h4>
                          <p>{{ resource.type }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </span>
                <span class="server-resource-templates" v-if="server.resource_templates">
                  Resource Templates ({{ server.resource_templates.length }}): {{server.resource_templates.map(t => t.name).slice(0, 3).join(', ')}}
                  <div class="template-list" v-if="server.resource_templates.length > 0">
                    <div v-for="template in server.resource_templates" :key="template.name" class="item-details" @click.stop="selectResourceTemplate(server, template)" :class="{ 'selected': selectedResourceTemplate?.name === template.name }">
                      <div class="item-header">
                        <span class="item-name">{{ template.name }}</span>
                      </div>
                      <div class="item-content">
                        <p class="item-description">{{ template.description }}</p>
                        <div class="item-schema" v-if="template.schema">
                          <h4>Schema:</h4>
                          <pre>{{ JSON.stringify(template.schema, null, 2) }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </span>
              </div>
              <div class="server-actions">
                <button @click.stop="toggleConnection(server)" :class="{ 'connected': server.status === 'connected' }" :disabled="server.status === 'connecting' || server.status === 'disconnecting'">
                  {{ getConnectionButtonText(server) }}
                </button>
                <button @click.stop="removeServer(server)" class="btn-delete" :disabled="server.status === 'connecting' || server.status === 'disconnecting'">
                  Remove
                </button>
              </div>
            </div>
          </div>

          <!-- Tool Parameter Form -->
          <div v-if="selectedTool" class="tool-parameter-form">
            <h3>{{ selectedTool.name }} Parameters</h3>
            <form @submit.prevent="executeTool">
              <div v-for="(param, name) in selectedTool.inputSchema.properties" :key="name" class="param-group">
                <label :for="name">{{ param.title || name }}</label>
                <input :id="name" v-model="toolParams[name]" :type="getInputType(param)" :placeholder="param.description" :required="selectedTool.inputSchema.required?.includes(name)">
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

          <!-- Prompt Parameter Form -->
          <div v-if="selectedPrompt" class="tool-parameter-form">
            <h3>{{ selectedPrompt.name }} Parameters</h3>
            <form @submit.prevent="getPrompt">
              <div v-for="arg in selectedPrompt.arguments" :key="arg.name" class="param-group">
                <label :for="arg.name">{{ arg.name }}</label>
                <input :id="arg.name" v-model="promptParams[arg.name]" type="text" :placeholder="arg.description || `Enter ${arg.name}`" :required="arg.required">
              </div>
              <button type="submit" class="btn-execute" :disabled="isExecuting">
                {{ isExecuting ? 'Executing...' : 'Get Prompt' }}
              </button>
            </form>

            <!-- Prompt Execution Result -->
            <div v-if="promptResult" class="tool-result">
              <h4>Execution Result</h4>
              <div class="result-content">
                <pre>{{ typeof promptResult === 'object' ? JSON.stringify(promptResult, null, 2) : promptResult }}</pre>
              </div>
            </div>
          </div>

          <!-- Resource Parameter Form -->
          <div v-if="selectedResource" class="tool-parameter-form">
            <h3>{{ selectedResource.name }} Parameters</h3>
            <form @submit.prevent="fetchResource">
              <div v-for="(param, name) in selectedResource.parameters" :key="name" class="param-group">
                <label :for="name">{{ name }}</label>
                <input :id="name" v-model="resourceParams[name]" type="text" :placeholder="param.description" :required="param.required">
              </div>
              <button type="submit" class="btn-execute" :disabled="isExecuting">
                {{ isExecuting ? 'Fetching...' : 'Fetch Resource' }}
              </button>
            </form>

            <!-- Resource Execution Result -->
            <div v-if="resourceResult" class="tool-result">
              <h4>Resource Content</h4>
              <div class="result-content">
                <pre>{{ typeof resourceResult === 'object' ? JSON.stringify(resourceResult, null, 2) : resourceResult }}</pre>
              </div>
            </div>
          </div>

          <!-- Resource Template Parameter Form -->
          <div v-if="selectedResourceTemplate" class="tool-parameter-form">
            <h3>{{ selectedResourceTemplate.name }} Parameters</h3>
            <div class="template-url">
              <h4>Template URL:</h4>
              <pre>{{ selectedResourceTemplate.uriTemplate }}</pre>
            </div>
            <form @submit.prevent="fetchResourceFromTemplate">
              <div v-for="param in urlParameters" :key="param.name" class="param-group">
                <label :for="param.name">{{ param.name }}</label>
                <input :id="param.name" v-model="resourceTemplateParams[param.name]" type="text" :placeholder="param.description" :required="param.required">
              </div>
              <button type="submit" class="btn-execute" :disabled="isExecuting">
                {{ isExecuting ? 'Fetching...' : 'Fetch Resource' }}
              </button>
            </form>

            <!-- Resource Template Execution Result -->
            <div v-if="resourceTemplateResult" class="tool-result">
              <h4>Execution Result</h4>
              <div class="result-content">
                <pre>{{ typeof resourceTemplateResult === 'object' ? JSON.stringify(resourceTemplateResult, null, 2) : resourceTemplateResult }}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- Tool Content -->
        <div v-if="activeTab === 'tool'" class="tab-content">
          <div class="tool-tools-section">
            <div class="tools-container">
              <div class="tools-input-wrapper">
                <textarea v-model="toolInput" placeholder="Enter tool content to list tools" class="tools-input" rows="4"></textarea>
                <div class="tools-button-wrapper">
                  <button @click="listToolsOfTool" class="btn-list-tools" :disabled="isExecuting">
                    {{ isExecuting ? 'Loading...' : 'List Tools' }}
                  </button>
                </div>
              </div>
              <div v-if="listToolsResult" class="tools-result">
                <h4>Tools Found:</h4>
                <div class="result-content">
                  <pre>{{ JSON.stringify(listToolsResult, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>

          <div class="tool-container">
            <div class="tool-messages">
              <div v-for="(message, index) in toolMessages" :key="index" :class="['message', message.type]">
                <div class="message-content">{{ message.content }}</div>
              </div>
            </div>
            <div class="tool-input">
              <textarea v-model="newMessage" placeholder="Type your message..." @keyup.enter="sendMessage"></textarea>
              <button @click="sendMessage" class="btn-send">Send</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { httpClient } from '../utils/http-client'
import { API_BASE_URL } from '../api/config'

export default {
  name: 'ServerManager',
  data() {
    return {
      servers: [],
      selectedServer: null,
      selectedTool: null,
      selectedPrompt: null,
      selectedResource: null,
      selectedResourceTemplate: null,
      toolParams: {},
      promptParams: {},
      resourceParams: {},
      resourceTemplateParams: {},
      toolResult: null,
      promptResult: null,
      resourceResult: null,
      resourceTemplateResult: null,
      isExecuting: false,
      newServer: {
        name: '',
        url: ''
      },
      urlError: '',
      urlParameters: [],
      activeTab: 'server',
      toolMessages: [],
      newMessage: '',
      toolInput: '',
      listToolsResult: null
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
        const response = await httpClient.get(`${API_BASE_URL}/servers`)
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
        const response = await httpClient.post(`${API_BASE_URL}/add_server`, {
          url: this.newServer.url,
          name: this.newServer.name
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
        const response = await httpClient.delete(`${API_BASE_URL}/remove_server?name=${encodeURIComponent(server.name)}`)

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
          const response = await httpClient.post(`${API_BASE_URL}/disconnect_server?name=${server.name}`)

          if (!response.ok) {
            throw new Error('Failed to disconnect from server')
          }

          const result = await response.json()
          if (result.status === 'success') {
            await this.fetchServers()
            const updatedServer = this.servers.find(s => s.name === server.name)
            if (updatedServer) {
              this.selectServer(updatedServer)
            }
          } else {
            throw new Error(result.message || 'Failed to disconnect from server')
          }
        } else {
          const response = await httpClient.post(`${API_BASE_URL}/connect_server?name=${server.name}`)

          if (!response.ok) {
            throw new Error('Failed to connect to server')
          }

          const result = await response.json()
          if (result.status === 'success') {
            await this.fetchServers()
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
      this.selectedPrompt = null;
      this.selectedResource = null;
      this.selectedResourceTemplate = null;
      this.toolParams = {};  // Reset parameters
    },
    selectPrompt(server, prompt) {
      this.selectedPrompt = prompt;
      this.selectedTool = null;
      this.selectedResource = null;
      this.selectedResourceTemplate = null;
      // Initialize parameters based on prompt arguments
      this.promptParams = {};
      if (prompt.arguments) {
        prompt.arguments.forEach(arg => {
          this.promptParams[arg.name] = '';
        });
      }
    },
    selectResource(server, resource) {
      this.selectedResource = resource;
      this.selectedTool = null;
      this.selectedPrompt = null;
      this.selectedResourceTemplate = null;
      this.resourceParams = {};  // Reset parameters
    },
    selectResourceTemplate(server, template) {
      this.selectedResourceTemplate = template;
      this.selectedTool = null;
      this.selectedPrompt = null;
      this.selectedResource = null;
      this.resourceTemplateParams = {};  // Reset parameters

      // Parse URL parameters from template URL
      if (template.uriTemplate) {
        // Find all parameters wrapped in {}
        const regex = /\{([^}]+)\}/g;
        let match;
        const params = [];

        while ((match = regex.exec(template.uriTemplate)) !== null) {
          const paramName = match[1];
          params.push({
            name: paramName,
            key: paramName,
            description: `Enter value for ${paramName}`,
            required: true
          });
        }

        this.urlParameters = params;
      } else {
        this.urlParameters = [];
      }
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
        this.isExecuting = true
        this.toolResult = null

        const response = await httpClient.post(`${API_BASE_URL}/execute_tool`, {
          server: this.selectedServer.name,
          tool: this.selectedTool.name,
          parameters: this.toolParams
        })

        if (!response.ok) {
          throw new Error('Failed to execute tool')
        }

        const result = await response.json()
        this.toolResult = result
      } catch (error) {
        console.error('Error executing tool:', error)
        this.toolResult = { error: error.message }
      } finally {
        this.isExecuting = false
      }
    },
    async getPrompt() {
      try {
        if (!this.selectedServer || !this.selectedPrompt) {
          throw new Error('Please select a server and prompt first')
        }

        this.isExecuting = true
        this.promptResult = null

        const response = await httpClient.post(`${API_BASE_URL}/get_prompt`, {
          server: this.selectedServer.name,
          prompt: this.selectedPrompt.name,
          parameters: this.promptParams
        })

        if (!response.ok) {
          throw new Error('Failed to get prompt')
        }

        const result = await response.json()
        this.promptResult = result
      } catch (error) {
        console.error('Error getting prompt:', error)
        this.promptResult = { error: error.message }
      } finally {
        this.isExecuting = false
      }
    },
    async fetchResource() {
      try {
        if (!this.selectedServer || !this.selectedResource) {
          throw new Error('Please select a server and resource first')
        }

        this.isExecuting = true
        this.resourceResult = null

        const response = await httpClient.post(`${API_BASE_URL}/fetch_resource`, {
          server: this.selectedServer.name,
          resource: this.selectedResource.name
        })

        if (!response.ok) {
          throw new Error('Failed to fetch resource')
        }

        const result = await response.json()
        this.resourceResult = result
      } catch (error) {
        console.error('Error fetching resource:', error)
        this.resourceResult = { error: error.message }
      } finally {
        this.isExecuting = false
      }
    },
    async fetchResourceFromTemplate() {
      try {
        if (!this.selectedServer || !this.selectedResourceTemplate) {
          throw new Error('Please select a server and resource template first')
        }

        this.isExecuting = true
        this.resourceTemplateResult = null

        let finalUrl = this.selectedResourceTemplate.uriTemplate
        for (const param of this.urlParameters) {
          const value = this.resourceTemplateParams[param.name]
          if (!value && param.required) {
            throw new Error(`Missing required parameter: ${param.name}`)
          }
          finalUrl = finalUrl.replace(`{${param.name}}`, encodeURIComponent(value))
        }

        const response = await httpClient.post(`${API_BASE_URL}/fetch_resource`, {
          server: this.selectedServer.name,
          resource: finalUrl,
        })

        if (!response.ok) {
          throw new Error('Failed to fetch resource from template')
        }

        const result = await response.json()
        this.resourceTemplateResult = result
      } catch (error) {
        console.error('Error fetching resource from template:', error)
        this.resourceTemplateResult = { error: error.message }
      } finally {
        this.isExecuting = false
      }
    },
    sendMessage() {
      if (!this.newMessage.trim()) return;

      // Add user message
      this.toolMessages.push({
        type: 'user',
        content: this.newMessage
      });

      // TODO: Add API call to send message and get response
      // For now, just add a placeholder response
      setTimeout(() => {
        this.toolMessages.push({
          type: 'assistant',
          content: 'This is a placeholder response. API integration needed.'
        });
      }, 1000);

      this.newMessage = '';
    },
    async listToolsOfTool() {
      try {
        this.isExecuting = true
        this.listToolsResult = null

        const response = await httpClient.post(`${API_BASE_URL}/dev/list_tool_of_chat`, {
          content: this.toolInput
        })

        if (!response.ok) {
          throw new Error('Failed to list tools of tool')
        }

        const result = await response.json()
        this.listToolsResult = result
      } catch (error) {
        console.error('Error listing tools of tool:', error)
        this.listToolsResult = { error: error.message }
      } finally {
        this.isExecuting = false
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
  cursor: pointer;
}

.server-tools:hover,
.server-prompts:hover,
.server-resources:hover,
.server-resource-templates:hover {
  color: #2196f3;
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

.tool-list,
.prompt-list,
.resource-list,
.template-list {
  position: absolute;
  left: 0;
  top: 100%;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 300px;
  max-width: 500px;
  display: none;
}

.server-tools:hover .tool-list,
.server-prompts:hover .prompt-list,
.server-resources:hover .resource-list,
.server-resource-templates:hover .template-list {
  display: block;
}

.tool-item,
.item-details {
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.tool-item:last-child,
.item-details:last-child {
  border-bottom: none;
}

.tool-item:hover,
.item-details:hover {
  background-color: #f5f5f5;
}

.tool-header,
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tool-name,
.item-name {
  font-weight: bold;
  color: #2196f3;
}

.tool-description,
.item-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  white-space: pre-line;
  word-wrap: break-word;
}

.tool-parameters,
.item-parameters,
.item-type,
.item-schema {
  font-size: 12px;
  margin-top: 8px;
}

.tool-parameters h4,
.item-parameters h4,
.item-type h4,
.item-schema h4 {
  margin: 8px 0;
  color: #333;
}

.tool-parameters ul,
.item-parameters ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tool-parameters li,
.item-parameters li {
  margin: 4px 0;
  color: #666;
}

.item-content {
  font-size: 14px;
}

.item-content pre {
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  margin: 8px 0;
}

.tool-parameter-form {
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.template-url {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.template-url h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.template-url pre {
  margin: 0;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  overflow-x: auto;
  font-family: monospace;
  font-size: 14px;
  color: #333;
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

.dialog-overlay {
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

.dialog-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.dialog-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel {
  background-color: #9e9e9e;
  color: white;
}

.btn-list-tools {
  background-color: #673ab7;
  color: white;
  margin-bottom: 20px;
}

.server-actions-header {
  margin-bottom: 20px;
}

.main-container {
  display: flex;
  min-height: 100vh;
}

.left-tabs {
  width: 200px;
  background-color: #f5f5f5;
  border-right: 1px solid #ddd;
  padding: 20px 0;
}

.tab-item {
  padding: 15px 20px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 500;
  color: #666;
}

.tab-item:hover {
  background-color: #e9e9e9;
}

.tab-item.active {
  background-color: #e3f2fd;
  color: #2196f3;
  border-right: 3px solid #2196f3;
}

.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.tab-content {
  height: 100%;
}

.tool-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
}

.tool-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 15px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
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

.tool-input {
  display: flex;
  gap: 10px;
}

.tool-input textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  height: 60px;
  font-family: inherit;
}

.btn-send {
  background-color: #2196f3;
  color: white;
  padding: 0 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-send:hover {
  background-color: #1976d2;
}

.tool-tools-section {
  margin-bottom: 20px;
  padding: 0;
  background-color: #f5f5f5;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  min-height: 200px;
}

.tools-container {
  width: 100%;
  max-width: 800px;
  padding: 20px;
}

.tools-input-wrapper {
  position: relative;
  margin-bottom: 15px;
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  padding-bottom: 50px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.tools-input {
  width: 100%;
  padding: 0;
  border: none;
  font-size: 14px;
  resize: none;
  background: transparent;
  line-height: 1.5;
  display: block;
  margin: 0;
  min-height: 100px;
  font-family: inherit;
  vertical-align: top;
}

.tools-input:focus {
  outline: none;
}

.tools-button-wrapper {
  position: absolute;
  bottom: 15px;
  right: 15px;
  height: 36px;
  display: flex;
  align-items: center;
}

.btn-list-tools {
  background-color: #673ab7;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-list-tools:hover:not(:disabled) {
  background-color: #5e35b1;
  transform: translateY(-1px);
}

.btn-list-tools:disabled {
  background-color: #b0bec5;
  cursor: not-allowed;
}

.tools-result {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.tools-result h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.server-list-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.btn-refresh {
  background: none;
  border: none;
  padding: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  background-color: #f0f0f0;
}

.btn-refresh:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.refresh-icon {
  font-size: 18px;
  line-height: 1;
}
</style>