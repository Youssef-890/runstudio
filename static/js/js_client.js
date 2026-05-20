/**
 * In-browser JavaScript (client mode). Captures console.log, then restores it.
 */

export function runJavaScriptClient(code) {
  const lines = [];
  const oldLog = console.log;
  console.log = (...args) => {
    lines.push(args.map((a) => (typeof a === "object" ? JSON.stringify(a) : String(a))).join(" "));
    oldLog.apply(console, args);
  };
  try {
    const fn = new Function(`"use strict";\n${code}`);
    const ret = fn();
    if (ret !== undefined) {
      lines.push(String(ret));
    }
    const stdout = lines.length ? lines.join("\n") + "\n" : "";
    return { stdout, stderr: "" };
  } catch (e) {
    return { stdout: lines.join("\n"), stderr: String(e) };
  } finally {
    console.log = oldLog;
  }
}
