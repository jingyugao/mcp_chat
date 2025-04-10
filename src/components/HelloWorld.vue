<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <div>
      <input v-model="url" placeholder="Enter URL" />
      <button @click="list_tools">List Tools</button>
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
  name: 'HelloWorld',
  props: {
    msg: String
  },
  data() {
    return {
      url: 'http://127.0.0.1:9002/sse',
      result: ''
    };
  },
  methods: {
    async list_tools() {
      const transport = new SSEClientTransport(
        new URL('http://localhost:9002/sse')
      );

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
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
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
}

button:hover {
  background-color: #369b72;
}

textarea {
  width: 100%;
  height: 200px;
  margin-top: 20px;
  padding: 10px;
  font-family: monospace;
}
</style>
