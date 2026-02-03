import axios from 'axios';
import { auth } from '../utils/firebase';

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

apiClient.interceptors.request.use(
    async (config) => {
        const currentUser = auth.currentUser;
        if (currentUser) {
            try {
                const token = await currentUser.getIdToken();
                config.headers['Authorization'] = `Bearer ${token}`;
            } catch (error) {
                console.error("Gagal mendapatkan token:", error);
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

class ApiService {

    async downloadAnalyzedData({ file_format, source, timestamp, area, sheet_name }) {
        const params = new URLSearchParams({ file_format, source });
        if (timestamp) params.append('timestamp', timestamp);
        if (area && area !== 'Semua Area') params.append('area', area);
        if (sheet_name) params.append('sheet_name', sheet_name);

        return apiClient.get(`/api/web/download?${params.toString()}`, {
            responseType: 'blob', 
        }).then(response => {
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            let filename = `data_aset_${source}.${file_format}`;
            
            const contentDisposition = response.headers['content-disposition'];
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch.length > 1) {
                    filename = filenameMatch[1];
                }
            }
            
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        });
    }

    async getToolChoice(user_prompt, tools, conversation_history) {
        const payload = { user_prompt, tools, conversation_history };
        return apiClient.post('/api/web/llm-router', payload).then(res => res.data);
    }

    async summarizeResult(user_prompt, tool_result, conversation_history) {
        const payload = { user_prompt, tool_result, conversation_history };
        return apiClient.post('/api/web/llm-summarize', payload).then(res => res.data);
    }
}

const apiServiceInstance = new ApiService();
export default apiServiceInstance;