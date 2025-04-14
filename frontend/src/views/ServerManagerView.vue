<template>
  <div class="server-manager-view">
    <div class="page-header">
      <h1 class="text-3xl font-bold">Server Manager</h1>
      <p class="text-gray-600 mt-2">Manage your server connections and configurations</p>
    </div>
    <div class="content-wrapper">
      <ServerManager />
    </div>
  </div>
</template>

<script>
import ServerManager from '../components/ServerManager.vue'

export default {
  name: 'ServerManagerView',
  components: {
    ServerManager
  }
}
</script>

<style scoped>
.server-manager-view {
  padding: 2rem;
  min-height: calc(100vh - 64px);
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}
</style> 