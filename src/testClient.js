import { initializeClient } from './utils/sseClient.js';

async function main() {
  try {
    const { client, prompts, tools } = await initializeClient();
    console.log('Client initialized successfully');
    console.log('Available prompts:', prompts);
    console.log('Available tools:', tools);
  } catch (error) {
    console.error('Error:', error);
  }
}

main(); 