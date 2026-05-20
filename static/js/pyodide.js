/**
 * Browser-side Python via Pyodide (CDN). Loaded on first client run.
 */

let pyodideInstance = null;
let loadPromise = null;

function injectPyodideScript() {
  return new Promise((resolve, reject) => {
    if (typeof globalThis.loadPyodide === "function") {
      resolve();
      return;
    }
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js";
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Could not load Pyodide from the CDN."));
    document.head.appendChild(s);
  });
}

export async function ensurePyodide() {
  if (pyodideInstance) return pyodideInstance;
  if (!loadPromise) {
    loadPromise = (async () => {
      await injectPyodideScript();
      const py = await globalThis.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/",
      });
      pyodideInstance = py;
      return py;
    })();
  }
  try {
    return await loadPromise;
  } catch (e) {
    loadPromise = null;
    throw e;
  }
}

/**
 * @param {string} code
 * @returns {Promise<{ stdout: string, stderr: string }>}
 */
export async function runPythonClient(code) {
  const py = await ensurePyodide();
  let out = "";
  py.setStdout({ batched: (msg) => (out += msg) });
  py.setStderr({ batched: (msg) => (out += msg) });
  try {
    await py.runPythonAsync(code);
    return { stdout: out, stderr: "" };
  } catch (e) {
    return { stdout: out, stderr: String(e) };
  }
}
