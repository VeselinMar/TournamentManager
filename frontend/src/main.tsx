import React from "react";
import ReactDOM from "react-dom/client";
import AppRouter from "./router";

// ===== Patch Emotion / MUI insertRule to catch invalid CSS =====
const patchEmotionInsertRule = () => {
  for (const sheet of Array.from(document.styleSheets) as CSSStyleSheet[]) {
    const originalInsertRule = sheet.insertRule;

    sheet.insertRule = function (rule: string, index?: number) {
      try {
        return originalInsertRule.call(this, rule, index);
      } catch (err) {
        console.error("Invalid CSS rule detected:", rule, err);
        return 0;
      }
    };
  }
};

document.addEventListener("DOMContentLoaded", () => {
  patchEmotionInsertRule();
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
);