window.mermaid = window.mermaid || {};
document.addEventListener("DOMContentLoaded", function () {
  try {
    mermaid.initialize({ startOnLoad: true, securityLevel: "strict" });
  } catch (e) {
    console.error("Mermaid init error:", e);
  }
});
