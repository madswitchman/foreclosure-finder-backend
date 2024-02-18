module.exports = {
  extends: [
    "eslint:recommended",
    "google",
  ],
  env: {
    es6: true,
    node: true,
    browser: true,
  },
  parserOptions: {
    "ecmaVersion": 2018,
  },
  rules: {
    "no-restricted-globals": ["error", "name", "length"],
    "prefer-arrow-callback": "error",
    "quotes": ["error", "double", {"allowTemplateLiterals": true}],
    "linbreak-style": 0,
  },
  overrides: [
    {
      files: ["**/*.spec.*"],
      env: {
        mocha: true,
      },
      rules: {},
    },
  ],
  globals: {SwaggerEditor: false},
};
