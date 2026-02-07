const fs = require("fs");
const path = require("path");

module.exports = async function handler(req, res) {
  try {
    const htmlPath = path.join(__dirname, "../static/logs.html");
    const htmlContent = fs.readFileSync(htmlPath, "utf8");

    res.statusCode = 200;
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.end(htmlContent);
  } catch (error) {
    console.error("Failed to serve logs.html:", error);
    res.statusCode = 500;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({
      detail: "Failed to load logs.html",
      error: error.message
    }));
  }
};
