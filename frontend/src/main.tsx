import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import AppRouter from "./router";

const RootApp = () => (
  <Suspense fallback={<div>Loading app...</div>}>
    <AppRouter />
  </Suspense>
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RootApp />
  </React.StrictMode>
);