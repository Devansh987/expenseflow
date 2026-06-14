import axios from 'axios';

const API = axios.create({ 
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' 
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const register = (data) => API.post('/auth/register', data);
export const login = (email, password) => {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  return API.post('/auth/token', form);
};
export const getMe = () => API.get('/auth/me');
export const getGroups = () => API.get('/groups');
export const createGroup = (name) => API.post('/groups', { name });
export const getGroupDetail = (id) => API.get(`/groups/${id}`);
export const addMember = (groupId, userId) => API.post(`/groups/${groupId}/members/${userId}`);
export const removeMember = (groupId, userId) => API.delete(`/groups/${groupId}/members/${userId}`);
export const createExpense = (groupId, data) => API.post(`/groups/${groupId}/expenses`, data);
export const getBalances = (groupId) => API.get(`/groups/${groupId}/balances`);
export const createSettlement = (groupId, data) => API.post(`/groups/${groupId}/settlements`, data);
export const getSettlements = (groupId) => API.get(`/groups/${groupId}/settlements`);
export const uploadCSV = (groupId, file) => {
  const form = new FormData();
  form.append('file', file);
  return API.post(`/groups/${groupId}/import`, form);
};
export const getImports = (groupId) => API.get(`/groups/${groupId}/imports`);
export const getImportReport = (groupId, sessionId) => API.get(`/groups/${groupId}/imports/${sessionId}/report`);

export default API;
