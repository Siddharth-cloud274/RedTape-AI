/**
 * API Service for RedTape AI Frontend
 * Reads base URL from VITE_API_URL or defaults to http://localhost:8000
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Check backend health status (GET /api/health)
 */
export async function checkBackendHealth() {
  const url = `${API_BASE_URL}/api/health`;
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      url,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Unable to connect to backend server',
      url,
    };
  }
}

/**
 * Send a chat message to the FastAPI backend (POST /api/chat)
 * 
 * @param {Object} params
 * @param {string|null} params.conversationId
 * @param {string} params.clientMessageId
 * @param {string} params.message
 * @returns {Promise<{ success: boolean, data?: any, status?: number, error?: string }>}
 */
export async function sendChatMessageApi({ conversationId, clientMessageId, message }) {
  const url = `${API_BASE_URL}/api/chat`;

  const payload = {
    conversation_id: conversationId || null,
    client_message_id: clientMessageId,
    message: message.trim(),
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const responseData = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMessage =
        responseData?.detail ||
        (Array.isArray(responseData?.detail)
          ? responseData.detail.map((e) => e.msg).join(', ')
          : `HTTP error ${response.status}: ${response.statusText}`);

      return {
        success: false,
        status: response.status,
        error: errorMessage,
      };
    }

    return {
      success: true,
      status: response.status,
      data: responseData,
    };
  } catch (networkError) {
    return {
      success: false,
      status: 0,
      error: networkError.message || 'Network error: unable to reach RedTape AI backend.',
    };
  }
}

/**
 * Retrieve conversation details, message history, and confirmed facts (GET /api/conversations/:id)
 * 
 * @param {string} conversationId
 * @returns {Promise<{ success: boolean, data?: any, status?: number, error?: string }>}
 */
export async function getConversationHistory(conversationId) {
  const url = `${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}`;
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    const responseData = await response.json().catch(() => null);

    if (!response.ok) {
      return {
        success: false,
        status: response.status,
        error: responseData?.detail || `HTTP error ${response.status}: ${response.statusText}`,
      };
    }

    return {
      success: true,
      status: response.status,
      data: responseData,
    };
  } catch (error) {
    return {
      success: false,
      status: 0,
      error: error.message || 'Network error: unable to load conversation history.',
    };
  }
}

/**
 * Trigger official draft PDF generation (POST /api/documents/draft)
 */
export async function createDocumentDraft({ conversationId, templateId = 'kolkata_domicile_higher_studies', customFieldValues = null }) {
  const url = `${API_BASE_URL}/api/documents/draft`;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        template_id: templateId,
        custom_field_values: customFieldValues,
      }),
    });

    const data = await response.json().catch(() => null);
    if (!response.ok) {
      return {
        success: false,
        status: response.status,
        error: data?.detail || `HTTP error ${response.status}`,
      };
    }
    return { success: true, data };
  } catch (error) {
    return { success: false, status: 0, error: error.message };
  }
}

/**
 * Regenerate official draft PDF (POST /api/documents/:id/regenerate)
 */
export async function regenerateDocumentDraft({ documentId, updatedFields }) {
  const url = `${API_BASE_URL}/api/documents/${encodeURIComponent(documentId)}/regenerate`;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ updated_fields: updatedFields }),
    });

    const data = await response.json().catch(() => null);
    if (!response.ok) {
      return {
        success: false,
        status: response.status,
        error: data?.detail || `HTTP error ${response.status}`,
      };
    }
    return { success: true, data };
  } catch (error) {
    return { success: false, status: 0, error: error.message };
  }
}

export function getDocumentPreviewUrl(documentId) {
  return `${API_BASE_URL}/api/documents/${encodeURIComponent(documentId)}/preview`;
}

export function getDocumentDownloadUrl(documentId) {
  return `${API_BASE_URL}/api/documents/${encodeURIComponent(documentId)}/download`;
}

export { API_BASE_URL };
