<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <div>
      <input v-model="url" placeholder="Enter URL" />
      <button @click="add_url">Add URL</button>
      <button @click="list_tools">List Tools</button>
      <button @click="getCurrentTime">Get Current Time</button>
    </div>
    <div class="url-list">
      <h3>URL List</h3>
      <ul>
        <li v-for="(item, index) in urlList" :key="index">
          {{ item }}
          <button @click="remove_url(index)" class="remove-btn">Remove</button>
        </li>
      </ul>
    </div>
    <div>
      <textarea v-model="result" readonly></textarea>
    </div>
  </div>
</template>

<script>
/* eslint-disable */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

export default {
  name: 'MCP',
  props: {
    msg: String
  },
  data() {
    return {
      url: 'http://127.0.0.1:9002/sse',
      result: '',
      urlList: [],
      urlClient: new Map(),
      currentTime: ''
    };
  },
  methods: {
    async add_url() {
      if (this.url && !this.urlList.includes(this.url)) {
        const transport = new SSEClientTransport(
          new URL(this.url)
        );
        const client = new Client( );
      
        try {
          await client.connect(transport);
           this.urlClient.set(this.url,  client);
        } catch (error) {
          client.close();
          console.error('Error:', error);
          this.result = `Error: ${error.message}`;
        }
      }
      this.urlList.push(this.url);

    },
    remove_url(index) {
      this.urlList.splice(index, 1);
    },
    async list_tools() {
    
      const client = new Client(
        {
          name: "example-client",
          version: "1.0.0"
        }
      );
      
      // Connect to the server
      await client.connect(transport);
      return ;

      // List tools
      const tools = await client.listTools();
      console.log('Available tools:', tools);

    },
    async getCurrentTime() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/time');
        const data = await response.json();
        this.result = `Current Time: ${data.formatted_time}`;
      } catch (error) {
        console.error('Error fetching time:', error);
        this.result = `Error fetching time: ${error.message}`;
      }
    },
    hello() {

    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10px 0;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.url-list {
  margin: 20px 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

input {
  margin-right: 10px;
  padding: 5px;
}

button {
  padding: 5px 10px;
  background-color: #42b983;
  color: white;
  border: none;
  cursor: pointer;
  margin-right: 5px;
}

button:hover {
  background-color: #369b72;
}

.remove-btn {
  background-color: #ff4444;
}

.remove-btn:hover {
  background-color: #cc0000;
}

textarea {
  width: 100%;
  height: 200px;
  margin-top: 20px;
  padding: 10px;
  font-family: monospace;
}
</style>
