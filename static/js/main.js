import * as storage from "./storage.js";

const editor = document.getElementById("editor");
const output = document.getElementById("output");
const runBtn = document.getElementById("run");
const status = document.getElementById("status");
const execMode = document.getElementById("execMode");
const languageSelect = document.getElementById("language");
const localSelect = document.getElementById("localScripts");
const cloudSelect = document.getElementById("cloudScripts");
const btnSaveLocal = document.getElementById("saveLocal");
const btnLoadLocal = document.getElementById("loadLocal");
const btnDeleteLocal = document.getElementById("deleteLocal");
const btnRefreshCloud = document.getElementById("refreshCloud");
const btnSaveCloud = document.getElementById("saveCloud");
const btnLoadCloud = document.getElementById("loadCloud");
const scriptTitle = document.getElementById("scriptTitle");

const isAuth = document.body.dataset.authenticated === "true";

const SNIPPETS = {
  python: `print("Hello")
for i in range(3):
    print(i * i)
`,
  javascript: `console.log("Hello");
let sum = 0;
for (let i = 0; i < 4; i++) sum += i;
console.log("sum 0..3 =", sum);
`,
  cpp: `#include <iostream>
int main() {
  std::cout << "Hello" << std::endl;
  for (int i = 0; i < 3; i++) {
    std::cout << i * i << std::endl;
  }
  return 0;
}
`,
};

function getLanguage() {
  return languageSelect ? languageSelect.value : "python";
}

function fillLocalSelect() {
  if (!localSelect) return;
  localSelect.innerHTML = "";
  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = "— Select local —";
  localSelect.appendChild(opt0);
  for (const s of storage.listLocalScripts()) {
    const o = document.createElement("option");
    o.value = s.id;
    const tag = s.language && s.language !== "python" ? ` [${s.language}]` : "";
    o.textContent = (s.title || "Untitled") + tag;
    localSelect.appendChild(o);
  }
}

async function refreshCloudScripts() {
  if (!isAuth || !cloudSelect) return;
  cloudSelect.innerHTML = "";
  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = "— Select workspace —";
  cloudSelect.appendChild(opt0);
  const res = await fetch("/api/scripts", { credentials: "same-origin" });
  if (!res.ok) {
    if (status) {
      status.textContent =
        res.status === 401 || res.status === 302
          ? "Session expired — sign in again."
          : "Could not load workspace scripts (" + res.status + ").";
    }
    return;
  }
  let data;
  try {
    data = await res.json();
  } catch {
    if (status) status.textContent = "Invalid response from server.";
    return;
  }
  for (const s of data.scripts || []) {
    const o = document.createElement("option");
    o.value = String(s.id);
    const lg = s.language && s.language !== "python" ? ` [${s.language}]` : "";
    o.textContent = (s.title || "Untitled") + lg;
    cloudSelect.appendChild(o);
  }
}

async function executeCode() {
  if (!runBtn || !editor || !output || !status) return;
  if (!execMode) {
    status.textContent = "Runtime selector missing.";
    return;
  }
  runBtn.disabled = true;
  status.textContent = "Running…";
  output.textContent = "";
  output.classList.remove("error");
  const code = editor.value;
  const lang = getLanguage();
  try {
    if (execMode.value === "client") {
      if (lang === "cpp") {
        output.classList.add("error");
        output.textContent =
          "C++ needs the server compiler. Switch runtime to “Server”.";
        status.textContent = "Not available in browser";
        return;
      }
      if (lang === "javascript") {
        status.textContent = "JavaScript (browser)…";
        const { runJavaScriptClient } = await import("./js_client.js");
        const data = runJavaScriptClient(code);
        if (data.stderr) output.classList.add("error");
        output.textContent =
          [data.stdout, data.stderr].filter(Boolean).join("\n") || "(no output)";
        status.textContent = data.stderr ? "Finished with error" : "Finished (browser)";
        return;
      }
      status.textContent = "Pyodide…";
      const pyodide = await import("./pyodide.js");
      const data = await pyodide.runPythonClient(code);
      if (data.stderr) output.classList.add("error");
      output.textContent =
        [data.stdout, data.stderr].filter(Boolean).join("\n") || "(no output)";
      status.textContent = data.stderr ? "Finished with error" : "Finished (browser)";
      return;
    }

    const res = await fetch("/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language: lang }),
      credentials: "same-origin",
    });
    const data = await res.json();
    if (!res.ok) {
      output.classList.add("error");
      output.textContent = data.error || JSON.stringify(data);
      status.textContent = "HTTP " + res.status;
      return;
    }
    const parts = [];
    if (data.stdout) parts.push(data.stdout);
    if (data.stderr) {
      output.classList.add("error");
      parts.push(data.stderr);
    }
    output.textContent = parts.join("\n") || "(no output)";
    status.textContent = data.stderr ? "Finished with error" : "Finished (server)";
  } catch (e) {
    output.classList.add("error");
    output.textContent = "Error: " + e.message;
    status.textContent = "Failed";
  } finally {
    if (runBtn) runBtn.disabled = false;
  }
}

