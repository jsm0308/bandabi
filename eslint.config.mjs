import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import unicorn from "eslint-plugin-unicorn";

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      "react-hooks": reactHooks,
      unicorn,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,

      // Common "vibe coding mess" patterns
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",

      // Convention enforcement
      "unicorn/filename-case": [
        "error",
        { case: "kebabCase", ignore: ["README.md"] },
      ],

      // Reduce unsafe patterns
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/consistent-type-imports": "error",
    },
  },
];
