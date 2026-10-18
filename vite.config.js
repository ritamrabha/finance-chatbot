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
        '/api/groq': {
          target: 'https://api.groq.com/openai/v1',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/groq/, ''),
          headers: {
            Authorization: `Bearer ${groqApiKey}`,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
          }
        }
      }
    }
  };
});
