<template>
  <div class="home">
    <h1 class="text-3xl font-bold text-center my-8">Welcome to MCP Debug</h1>
    <div class="flex justify-center gap-8 mt-12">
      <div 
        class="card p-6 bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow cursor-pointer w-64"
        @click="$router.push('/chat')"
      >
        <h2 class="text-xl font-semibold mb-4">Chat</h2>
        <p class="text-gray-600">Access the chat interface to interact with the AI assistant.</p>
      </div>
      
      <div 
        class="card p-6 bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow cursor-pointer w-64"
        @click="$router.push('/server-manager')"
      >
        <h2 class="text-xl font-semibold mb-4">Server Manager</h2>
        <p class="text-gray-600">Manage your server settings and configurations.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>

<style scoped>
.home {
  min-height: calc(100vh - 64px);
  background-color: #f8f9fa;
}
</style> 