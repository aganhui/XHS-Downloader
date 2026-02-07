const fs = require("fs");
const path = require("path");

function getLogs(limit = 100, offset = 0) {
  try {
    const logDir = process.env.XHS_LOG_DIR || "/tmp/xhs_logs";
    const logFile = path.join(logDir, "request_logs.jsonl");

    if (!fs.existsSync(logFile)) {
      return { logs: [], total: 0 };
    }

    const lines = fs.readFileSync(logFile, "utf8").split("\n").filter((line) => line.trim());
    const total = lines.length;

    // 从后往前读取（最新的在前）
    const logs = [];
    for (let i = lines.length - 1 - offset; i >= Math.max(0, lines.length - offset - limit); i--) {
      try {
        const logEntry = JSON.parse(lines[i]);
        logs.push(logEntry);
      } catch (e) {
        // 跳过无效的JSON行
        continue;
      }
    }

    return { logs, total };
  } catch (e) {
    console.error("Failed to read logs:", e);
    return { logs: [], total: 0 };
  }
}

function clearLogs() {
  try {
    const logDir = process.env.XHS_LOG_DIR || "/tmp/xhs_logs";
    const logFile = path.join(logDir, "request_logs.jsonl");
    if (fs.existsSync(logFile)) {
      fs.unlinkSync(logFile);
    }
    return true;
  } catch (e) {
    console.error("Failed to clear logs:", e);
    return false;
  }
}

module.exports = async function handler(req, res) {
  res.setHeader("Content-Type", "application/json");

  if (req.method === "GET") {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const limit = Math.min(100, Math.max(1, parseInt(url.searchParams.get("limit") || "50")));
    const offset = Math.max(0, parseInt(url.searchParams.get("offset") || "0"));

    const { logs, total } = getLogs(limit, offset);

    res.statusCode = 200;
    res.end(
      JSON.stringify({
        items: logs,
        total,
        limit,
        offset,
      })
    );
  } else if (req.method === "DELETE") {
    const success = clearLogs();
    res.statusCode = success ? 200 : 500;
    res.end(
      JSON.stringify({
        success,
        message: success ? "日志已清空" : "清空日志失败",
      })
    );
  } else {
    res.statusCode = 405;
    res.end(JSON.stringify({ message: "Method Not Allowed" }));
  }
};
