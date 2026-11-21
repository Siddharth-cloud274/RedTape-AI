/**
 * RedTape AI - Chat Transport Layer
 * 
 * Milestone M3: Real HTTP transport sending requests to POST /api/chat.
 * Does not fall back to mock responses on error.
 */

import { sendChatMessageApi } from './api';

/**
 * Dispatches a chat message to the FastAPI backend.
 * 
 * @param {Object} params
 * @param {string|null} params.conversationId - Backend session ID (or null for new)
 * @param {string} params.clientMessageId - UUID for client message turn
 * @param {string} params.message - Raw text message
 * @returns {Promise<{ conversation_id: string, message_id: string, reply: string, mode: string }>}
 */
export async function sendChatMessage({ conversationId, clientMessageId, message }) {
  const result = await sendChatMessageApi({
    conversationId,
    clientMessageId,
    message,
  });

  if (!result.success) {
    const error = new Error(result.error || 'Failed to send message to backend.');
    error.status = result.status;
    throw error;
  }

  return result.data;
}