function loadLocalSelected() {
  const id = localSelect.value;
  if (!id) {
    if (status) status.textContent = "Pick a script from “This browser”.";
    return;
  }
  const s = storage.getLocalScript(id);
  if (!s) {
    if (status) status.textContent = "That local script was not found.";
    return;
  }
  editor.value = s.code;
  if (scriptTitle) scriptTitle.value = s.title;
  if (languageSelect && s.language) {
    languageSelect.value = s.language;
  }
}

function saveLocal() {
  try {
    const title = (scriptTitle && scriptTitle.value) || "Untitled";
    const code = editor ? editor.value : "";
    storage.saveLocalScript(title, code, getLanguage());
    fillLocalSelect();
    if (status) status.textContent = "Saved in this browser.";
  } catch (e) {
    console.error(e);
    if (status) status.textContent = "Local save failed: " + e.message;
  }
}

function deleteLocalSelected() {
  const id = localSelect.value;
  if (!id) {
    if (status) status.textContent = "Select a local script to delete.";
    return;
  }
  storage.deleteLocalScript(id);
  fillLocalSelect();
  if (status) status.textContent = "Local script removed.";
}

async function saveCloud() {
  if (!isAuth) return;
  const title = (scriptTitle && scriptTitle.value) || "Untitled";
  const code = editor ? editor.value : "";
  let res;
  try {
    res = await fetch("/api/scripts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ title, code, language: getLanguage() }),
    });
  } catch (e) {
    if (status) status.textContent = "Network: " + e.message;
    return;
  }
  if (!res.ok) {
    let detail = String(res.status);
    try {
      const err = await res.json();
      if (err && err.error) detail = err.error;
    } catch {
      /* ignore */
    }
    if (status) {
      status.textContent =
        res.status === 401 ? "Session expired — sign in again." : "Save failed: " + detail;
    }
    return;
  }
  await refreshCloudScripts();
  if (status) status.textContent = "Saved to your workspace.";
}

async function loadCloudSelected() {
  if (!isAuth || !cloudSelect) return;
  const id = cloudSelect.value;
  if (!id) {
    if (status) status.textContent = "Pick a script from “Your workspace”.";
    return;
  }
  const res = await fetch("/api/scripts/" + id, { credentials: "same-origin" });
  if (!res.ok) {
    if (status) {
      status.textContent =
        res.status === 401 ? "Session expired — sign in again." : "Load failed (" + res.status + ").";
    }
    return;
  }
  let row;
  try {
    row = await res.json();
  } catch {
    if (status) status.textContent = "Invalid server response.";
    return;
  }
  editor.value = row.code;
  if (scriptTitle) scriptTitle.value = row.title;
  if (languageSelect && row.language) {
    languageSelect.value = row.language;
  }
  if (status) status.textContent = "Loaded from workspace.";
}

try {
  if (runBtn) runBtn.addEventListener("click", executeCode);
  else console.error("RunStudio: #run missing");

  if (btnSaveLocal) btnSaveLocal.addEventListener("click", saveLocal);
  else console.error("RunStudio: #saveLocal missing");

  if (btnLoadLocal) btnLoadLocal.addEventListener("click", loadLocalSelected);
  else console.error("RunStudio: #loadLocal missing");

  if (btnDeleteLocal) btnDeleteLocal.addEventListener("click", deleteLocalSelected);
  else console.error("RunStudio: #deleteLocal missing");

  if (btnRefreshCloud) btnRefreshCloud.addEventListener("click", () => refreshCloudScripts());
  if (btnSaveCloud) btnSaveCloud.addEventListener("click", saveCloud);
  if (btnLoadCloud) btnLoadCloud.addEventListener("click", loadCloudSelected);

  if (languageSelect && editor) {
    languageSelect.addEventListener("change", () => {
      const v = getLanguage();
      if (SNIPPETS[v]) editor.value = SNIPPETS[v];
    });
    editor.value = SNIPPETS.python;
  }

  fillLocalSelect();
  if (isAuth) void refreshCloudScripts();
} catch (e) {
  console.error("RunStudio: init failed", e);
}
