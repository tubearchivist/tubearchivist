'use strict';
module.exports = {
  extends: ['eslint:recommended', 'eslint-config-prettier'],
  parserOptions: {
    ecmaVersion: 2020,
  },
  env: {
    browser: true,
  },
  rules: {
    strict: ['error', 'global'],
    'no-unused-vars': ['error', { vars: 'local' }],
    eqeqeq: ['error', 'always', { null: 'ignore' }],
    curly: ['error', 'multi-line'],
    'no-var': 'error',
  },
};
