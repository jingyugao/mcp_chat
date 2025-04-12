<template>
  <div id="app">
    <h1>Server Manager</h1>
    <ServerManager />
  </div>
</template>

<script>
import ServerManager from './components/ServerManager.vue'

export default {
  name: 'App',
  components: {
    ServerManager
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
