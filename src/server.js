import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListPromptsRequestSchema, ListPromptsResultSchema, ListToolsRequestSchema, ListToolsResultSchema } from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import cors from 'cors';

const app = express();

// 配置CORS
app.use(cors({
  origin: '*', // 允许所有来源访问，生产环境应该设置具体的域名
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

const transport = new StdioServerTransport();

console.log('Creating server...');

const server = new Server(
  {
    name: 'example-server',
    version: '1.0.0'
  },
  {
    transport,
    capabilities: {
      prompts: true,
      tools: true
    }
  }
);

// 设置Express路由
app.get('/sse', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  // 这里可以添加SSE事件处理逻辑
});

// 启动Express服务器
const PORT = 9002;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

console.log('Server created, registering handlers...');

// Register request handlers
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  console.log('Handling prompts/list request');
  return {
    prompts: [
      {
        name: 'example-prompt',
        description: 'An example prompt'
      }
    ]
  };
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  console.log('Handling tools/list request');
  return {
    tools: [
      {
        name: 'example-tool',
        description: 'An example tool'
      }
    ]
  };
});

console.log('Handlers registered, server ready');

// Keep the process running
process.stdin.resume(); 