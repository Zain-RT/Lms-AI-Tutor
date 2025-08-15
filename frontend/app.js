const el = (id) => document.getElementById(id);
const state = { api: '', courseId: '', sessionId: '', sending: false };

function readState() {
  state.api = el('apiBase').value.trim().replace(/\/$/, '');
  state.courseId = el('courseId').value.trim();
  state.sessionId = el('sessionId').value.trim();
}

function setSession(id) {
  state.sessionId = id || '';
  el('sessionId').value = state.sessionId;
}

function addMessage(role, content, createdAt) {
  const log = el('chatLog');
  const wrapper = document.createElement('div');
  wrapper.className = `msg ${role}`;
  const meta = createdAt ? `<div class="meta">${role} • ${new Date(createdAt).toLocaleString()}</div>` : `<div class="meta">${role}</div>`;
  wrapper.innerHTML = `${meta}<div class="bubble">${escapeHtml(content).replace(/\n/g, '<br/>')}</div>`;
  log.appendChild(wrapper);
  log.scrollTop = log.scrollHeight;
}

function renderThread(messages) {
  const log = el('chatLog');
  log.innerHTML = '';
  (messages || []).forEach(m => addMessage(m.role, m.content, m.created_at));
}

function renderSources(sources) {
  const container = el('sources');
  if (!sources || !sources.length) { container.innerHTML = ''; return; }
  const items = sources.map((s, i) => {
    const meta = s.metadata || {}; const title = meta.title || meta.file_name || meta.source || 'Source';
    const url = meta.file_url || meta.source || '';
    const extra = [meta.file_type, meta.page, meta.slide].filter(Boolean).join(', ');
    return `<div>[${i+1}] <strong>${escapeHtml(title)}</strong>${extra ? ` (${escapeHtml(extra)})` : ''}${url ? ` — <a href="${escapeAttr(url)}" target="_blank">open</a>` : ''} <span style="color:#6b7280;">score=${Number(s.score || 0).toFixed(2)}</span></div>`;
  }).join('');
  container.innerHTML = `<div><strong>Sources</strong></div>${items}`;
}

function escapeHtml(str) { return (str || '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c])); }
function escapeAttr(str) { return (str || '').replace(/["']/g, (c) => ({'"':'&quot;','\'':'&#39;'}[c])); }

async function createSession() {
  readState();
  if (!state.api || !state.courseId) { alert('Set API base and course id'); return; }
  const url = `${state.api}/chat/session?course_id=${encodeURIComponent(state.courseId)}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) { alert('Failed to create session'); return; }
  const data = await res.json();
  setSession(data.session_id);
  el('chatLog').innerHTML = '';
  el('sources').innerHTML = '';
}

async function endSession(deleteFlag=false) {
  readState();
  if (!state.sessionId) { alert('No session id'); return; }
  const url = `${state.api}/chat/end?session_id=${encodeURIComponent(state.sessionId)}${deleteFlag ? '&delete=true' : ''}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) { const text = await res.text(); alert(`Failed to end session: ${text}`); return; }
  const data = await res.json();
  if (data.deleted) {
    setSession('');
  }
  alert(`Session ended. Summary:\n\n${data.summary || '(none)'}`);
}

async function deleteSession() {
  readState();
  if (!state.sessionId) { alert('No session id'); return; }
  const url = `${state.api}/chat/session/${encodeURIComponent(state.sessionId)}`;
  const res = await fetch(url, { method: 'DELETE' });
  if (!res.ok) { const text = await res.text(); alert(`Failed to delete: ${text}`); return; }
  setSession('');
  el('chatLog').innerHTML = '';
  el('sources').innerHTML = '';
}

