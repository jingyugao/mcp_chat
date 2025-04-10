import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListPromptsRequestSchema, ListPromptsResultSchema, ListToolsRequestSchema, ListToolsResultSchema } from '@modelcontextprotocol/sdk/types.js';

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