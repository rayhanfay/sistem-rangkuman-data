import apiService from './api';

class AuthService {
  constructor() {
    this.token = localStorage.getItem('access_token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getToken() {
    return this.token;
  }

  async login(credentials) {
    try {
      const response = await apiService.login(credentials);
      this.setToken(response.access_token);
      return response;
    } catch (error) {
      throw error;
    }
  }

  async register(userData) {
    try {
      const response = await apiService.register(userData);
      return response;
    } catch (error) {
      throw error;
    }
  }

  async verifyToken() {
    try {
      const response = await apiService.verifyToken();
      return response;
    } catch (error) {
      throw error;
    }
  }

  logout() {
    this.setToken(null);
    apiService.logout();
  }

  isAuthenticated() {
    return !!this.token;
  }
}

export default new AuthService();