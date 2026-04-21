import api from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export async function login(credentials: LoginCredentials): Promise<void> {
  const response = await api.post('/login', credentials);
  if (!response.data.success) {
    throw new Error('Login failed');
  }
}

export async function checkAuth(): Promise<boolean> {
  try {
    const response = await api.get('/user');
    return !!response.data;
  } catch {
    return false;
  }
}
