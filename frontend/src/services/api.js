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

/**
 * Fetch application review summary (GET /api/reviews/:conversation_id)
 */
export async function fetchReviewSummary(conversationId) {
  const url = `${API_BASE_URL}/api/reviews/${encodeURIComponent(conversationId)}`;
  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return { success: false, status: res.status, error: data?.detail || `HTTP ${res.status}` };
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, status: 0, error: err.message };
  }
}

/**
 * Approve a specific document draft version (POST /api/reviews/:conversation_id/approve)
 */
export async function approveApplicationReview({
  conversationId,
  documentId,
  documentVersion,
  confirmCorrectness,
  acknowledgeUnsubmitted,
}) {
  const url = `${API_BASE_URL}/api/reviews/${encodeURIComponent(conversationId)}/approve`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        document_version: documentVersion,
        confirm_correctness: Boolean(confirmCorrectness),
        acknowledge_unsubmitted: Boolean(acknowledgeUnsubmitted),
      }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return { success: false, status: res.status, error: data?.detail || `HTTP ${res.status}` };
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, status: 0, error: err.message };
  }
}

/**
 * Request corrections/changes on application review (POST /api/reviews/:conversation_id/request-changes)
 */
export async function requestReviewChanges({ conversationId, reason, fieldsToEdit = [] }) {
  const url = `${API_BASE_URL}/api/reviews/${encodeURIComponent(conversationId)}/request-changes`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        reason,
        fields_to_edit: fieldsToEdit,
      }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return { success: false, status: res.status, error: data?.detail || `HTTP ${res.status}` };
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, status: 0, error: err.message };
  }
}

/**
 * Fetch verified online or offline submission handoff instructions (GET /api/reviews/:conversation_id/handoff)
 */
export async function fetchHandoffGuidance(conversationId) {
  const url = `${API_BASE_URL}/api/reviews/${encodeURIComponent(conversationId)}/handoff`;
  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return { success: false, status: res.status, error: data?.detail || `HTTP ${res.status}` };
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, status: 0, error: err.message };
  }
}

/**
 * Record portal open or download handoff action into audit log (POST /api/reviews/:conversation_id/handoff/action)
 */
export async function recordHandoffAction({ conversationId, action, urlTarget }) {
  const url = `${API_BASE_URL}/api/reviews/${encodeURIComponent(conversationId)}/handoff/action`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        action,
        url_target: urlTarget || null,
      }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return { success: false, status: res.status, error: data?.detail || `HTTP ${res.status}` };
    }
    return { success: true, data };
  } catch (err) {
    return { success: false, status: 0, error: err.message };
  }
}

export { API_BASE_URL };
