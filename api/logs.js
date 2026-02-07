const fs = require("fs");
const path = require("path");
const http = require("http");

function getLogsFromFile(limit = 100, offset = 0) {
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
    console.error("Failed to read logs from file:", e);
    return { logs: [], total: 0 };
  }
}

async function getLogsFromAPI(limit = 100, offset = 0, requestHost = null) {
  return new Promise((resolve) => {
    try {
      // 获取内部 API 密钥（用于绕过 Vercel 预览部署的身份验证）
      const internalKey = process.env.XHS_INTERNAL_API_KEY || "";

      // 构建基础 URL
      let baseUrl;
      if (process.env.VERCEL_URL) {
        // Vercel 环境（包括预览和生产）
        baseUrl = `https://${process.env.VERCEL_URL}`;
      } else if (requestHost && !requestHost.includes('localhost')) {
        // 从请求中获取 host（非本地）
        baseUrl = `https://${requestHost}`;
      } else {
        // 本地开发环境
        baseUrl = process.env.HOST || "http://localhost:8000";
      }

      // FastAPI 的日志端点：直接访问 /api/app/internal-logs
      const url = `${baseUrl}/api/app/internal-logs?limit=${limit}&offset=${offset}`;

      // 构建请求头
      const headers = {
        'Content-Type': 'application/json',
      };

      // 如果配置了内部 API 密钥，添加到请求头
      if (internalKey) {
        headers['x-internal-api-key'] = internalKey;
      }

      fetch(url, { headers })
        .then(async (response) => {
          if (!response.ok) {
            // 如果是 401 或 403，可能是身份验证问题
            if (response.status === 401 || response.status === 403) {
              console.log(`API log fetch requires authentication (${response.status}), skipping`);
              resolve({ logs: [], total: 0 });
              return;
            }
            const errorText = await response.text().catch(() => '');
            console.error(`Failed to read logs from API: HTTP ${response.status}`);
            throw new Error(`HTTP ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          resolve({ logs: data.items || [], total: data.total || 0 });
        })
        .catch((e) => {
          // 静默失败，不影响文件系统日志的显示
          resolve({ logs: [], total: 0 });
        });
    } catch (e) {
      console.error("Failed to read logs from API:", e);
      resolve({ logs: [], total: 0 });
    }
  });
}

async function getLogs(limit = 100, offset = 0, requestHost = null) {
  // 同时从文件系统和 API 获取日志，然后合并
  const [fileLogs, apiLogs] = await Promise.all([
    Promise.resolve(getLogsFromFile(limit, offset)),
    getLogsFromAPI(limit, offset, requestHost),
  ]);

  // 合并日志，按时间戳排序（最新的在前）
  const allLogs = [...fileLogs.logs, ...apiLogs.logs];
  allLogs.sort((a, b) => {
    const timeA = new Date(a.timestamp).getTime();
    const timeB = new Date(b.timestamp).getTime();
    return timeB - timeA; // 降序，最新的在前
  });

  // 去重（基于 timestamp 和 endpoint）
  const seen = new Set();
  const uniqueLogs = allLogs.filter((log) => {
    const key = `${log.timestamp}-${log.endpoint}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });

  // 应用 limit 和 offset
  const total = fileLogs.total + apiLogs.total;
  const paginatedLogs = uniqueLogs.slice(offset, offset + limit);

  return { logs: paginatedLogs, total };
}

async function clearLogs(requestHost = null) {
  let fileSuccess = false;
  let apiSuccess = false;

  // 清空文件日志
  try {
    const logDir = process.env.XHS_LOG_DIR || "/tmp/xhs_logs";
    const logFile = path.join(logDir, "request_logs.jsonl");
    if (fs.existsSync(logFile)) {
      fs.unlinkSync(logFile);
    }
    fileSuccess = true;
  } catch (e) {
    console.error("Failed to clear file logs:", e);
  }

  // 清空 API 日志
  try {
    const internalKey = process.env.XHS_INTERNAL_API_KEY || "";

    let baseUrl;
    if (process.env.VERCEL_URL) {
      baseUrl = `https://${process.env.VERCEL_URL}`;
    } else if (requestHost && !requestHost.includes('localhost')) {
      baseUrl = `https://${requestHost}`;
    } else {
      baseUrl = process.env.HOST || "http://localhost:8000";
    }

    const headers = {
      'Content-Type': 'application/json',
    };
    if (internalKey) {
      headers['x-internal-api-key'] = internalKey;
    }

    const response = await fetch(`${baseUrl}/api/app/internal-logs`, {
      method: "DELETE",
      headers
    });
    apiSuccess = response.ok;
    if (!apiSuccess && response.status !== 401 && response.status !== 403) {
      console.error(`Failed to clear API logs: HTTP ${response.status}`);
    }
  } catch (e) {
    // 静默失败
  }

  return fileSuccess || apiSuccess;
}

module.exports = async function handler(req, res) {
  res.setHeader("Content-Type", "application/json");

  const requestHost = req.headers.host;

  if (req.method === "GET") {
    const url = new URL(req.url, `http://${requestHost}`);
    const limit = Math.min(100, Math.max(1, parseInt(url.searchParams.get("limit") || "50")));
    const offset = Math.max(0, parseInt(url.searchParams.get("offset") || "0"));

    const { logs, total } = await getLogs(limit, offset, requestHost);

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
    const success = await clearLogs(requestHost);
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
