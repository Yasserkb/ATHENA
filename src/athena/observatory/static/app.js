"use strict";

const state = {
  overview: null,
  selectedId: null,
  project: null,
  graphMode: "retrieval",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat("en");

function formatTokens(value) {
  const number = Number(value || 0);
  if (number < 1000) return integer.format(number);
  return compact.format(number).replace("K", "k").replace("M", "m").replace("B", "b");
}

function formatTime(value) {
  if (!value) return "—";
  const normalized = value.includes("T") ? value : `${value.replace(" ", "T")}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.valueOf())
    ? value
    : new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(date);
}

function formatDuration(ms) {
  const value = Number(ms || 0);
  return value >= 1000 ? `${(value / 1000).toFixed(1)}s` : `${Math.round(value)}ms`;
}

async function request(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

async function loadOverview({ preserveSelection = true } = {}) {
  const refresh = $("#refresh");
  refresh.classList.add("loading");
  try {
    state.overview = await request("/api/overview");
    renderOverview();
    const ids = state.overview.projects.map((project) => project.id);
    if (!preserveSelection || !ids.includes(state.selectedId)) state.selectedId = ids[0] || null;
    renderProjectList();
    if (state.selectedId) await loadProject(state.selectedId);
    else renderNoProject();
  } catch (error) {
    toast(error.message, true);
  } finally {
    refresh.classList.remove("loading");
  }
}

function renderOverview() {
  const { summary, generated_at: generatedAt, methodology } = state.overview;
  $("#total-saved").textContent = formatTokens(summary.tokens_avoided);
  $("#total-requests").textContent = integer.format(summary.context_requests || 0);
  $("#graph-scale").textContent = formatTokens(summary.nodes);
  $("#edge-scale").textContent = `${formatTokens(summary.edges)} relationships`;
  $("#fleet-health").textContent = `${summary.healthy_projects}/${summary.projects}`;
  $("#fleet-caption").textContent = summary.projects
    ? `${summary.healthy_projects === summary.projects ? "All" : summary.projects - summary.healthy_projects} ${summary.healthy_projects === summary.projects ? "systems nominal" : "need attention"}`
    : "No projects linked";
  const rate = Number(summary.savings_rate || 0);
  $("#savings-rate").textContent = `${(rate * 100).toFixed(rate > .995 ? 2 : 1)}% efficiency`;
  $("#savings-meter").style.width = `${Math.min(100, rate * 100)}%`;
  $("#last-sync").textContent = formatTime(generatedAt);
  $("#methodology-copy").textContent = `${methodology.baseline} ${methodology.actual}`;
}

function renderProjectList() {
  const list = $("#project-list");
  const projects = state.overview.projects;
  if (!projects.length) {
    list.innerHTML = '<div class="empty-projects">No repositories yet. Use + to connect your first Athena index.</div>';
    return;
  }
  list.innerHTML = projects.map((project) => `
    <button class="project-button ${project.id === state.selectedId ? "active" : ""}"
      data-project-id="${escapeHtml(project.id)}" data-health="${escapeHtml(project.health)}">
      <i class="project-dot"></i>
      <span><b>${escapeHtml(project.name)}</b><small>${formatTokens(project.stats?.nodes)} nodes</small></span>
      <em>${project.health_score ?? 0}%</em>
    </button>`).join("");
  $$(".project-button").forEach((button) => button.addEventListener("click", () => selectProject(button.dataset.projectId)));
}

async function selectProject(projectId) {
  if (!projectId || projectId === state.selectedId) return;
  state.selectedId = projectId;
  renderProjectList();
  await loadProject(projectId);
}

async function loadProject(projectId) {
  try {
    state.project = await request(`/api/projects/${encodeURIComponent(projectId)}`);
    renderProject();
  } catch (error) {
    toast(error.message, true);
  }
}

function renderProject() {
  const project = state.project;
  const health = project.health || "unknown";
  $("#breadcrumb").textContent = project.name.toUpperCase();
  $("#project-title").textContent = project.name;
  $("#project-root").textContent = project.root;
  $("#project-health").textContent = health.toUpperCase();
  $("#project-health").dataset.health = health;
  $("#health-score").textContent = project.health_score ?? 0;
  $("#health-ring").style.setProperty("--score", `${Math.max(0, Math.min(100, project.health_score || 0)) * 3.6}deg`);
  $("#health-message").textContent = project.message || "No health message.";
  $("#index-state").textContent = project.stale ? "STALE" : project.initialized ? "CURRENT" : "EMPTY";
  $("#daemon-state").textContent = project.daemon?.state || "OFFLINE";
  $("#generation").textContent = project.index_generation ?? "—";
  $("#file-count").textContent = formatTokens(project.stats?.files);

  const savings = project.savings || {};
  const rate = Number(savings.savings_rate || 0);
  $("#selectivity").textContent = `${(rate * 100).toFixed(rate > .995 ? 2 : 1)}%`;
  drawEfficiency(project.contexts || []);
  renderActivity(project.activity || []);
  renderGraph();
}

function renderNoProject() {
  state.project = null;
  $("#breadcrumb").textContent = "ALL PROJECTS";
  $("#project-title").textContent = "Add a repository";
  $("#health-message").textContent = "Connect an Athena index to begin observing it.";
  $("#project-root").textContent = "Use the + button in the sidebar.";
  graphView.setData({ nodes: [], edges: [] });
  drawEfficiency([]);
  renderActivity([]);
}

function drawEfficiency(contexts) {
  const canvas = $("#efficiency-chart");
  const empty = $("#empty-chart");
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(rect.width * ratio));
  canvas.height = Math.max(1, Math.round(rect.height * ratio));
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  const width = rect.width;
  const height = rect.height;
  ctx.clearRect(0, 0, width, height);
  const data = [...contexts].reverse().slice(-18);
  empty.style.display = data.length ? "none" : "grid";
  if (!data.length) return;

  const pad = { left: 8, right: 8, top: 8, bottom: 22 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const max = Math.max(...data.map((point) => Number(point.baseline_tokens || 0)), 1);
  ctx.font = "8px Consolas, monospace";
  ctx.textAlign = "center";
  data.forEach((point, index) => {
    const x = pad.left + (index + .5) * (innerW / data.length);
    const baseH = Math.max(2, Number(point.baseline_tokens || 0) / max * innerH);
    const actualH = Math.max(2, Number(point.tokens_delivered || 0) / max * innerH);
    const barW = Math.max(3, innerW / data.length * .45);
    ctx.fillStyle = "rgba(95,108,125,.3)";
    ctx.fillRect(x - barW / 2, pad.top + innerH - baseH, barW, baseH);
    ctx.fillStyle = "#c8ff4d";
    ctx.fillRect(x - barW / 2, pad.top + innerH - actualH, barW, actualH);
    if (index === 0 || index === data.length - 1 || index === Math.floor(data.length / 2)) {
      ctx.fillStyle = "#66717f";
      ctx.fillText(`${index + 1}`, x, height - 5);
    }
  });
  ctx.strokeStyle = "rgba(255,255,255,.06)";
  ctx.beginPath(); ctx.moveTo(pad.left, pad.top + innerH + .5); ctx.lineTo(width - pad.right, pad.top + innerH + .5); ctx.stroke();
}

function renderActivity(activity) {
  const list = $("#activity-list");
  $("#activity-count").textContent = `${activity.length} EVENT${activity.length === 1 ? "" : "S"}`;
  if (!activity.length) {
    list.innerHTML = '<div class="activity-empty">No recorded operations for this index yet.</div>';
    return;
  }
  list.innerHTML = activity.slice(0, 12).map((item) => {
    const payload = item.payload || {};
    const context = item.operation === "context";
    const detail = context
      ? `${payload.persona || "auto"} · ${item.result_count} evidence result${item.result_count === 1 ? "" : "s"}${payload.cache_hit ? " · cache hit" : ""}`
      : `${payload.unchanged || 0} unchanged · ${payload.deleted || 0} deleted`;
    return `<div class="activity-row">
      <span>${formatTime(item.created_at)}</span>
      <b class="operation ${escapeHtml(item.operation)}"><i></i>${escapeHtml(item.operation)}</b>
      <div class="activity-detail">${escapeHtml(detail)}</div>
      <div class="activity-value">${context ? `${formatTokens(item.estimated_tokens)} tok` : `${item.result_count} files`}</div>
      <div class="activity-value">${formatDuration(item.duration_ms)}</div>
    </div>`;
  }).join("");
}

function renderGraph() {
  const project = state.project;
  const retrieval = project?.retrieval_graph || { nodes: [], edges: [] };
  const overview = project?.graph || { nodes: [], edges: [] };
  let data = state.graphMode === "retrieval" ? retrieval : overview;
  if (state.graphMode === "retrieval" && !data.nodes.length) data = { nodes: [], edges: [] };
  graphView.setData(data);
  $("#graph-empty").style.display = data.nodes.length ? "none" : "grid";
  $("#detail-nodes").textContent = integer.format(data.nodes.length);
  $("#detail-edges").textContent = integer.format(data.edges.length);
  const context = project?.latest_context;
  $("#detail-confidence").textContent = context?.confidence == null ? "—" : `${Math.round(context.confidence * 100)}%`;
  $("#detail-persona").textContent = context?.persona || "NO TRACE RECORDED";
}

class GraphView {
  constructor(canvas, tooltip) {
    this.canvas = canvas;
    this.tooltip = tooltip;
    this.ctx = canvas.getContext("2d");
    this.nodes = [];
    this.edges = [];
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;
    this.dragging = null;
    this.hovered = null;
    this.pointerDown = false;
    this.bind();
    new ResizeObserver(() => this.resize()).observe(canvas.parentElement);
  }

  bind() {
    this.canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      this.scale = Math.max(.45, Math.min(2.4, this.scale * (event.deltaY > 0 ? .9 : 1.1)));
      this.draw();
    }, { passive: false });
    this.canvas.addEventListener("pointerdown", (event) => {
      this.pointerDown = true;
      this.dragging = this.hit(event.offsetX, event.offsetY);
      if (this.dragging) this.canvas.setPointerCapture(event.pointerId);
    });
    this.canvas.addEventListener("pointermove", (event) => {
      if (this.dragging && this.pointerDown) {
        this.dragging.x = (event.offsetX - this.offsetX) / this.scale;
        this.dragging.y = (event.offsetY - this.offsetY) / this.scale;
        this.draw();
        return;
      }
      this.hovered = this.hit(event.offsetX, event.offsetY);
      if (this.hovered) {
        this.tooltip.style.display = "block";
        this.tooltip.style.left = `${Math.min(event.offsetX + 14, this.width - 285)}px`;
        this.tooltip.style.top = `${Math.max(10, event.offsetY - 24)}px`;
        this.tooltip.innerHTML = `<b>${escapeHtml(this.hovered.name)}</b><span>${escapeHtml(this.hovered.kind)} · ${escapeHtml(this.hovered.path || this.hovered.qualified_name || "graph node")}</span>`;
      } else {
        this.tooltip.style.display = "none";
      }
      this.draw();
    });
    const release = () => { this.pointerDown = false; this.dragging = null; };
    this.canvas.addEventListener("pointerup", release);
    this.canvas.addEventListener("pointercancel", release);
    this.canvas.addEventListener("pointerleave", () => { if (!this.pointerDown) this.tooltip.style.display = "none"; });
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    this.width = rect.width; this.height = rect.height; this.ratio = ratio;
    this.canvas.width = Math.max(1, Math.round(rect.width * ratio));
    this.canvas.height = Math.max(1, Math.round(rect.height * ratio));
    this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.offsetX = rect.width / 2;
    this.offsetY = rect.height / 2;
    this.draw();
  }

  setData(data) {
    const width = Math.max(300, this.canvas.getBoundingClientRect().width);
    const height = Math.max(300, this.canvas.getBoundingClientRect().height);
    this.nodes = (data.nodes || []).map((node, index) => {
      const angle = hash(node.id) / 4294967295 * Math.PI * 2;
      const radius = 45 + (index % 8) * Math.min(width, height) / 24;
      return { ...node, x: Math.cos(angle) * radius, y: Math.sin(angle) * radius, r: 4 + Math.min(7, Math.sqrt(node.degree || 1)) };
    });
    this.edges = data.edges || [];
    this.settle();
    this.scale = 1; this.hovered = null;
    this.resize();
  }

  settle() {
    const byId = new Map(this.nodes.map((node) => [node.id, node]));
    for (let iteration = 0; iteration < 90; iteration += 1) {
      for (let i = 0; i < this.nodes.length; i += 1) {
        const a = this.nodes[i];
        let fx = -a.x * .003, fy = -a.y * .003;
        for (let j = i + 1; j < this.nodes.length; j += 1) {
          const b = this.nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const distance2 = Math.max(80, dx * dx + dy * dy);
          const force = 85 / distance2;
          fx += dx * force; fy += dy * force;
          b.x -= dx * force; b.y -= dy * force;
        }
        a.x += fx; a.y += fy;
      }
      for (const edge of this.edges) {
        const a = byId.get(edge.source), b = byId.get(edge.target);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const force = (distance - 78) * .012;
        const fx = dx / distance * force, fy = dy / distance * force;
        a.x += fx; a.y += fy; b.x -= fx; b.y -= fy;
      }
    }
  }

  hit(x, y) {
    const gx = (x - this.offsetX) / this.scale, gy = (y - this.offsetY) / this.scale;
    return [...this.nodes].reverse().find((node) => Math.hypot(node.x - gx, node.y - gy) <= node.r + 6) || null;
  }

  draw() {
    if (!this.width || !this.height) return;
    const ctx = this.ctx;
    ctx.setTransform(this.ratio, 0, 0, this.ratio, 0, 0);
    ctx.clearRect(0, 0, this.width, this.height);
    ctx.save();
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.scale, this.scale);
    const byId = new Map(this.nodes.map((node) => [node.id, node]));
    for (const edge of this.edges) {
      const source = byId.get(edge.source), target = byId.get(edge.target);
      if (!source || !target) continue;
      ctx.strokeStyle = "rgba(108,126,146,.24)";
      ctx.lineWidth = .65 / this.scale;
      ctx.beginPath(); ctx.moveTo(source.x, source.y); ctx.lineTo(target.x, target.y); ctx.stroke();
    }
    for (const node of this.nodes) {
      const active = node === this.hovered;
      const color = nodeColor(node.kind);
      if (active) { ctx.shadowColor = color; ctx.shadowBlur = 18; }
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(node.x, node.y, node.r + (active ? 2 : 0), 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = active ? "#fff" : "rgba(7,9,13,.9)";
      ctx.lineWidth = 1.2 / this.scale; ctx.stroke();
      if (active || node.degree >= 8) {
        ctx.fillStyle = active ? "#f4f6f8" : "rgba(188,197,208,.62)";
        ctx.font = `${9 / this.scale}px Consolas, monospace`;
        ctx.textAlign = "center";
        ctx.fillText(shorten(node.name, 22), node.x, node.y - node.r - 7 / this.scale);
      }
    }
    ctx.restore();
  }
}

function nodeColor(kind) {
  if (["endpoint", "configuration_key", "environment_variable"].includes(kind)) return "#ffbd59";
  if (["database_table", "migration"].includes(kind)) return "#a987ff";
  if (["test", "workflow"].includes(kind)) return "#4de7ff";
  if (["class", "interface", "record", "method"].includes(kind)) return "#c8ff4d";
  if (kind === "external_symbol") return "#536070";
  return "#9ba6b4";
}

function hash(text) {
  let value = 2166136261;
  for (let i = 0; i < text.length; i += 1) value = Math.imul(value ^ text.charCodeAt(i), 16777619);
  return value >>> 0;
}

function shorten(value, length) { return value.length > length ? `${value.slice(0, length - 1)}…` : value; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]); }

let toastTimer;
function toast(message, error = false) {
  const element = $("#toast");
  element.textContent = message;
  element.className = `toast show${error ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => element.className = "toast", 3200);
}

const graphView = new GraphView($("#graph-canvas"), $("#node-tooltip"));

$("#refresh").addEventListener("click", () => loadOverview());
$("#show-methodology").addEventListener("click", () => $("#methodology-dialog").showModal());
$("#show-add-project").addEventListener("click", () => {
  $("#form-error").textContent = "";
  $("#add-project-dialog").showModal();
  $("#project-path").focus();
});
$("#add-project-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const root = $("#project-path").value.trim();
  if (!root) return;
  try {
    const project = await request("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ root }),
    });
    state.selectedId = project.id;
    $("#add-project-dialog").close();
    $("#project-path").value = "";
    toast(`${project.name} connected`);
    await loadOverview();
  } catch (error) {
    $("#form-error").textContent = error.message;
  }
});
$$('[data-graph-mode]').forEach((button) => button.addEventListener("click", () => {
  state.graphMode = button.dataset.graphMode;
  $$('[data-graph-mode]').forEach((item) => item.classList.toggle("active", item === button));
  renderGraph();
}));

window.addEventListener("resize", () => {
  drawEfficiency(state.project?.contexts || []);
});

loadOverview({ preserveSelection: false });
setInterval(() => loadOverview(), 15000);
