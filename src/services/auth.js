import { reactive } from 'vue';

export const DEFAULT_USER = 'admin';
export const DEFAULT_PASSWORD = 'demo-o5FNMgTTn2gK';

export const authState = reactive({
  isAuthenticated: true, // Default to true so user NEVER has to type password on startup
  user: localStorage.getItem('finsight_auth_user') || DEFAULT_USER,
  role: 'Chief Financial Officer (CFO)',
  name: 'Finance Administrator',
  defaultUser: DEFAULT_USER,
  defaultPassword: DEFAULT_PASSWORD
});

export async function login(username, password) {
  // If no username/password provided, use default credentials automatically
  const u = (username && username.trim()) ? username.trim() : DEFAULT_USER;
  const p = (password && password.trim()) ? password.trim() : DEFAULT_PASSWORD;

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    });
    if (res.ok) {
      const data = await res.json();
      authState.isAuthenticated = true;
      authState.user = data.user?.username || u;
      authState.name = data.user?.name || 'Finance Administrator';
      authState.role = data.user?.role || 'Chief Financial Officer (CFO)';
      localStorage.setItem('finsight_auth_user', authState.user);
      return { success: true };
    }
  } catch (err) {
    // Fallback if backend network is offline
    if (p === DEFAULT_PASSWORD || !p) {
      authState.isAuthenticated = true;
      authState.user = u;
      localStorage.setItem('finsight_auth_user', u);
      return { success: true };
    }
  }

  return { success: false, error: 'Invalid credentials. Default password is ' + DEFAULT_PASSWORD };
}

export function logout() {
  authState.isAuthenticated = false;
  localStorage.removeItem('finsight_auth_user');
}

export function loginWithDefault() {
  authState.isAuthenticated = true;
  authState.user = DEFAULT_USER;
  localStorage.setItem('finsight_auth_user', DEFAULT_USER);
}
