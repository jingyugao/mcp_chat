<template>
  <div id="app">
    <h1>Server Manager</h1>
    <ServerManager 
      @server-added="handleServerAdded"
      @server-removed="handleServerRemoved"
      @server-connected="handleServerConnected"
      @server-disconnected="handleServerDisconnected"
      @server-selected="handleServerSelected"
    />
  </div>
</template>

<script>
import ServerManager from './components/ServerManager.vue'

export default {
  name: 'App',
  components: {
    ServerManager
  },
  methods: {
    handleServerAdded(server) {
      console.log('Server added:', server)
    },
    handleServerRemoved(server) {
      console.log('Server removed:', server)
    },
    handleServerConnected(server) {
      console.log('Server connected:', server)
    },
    handleServerDisconnected(server) {
      console.log('Server disconnected:', server)
    },
    handleServerSelected(server) {
      console.log('Server selected:', server)
    }
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin: 0;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #34495e;
  margin-bottom: 30px;
}
</style>
