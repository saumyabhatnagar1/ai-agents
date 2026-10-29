// Node 18 has Event, but CustomEvent is only global from Node 19.
// mcp-memory-libsql's tmcp dependency constructs CustomEvent at startup.
if (typeof globalThis.CustomEvent !== "function") {
  globalThis.CustomEvent = class CustomEvent extends Event {
    constructor(type, params = {}) {
      super(type, params);
      this.detail = params.detail ?? null;
    }
  };
}
