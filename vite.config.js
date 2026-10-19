import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const groqApiKey = env.VITE_GROQ_API_KEY || env.groq_api_key || env.LLM_API_KEY || '';

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      open: false,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        }
      }
    }
  };
});
