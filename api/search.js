const { get_request_headers_params } = require("../source/expansion/assets/xhs_xs_xsc_56.js");
require("../source/expansion/assets/xhs_xray.js");

function parseCookies(cookieString) {
  if (!cookieString) return {};
  return cookieString.split(";").reduce((acc, part) => {
    const [k, ...v] = part.trim().split("=");
    acc[k] = v.join("=");
    return acc;
  }, {});
}

function generateTraceId(len = 16) {
  const chars = "abcdef0123456789";
  let out = "";
  for (let i = 0; i < len; i += 1) {
    out += chars[Math.floor(Math.random() * chars.length)];
  }
  return out;
}

function buildFilters({
  sort_type_choice = 0,
  note_type = 0,
  note_time = 0,
  note_range = 0,
  pos_distance = 0,
}) {
  const sortType = {
    1: "time_descending",
    2: "popularity_descending",
    3: "comment_descending",
    4: "collect_descending",
  }[sort_type_choice] || "general";
  const filterNoteType = { 1: "视频笔记", 2: "普通笔记" }[note_type] || "不限";
  const filterNoteTime = { 1: "一天内", 2: "一周内", 3: "半年内" }[note_time] || "不限";
  const filterNoteRange = { 1: "已看过", 2: "未看过", 3: "已关注" }[note_range] || "不限";
  const filterPosDistance = { 1: "同城", 2: "附近" }[pos_distance] || "不限";
  return [
    { tags: [sortType], type: "sort_type" },
    { tags: [filterNoteType], type: "filter_note_type" },
    { tags: [filterNoteTime], type: "filter_note_time" },
    { tags: [filterNoteRange], type: "filter_note_range" },
    { tags: [filterPosDistance], type: "filter_pos_distance" },
  ];
}

function buildHeaders(cookie, api, data) {
  // 清理 Cookie 字符串中的换行符和其他非法字符
  const cleanedCookie = cookie ? cookie.replace(/\n/g, "").replace(/\r/g, "").trim() : "";
  const cookies = parseCookies(cleanedCookie);
  const a1 = cookies.a1 || "";
  if (!a1) {
    throw new Error("Cookie 缺少 a1");
  }
  const { xs, xt, xs_common } = get_request_headers_params(api, data, a1, "POST");
  const xray = global.traceId ? global.traceId() : "";
  return {
    "authority": "edith.xiaohongshu.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json;charset=UTF-8",
    "origin": "https://www.xiaohongshu.com",
    "pragma": "no-cache",
    "referer": "https://www.xiaohongshu.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "x-b3-traceid": generateTraceId(16),
    "x-s": xs,
    "x-t": String(xt),
    "x-s-common": xs_common,
    "x-xray-traceid": xray,
    "cookie": cleanedCookie,
  };
}

function buildNoteUrl(item) {
  const noteId = item.id || item.note_id || item.noteId;
  const xsecToken = item.xsec_token || item.xsecToken;
  if (noteId && xsecToken) {
    return `https://www.xiaohongshu.com/explore/${noteId}?xsec_token=${xsecToken}`;
  }
  if (noteId) {
    return `https://www.xiaohongshu.com/explore/${noteId}`;
  }
  return null;
}

async function readBody(req) {
  if (req.body && typeof req.body === "object") {
    return req.body;
  }
  return new Promise((resolve) => {
    let data = "";
    req.on("data", (chunk) => {
      data += chunk;
    });
    req.on("end", () => {
      try {
        resolve(JSON.parse(data || "{}"));
      } catch (e) {
        resolve({});
      }
    });
  });
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.statusCode = 405;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ message: "Method Not Allowed" }));
    return;
  }
  try {
    const body = await readBody(req);
    const {
      keyword,
      require_num = 20,
      cookie,
      sort_type_choice = 0,
      note_type = 0,
      note_time = 0,
      note_range = 0,
      pos_distance = 0,
      geo = null,
    } = body || {};
    if (!keyword) {
      res.statusCode = 400;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ message: "keyword 不能为空" }));
      return;
    }
    const api = "/api/sns/web/v1/search/notes";
    let page = 1;
    let items = [];
    while (true) {
      const data = {
        keyword,
        page,
        page_size: 20,
        search_id: generateTraceId(21),
        sort: "general",
        note_type: 0,
        ext_flags: [],
        filters: buildFilters({
          sort_type_choice,
          note_type,
          note_time,
          note_range,
          pos_distance,
        }),
        geo: geo ? JSON.stringify(geo) : "",
        image_formats: ["jpg", "webp", "avif"],
      };
      const requestCookie = cookie || process.env.XHS_COOKIE || "";
      const headers = buildHeaders(requestCookie, api, data);
      const response = await fetch(`https://edith.xiaohongshu.com${api}`, {
        method: "POST",
        headers,
        body: JSON.stringify(data),
      });
      const json = await response.json();
      if (!json.success) {
        throw new Error(json.msg || "搜索请求失败");
      }
      const pageItems = json?.data?.items || [];
      items = items.concat(pageItems);
      if (!json?.data?.has_more || items.length >= require_num) {
        break;
      }
      page += 1;
    }
    const notes = items.filter((i) => i.model_type === "note");
    const data = (notes.length ? notes : items).slice(0, require_num).map((item) => {
      const note = { ...item };
      const url = buildNoteUrl(note);
      if (url) note.note_url = url;
      return note;
    });
    res.statusCode = 200;
    res.setHeader("Content-Type", "application/json");
    res.end(
      JSON.stringify({
        message: "搜索笔记成功",
        params: body,
        data,
      })
    );
  } catch (error) {
    const message = String(error?.message || error);
    res.statusCode = message.includes("Cookie 缺少 a1") ? 400 : 500;
    res.setHeader("Content-Type", "application/json");
    res.end(
      JSON.stringify({
        message: "搜索笔记失败",
        error: message,
      })
    );
  }
};
