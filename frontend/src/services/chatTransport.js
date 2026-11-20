/**
 * RedTape AI - Chat Transport Adapter
 * 
 * Milestone M2: Mock transport simulating message dispatch with async latency.
 * In Milestone M3, this will be replaced with real POST /api/chat integration.
 */

const MOCK_RESPONSE_TEXT = 
  'Demo mode: your message was received. AI assistance will be enabled in a later milestone.';

/**
 * Sends a chat message to the transport layer.
 * 
 * @param {string} conversationId 
 * @param {string} userText 
 * @returns {Promise<{ id: string, role: string, content: string, timestamp: string, isMock: boolean }>}
 */
export async function sendChatMessage(conversationId, userText) {
  // Simulate network/generation latency (450ms)
  await new Promise((resolve) => setTimeout(resolve, 450));

  return {
    id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
    role: 'assistant',
    content: MOCK_RESPONSE_TEXT,
    timestamp: new Date().toISOString(),
    isMock: true,
  };
}
