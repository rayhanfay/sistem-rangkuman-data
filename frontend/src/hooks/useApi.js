import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

class ApiService {
  async getDashboardData(token) {
    const config = { headers: { Authorization: `Bearer ${token}` } };
    return apiClient.get('/api/dashboard/latest-mcp', config).then(res => res.data);
  }

  async getHistory(token) {
    const config = { headers: { Authorization: `Bearer ${token}` } };
    return apiClient.get('/api/history-results', config).then(res => res.data);
  }
  
  async getStatsData(token, timestamp) {
    if (!timestamp) throw new Error("Timestamp diperlukan");
    const config = { headers: { Authorization: `Bearer ${token}` } };
    return apiClient.get(`/api/stats-data?timestamp=${timestamp}`, config).then(res => res.data);
  }

  async deleteHistory(token, timestamp) {
    const config = { headers: { Authorization: `Bearer ${token}` } };
    return apiClient.delete(`/api/delete-history/${timestamp}`, config).then(res => res.data);
  }

  async triggerMcpAnalysis(token) {
    const config = { headers: { Authorization: `Bearer ${token}` } };
    return apiClient.post('/api/mcp/trigger-analysis', {}, config).then(res => res.data);
  }

  async uploadFile(token, file) {
    const formData = new FormData();
    formData.append('file', file);
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    };
    return apiClient.post('/api/upload', formData, config).then(res => res.data);
  }
}

export default new ApiService();