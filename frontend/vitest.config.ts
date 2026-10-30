import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    maxWorkers: 2,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
  },
});
