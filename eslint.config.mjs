import js from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["public/", "node_modules/"] },
  js.configs.recommended,
  {
    files: ["static/**/*.js"],
    languageOptions: {
      sourceType: "script",
      globals: globals.browser,
    },
  },
  {
    files: ["*.config.mjs"],
    languageOptions: {
      sourceType: "module",
      globals: globals.node,
    },
  },
];
