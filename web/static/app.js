const form = document.getElementById("searchForm");
const input = document.getElementById("urlInput");
const btn = document.getElementById("searchBtn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const url = input.value.trim();
  if (!url) return;
  fetchMeta(url);
});

async function fetchMeta(url) {
  statusEl.className = "status loading";
  statusEl.innerHTML = '<span class="spinner"></span> Fetching metadata...';
  resultsEl.innerHTML = "";
  btn.disabled = true;

  try {
    const res = await fetch(`/api/metadata?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    render(data);
    statusEl.innerHTML = "";
    statusEl.className = "status";
  } catch (err) {
    statusEl.className = "status error";
    statusEl.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

/* ── Helpers ──────────────────────────────────────────────────────────── */
function fmtNum(n) {
  if (n == null) return "N/A";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toLocaleString();
}

function fmtDur(s) {
  if (s == null) return "N/A";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  const parts = [];
  if (h) parts.push(h + "h");
  if (m) parts.push(m + "m");
  parts.push(sec + "s");
  return parts.join(" ");
}

function fmtDate(d) {
  if (!d) return "N/A";
  try {
    const dt = new Date(
      Number(d.slice(0, 4)),
      Number(d.slice(4, 6)) - 1,
      Number(d.slice(6, 8))
    );
    return dt.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return d;
  }
}

function panel(color, title, bodyHtml) {
  return `
    <div class="panel">
      <div class="panel-header ${color}">
        <span class="dot"></span> ${title}
      </div>
      <div class="panel-body">${bodyHtml}</div>
    </div>`;
}

function kvGrid(pairs) {
  return (
    '<div class="kv-grid">' +
    pairs
      .map(
        ([k, v]) =>
          `<div class="key">${esc(k)}</div><div class="val">${v instanceof SafeHtml ? v.html : esc(v ?? "N/A")}</div>`
      )
      .join("") +
    "</div>"
  );
}

class SafeHtml {
  constructor(html) { this.html = html; }
}

/* ── Render ───────────────────────────────────────────────────────────── */
function render(d) {
  let html = "";

  /* Thumbnail + Title */
  if (d.thumbnail) {
    html += `<div class="title-banner">
      <img src="${d.thumbnail}" alt="thumbnail" loading="lazy" />
      <div class="title-text">
        <h2>${esc(d.title)}</h2>
        <div class="channel">${esc(d.channel)}</div>
      </div>
    </div>`;
  }

  /* Overview */
  html += panel("blue", "Overview", kvGrid([
    ["Channel", linkOr(d.channel, d.channel_url)],
    ["Upload Date", fmtDate(d.upload_date)],
    ["Duration", fmtDur(d.duration)],
    ["Category", d.category],
    ["Video ID", mono(d.id)],
  ]));

  /* Statistics */
  const watchHrs =
    d.view_count && d.duration
      ? ((d.view_count * d.duration) / 3600).toLocaleString(undefined, {
          maximumFractionDigits: 0,
        })
      : null;

  html += panel("green", "Statistics", kvGrid([
    ["Views", fmtNum(d.view_count)],
    ["Likes", fmtNum(d.like_count)],
    ["Dislikes", d.dislike_count != null ? fmtNum(d.dislike_count) : null],
    ["Comments", fmtNum(d.comment_count)],
    ["Est. Watch Hours", watchHrs],
  ]));

  /* Technical Details */
  const rows = [
    ["Resolution", d.resolution],
    ["FPS", d.fps],
    ["Format", d.format],
    ["Video Codec", d.vcodec !== "none" ? d.vcodec : null],
    ["Audio Codec", d.acodec !== "none" ? d.acodec : null],
  ];
  if (d.tbr) rows.push(["Total Bitrate", d.tbr.toFixed(0) + " kbps"]);
  if (d.vbr) rows.push(["Video Bitrate", d.vbr.toFixed(0) + " kbps"]);
  if (d.abr) rows.push(["Audio Bitrate", d.abr.toFixed(0) + " kbps"]);
  if (d.filesize)
    rows.push(["File Size", (d.filesize / (1024 * 1024)).toFixed(1) + " MB"]);
  rows.push(["Subtitles", d.subtitles?.length ? "Yes" : "No"]);
  rows.push(["Chapters", d.chapters?.length ? "Yes" : "No"]);
  if (d.is_live) rows.push(["Status", '<span style="color:var(--accent-red);font-weight:700">LIVE NOW</span>']);
  else if (d.was_live) rows.push(["Status", '<span style="color:var(--accent-yellow)">Was Live</span>']);

  html += panel("yellow", "Technical Details", kvGrid(rows));

  /* Availability */
  const avail = [
    ["Is Private", d.is_private ? "Yes" : "No"],
    ["Is Unlisted", d.was_unlisted ? "Yes" : "No"],
    ["Is Live", d.is_live ? "Yes" : "No"],
    ["Is Episode", d.is_episode ? "Yes" : "No"],
  ];
  if (d.age_limit != null) avail.unshift(["Age Restriction", d.age_limit + "+"]);

  html += panel("magenta", "Availability", kvGrid(avail));

  /* Subtitles */
  if (d.subtitles?.length || d.auto_captions_count > 0) {
    let chips = "";
    if (d.subtitles?.length) {
      chips += d.subtitles.map((s) => `<span class="chip manual">${esc(s)}</span>`).join("");
    }
    if (d.auto_captions_count > 0) {
      chips += `<span class="chip auto">+${d.auto_captions_count} auto-generated</span>`;
    }
    html += panel("cyan", "Subtitles & Captions", `<div class="chip-list">${chips}</div>`);
  }

  /* Chapters */
  if (d.chapters?.length) {
    const items = d.chapters
      .map((ch) => {
        const dur = ch.end_time != null && ch.start_time != null
          ? fmtDur(ch.end_time - ch.start_time)
          : "";
        return `<li class="chapter-item">
          <span class="chapter-time">${fmtDur(ch.start_time)}</span>
          <span>${esc(ch.title)}</span>
          <span class="chapter-dur">${dur}</span>
        </li>`;
      })
      .join("");
    html += panel(
      "blue",
      "Chapters",
      `<ul class="chapter-list">${items}</ul>`
    );
  }

  /* Tags */
  if (d.tags?.length) {
    const tags = d.tags.map((t) => `<span class="tag">#${esc(t)}</span>`).join("");
    html += panel("red", "Tags", `<div class="tag-list">${tags}</div>`);
  }

  /* Description */
  if (d.description) {
    html += panel("white", "Description", `<div class="description">${esc(d.description)}</div>`);
  }

  /* URLs */
  html += panel("blue", "URLs", kvGrid([
    ["Video URL", linkOr(d.webpage_url, d.webpage_url)],
    ["Channel URL", linkOr(d.channel_url, d.channel_url)],
    ["Thumbnail", linkOr(d.thumbnail, d.thumbnail)],
  ]));

  /* Formats */
  if (d.formats?.length > 1) {
    const header = `<tr>
      <th>ID</th><th>Ext</th><th>Resolution</th><th>FPS</th>
      <th>VCodec</th><th>ACodec</th><th class="num">Size</th><th class="num">Bitrate</th>
    </tr>`;
    const fmtRows = d.formats.map((f) => {
      const size = f.filesize
        ? (f.filesize / (1024 * 1024)).toFixed(1) + " MB"
        : "N/A";
      const tbr = f.tbr ? f.tbr.toFixed(0) + " kbps" : "N/A";
      const vc = f.vcodec === "none" ? "-" : (f.vcodec || "-");
      const ac = f.acodec === "none" ? "-" : (f.acodec || "-");
      return `<tr>
        <td>${esc(f.format_id)}</td>
        <td>${esc(f.ext)}</td>
        <td>${esc(f.resolution || (f.vcodec === "none" ? "audio only" : "N/A"))}</td>
        <td>${f.fps ?? ""}</td>
        <td>${esc(vc)}</td>
        <td>${esc(ac)}</td>
        <td class="num">${size}</td>
        <td class="num">${tbr}</td>
      </tr>`;
    }).join("");

    html += `<div class="panel">
      <div class="panel-header white"><span class="dot"></span> Available Formats</div>
      <div class="panel-body no-pad">
        <div class="table-scroll">
          <table class="data-table"><thead>${header}</thead><tbody>${fmtRows}</tbody></table>
        </div>
      </div>
    </div>`;
  }

  resultsEl.innerHTML = html;
}

/* ── Escaping ─────────────────────────────────────────────────────────── */
function esc(s) {
  if (s == null) return "";
  const el = document.createElement("span");
  el.textContent = String(s);
  return el.innerHTML;
}

function linkOr(text, url) {
  if (!url) return esc(text);
  return new SafeHtml(`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text)}</a>`);
}

function mono(text) {
  return new SafeHtml(`<span style="font-family:var(--font)">${esc(text)}</span>`);
}