async function sendMessage() {
  readState();
  if (state.sending) return;
  if (!state.api || !state.courseId) { alert('Set API base and course id'); return; }
  const text = el('message').value.trim();
  if (!text) return;
  const payload = {
    course_id: state.courseId,
    query: text,
    session_id: state.sessionId || null,
  };
  const k = Number(el('topK').value);
  if (k > 0) payload.top_k = k;
  const th = el('threshold').value;
  if (th !== '') payload.threshold = Number(th);

  try {
    state.sending = true;
    el('btnSend').disabled = true;
    const res = await fetch(`${state.api}/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const text = await res.text();
      alert(`Chat failed: ${text}`);
      return;
    }
    const data = await res.json();
    if (data.session_id && !state.sessionId) setSession(data.session_id);
    renderThread(data.messages || []);
    renderSources(data.sources || []);
    el('message').value = '';
  } finally {
    state.sending = false;
    el('btnSend').disabled = false;
  }
}

// Existing tester logic remains below; this section adds a floating chat widget
(function widget() {
  const apiInput = document.getElementById('apiBase');
  const fab = document.getElementById('chatFab');
  const widget = document.getElementById('chatWidget');
  const closeBtn = document.getElementById('chatClose');
  const input = document.getElementById('chatInput');
  const send = document.getElementById('chatSend');
  const log = document.getElementById('chatLogWidget');
  const sources = document.getElementById('chatSourcesWidget');

  let widgetSessionId = '';
  const widgetCourseId = 'math';
  let sending = false;

  function addMsg(role, content, createdAt) {
    const wrapper = document.createElement('div');
    wrapper.className = `msg ${role}`;
    const meta = createdAt ? `<div class="meta">${role} • ${new Date(createdAt).toLocaleString()}</div>` : `<div class="meta">${role}</div>`;
    wrapper.innerHTML = `${meta}<div class="bubble">${escapeHtml(content).replace(/\n/g, '<br/>')}</div>`;
    log.appendChild(wrapper);
    log.scrollTop = log.scrollHeight;
  }

  function renderWidgetThread(messages) {
    log.innerHTML = '';
    (messages || []).forEach(m => addMsg(m.role, m.content, m.created_at));
  }

  function renderWidgetSources(list) {
    if (!list || !list.length) { sources.innerHTML = ''; return; }
    const items = list.map((s, i) => {
      const meta = s.metadata || {}; const title = meta.title || meta.file_name || meta.source || 'Source';
      const url = meta.file_url || meta.source || '';
      const extra = [meta.file_type, meta.page, meta.slide].filter(Boolean).join(', ');
      return `<div>[${i+1}] <strong>${escapeHtml(title)}</strong>${extra ? ` (${escapeHtml(extra)})` : ''}${url ? ` — <a href="${escapeAttr(url)}" target="_blank">open</a>` : ''} <span style=\"color:#6b7280;\">score=${Number(s.score || 0).toFixed(2)}</span></div>`;
    }).join('');
    sources.innerHTML = `<div><strong>Sources</strong></div>${items}`;
  }

  async function ensureWidgetSession() {
    if (widgetSessionId) return widgetSessionId;
    const api = apiInput.value.trim().replace(/\/$/, '');
    const url = `${api}/chat/session?course_id=${encodeURIComponent(widgetCourseId)}`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to create session');
    const data = await res.json();
    widgetSessionId = data.session_id;
    return widgetSessionId;
  }

  async function widgetSend() {
    if (sending) return;
    const text = input.value.trim();
    if (!text) return;
    const api = apiInput.value.trim().replace(/\/$/, '');
    try {
      sending = true; send.disabled = true;
      await ensureWidgetSession();
      const payload = { course_id: widgetCourseId, query: text, session_id: widgetSessionId };
      const res = await fetch(`${api}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) { const t = await res.text(); throw new Error(t); }
      const data = await res.json();
      // Prefer returned session id if present
      if (data.session_id && !widgetSessionId) widgetSessionId = data.session_id;
      renderWidgetThread(data.messages || []);
      renderWidgetSources(data.sources || []);
      input.value = '';
    } catch (e) {
      alert('Chat failed: ' + (e.message || e));
    } finally {
      sending = false; send.disabled = false;
    }
  }

  async function endAndDeleteWidgetSession() {
    if (!widgetSessionId) return;
    const api = apiInput.value.trim().replace(/\/$/, '');
    const url = `${api}/chat/end?session_id=${encodeURIComponent(widgetSessionId)}&delete=true`;
    try { await fetch(url, { method: 'POST' }); } catch {}
    widgetSessionId = '';
  }

  fab?.addEventListener('click', async () => {
    log.innerHTML = ''; sources.innerHTML = '';
    widget.classList.remove('hidden'); widget.setAttribute('aria-hidden', 'false');
    try { await ensureWidgetSession(); } catch (e) { alert('Failed to start chat: ' + (e.message || e)); }
    input.focus();
  });

  closeBtn?.addEventListener('click', async () => {
    await endAndDeleteWidgetSession();
    widget.classList.add('hidden'); widget.setAttribute('aria-hidden', 'true');
  });

  send?.addEventListener('click', widgetSend);
  input?.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); widgetSend(); }});
})();

// Wire events
window.addEventListener('DOMContentLoaded', () => {
  el('btnCreate').addEventListener('click', createSession);
  el('btnEnd').addEventListener('click', () => endSession(false));
  el('btnEndDelete').addEventListener('click', () => endSession(true));
  el('btnDelete').addEventListener('click', deleteSession);
  el('btnSend').addEventListener('click', sendMessage);
  el('message').addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }});
}); 