import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

async function initializeClient() {
  try {
    const transport = new SSEClientTransport(
      new URL('http://127.0.0.1:9002/sse')
    );

    const client = new Client(
      {
        name: "example-client",
        version: "1.0.0"
      }
    );

    // Connect to the server
    await client.connect(transport);

    // List prompts
    const prompts = await client.listPrompts();
    console.log('Available prompts:', prompts);

    // List tools
    const tools = await client.listTools();
    console.log('Available tools:', tools);

    return {
      client,
      prompts,
      tools
    };
  } catch (error) {
    console.error('Error:', error);
    if (error.message.includes('CORS')) {
      console.error('CORS Error detected. Please check server configuration.');
    }
    throw error;
  }
}

// Run the test
initializeClient().catch(console.error); 