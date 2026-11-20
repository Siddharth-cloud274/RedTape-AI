/**
 * API Service for RedTape AI Frontend
 * Reads base URL from VITE_API_URL or defaults to http://localhost:8000
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

export { API_BASE_URL };
