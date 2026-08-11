/* Portfolio shell: section routing, sidebar, and the resume assistant. */

(() => {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const sidebar = $('#sidebar');
  const scrim = $('#scrim');
  const scroll = $('#scroll');
  const panel = $('#chatPanel');
  const messages = $('#messages');
  const input = $('#input');
  const sendBtn = $('#send');
  const recentList = $('#recentList');

  /* ── section routing ─────────────────────────────────────────────────── */

  function show(id) {
    $$('.section').forEach((s) => s.classList.toggle('active', s.id === `s-${id}`));
    $$('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.section === id));
    scroll.scrollTop = 0;
    if (history.replaceState) history.replaceState(null, '', `#${id}`);
    closeSidebar();
  }

  $$('.nav-item, .jump').forEach((btn) => {
    btn.addEventListener('click', () => show(btn.dataset.section));
  });

  const initial = location.hash.replace('#', '');
  if (initial && $(`#s-${initial}`)) show(initial);

  /* ── sidebar (mobile) ────────────────────────────────────────────────── */

  const app = $('#app');
  const isDrawer = () => window.matchMedia('(max-width: 980px)').matches;

  function openSidebar() {
    sidebar.classList.add('open');
    scrim.classList.add('show');
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    scrim.classList.remove('show');
  }

  /* The same two buttons mean different things per breakpoint: below 980px the
     sidebar is an overlay drawer, above it the sidebar is part of the layout and
     has to collapse instead. Without the branch, the close button did nothing at
     all on desktop. */
  $('#sidebarOpen').addEventListener('click', () => {
    if (isDrawer()) openSidebar();
    else app.classList.remove('sidebar-collapsed');
  });

  $('#sidebarClose').addEventListener('click', () => {
    if (isDrawer()) closeSidebar();
    else app.classList.add('sidebar-collapsed');
  });

  scrim.addEventListener('click', closeSidebar);

  // Leaving the collapsed state stuck while crossing the breakpoint would hide
  // the drawer's own trigger, so clear it on the way down.
  window.matchMedia('(max-width: 980px)').addEventListener('change', (e) => {
    if (e.matches) app.classList.remove('sidebar-collapsed');
    else closeSidebar();
  });

  /* ── tiny markdown renderer ──────────────────────────────────────────────
     The assistant replies in light markdown (bold, bullets, paragraphs).
     Escaping happens first, so model output can never inject markup.        */

  function escapeHtml(text) {
    return text.replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  function renderMarkdown(raw) {
    const inline = (line) => line
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[\s(])\*([^*\n]+)\*/g, '$1<em>$2</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>');

    const out = [];
    let list = null;

    escapeHtml(raw).split('\n').forEach((line) => {
      const item = line.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)$/);
      if (item) {
        list = list || [];
        list.push(`<li>${inline(item[1])}</li>`);
        return;
      }
      if (list) { out.push(`<ul>${list.join('')}</ul>`); list = null; }
      if (line.trim()) out.push(`<p>${inline(line)}</p>`);
    });

    if (list) out.push(`<ul>${list.join('')}</ul>`);
    return out.join('') || `<p>${escapeHtml(raw)}</p>`;
  }

  /* ── chat ────────────────────────────────────────────────────────────── */

  const history_ = [];
  let busy = false;

  function openPanel() {
    if (panel.hidden) {
      panel.hidden = false;
      if (!messages.childElementCount) {
        addBubble('bot', `Hi — ask me anything about ${window.PORTFOLIO.firstName}'s experience, projects or fit for a role. I answer from his resume only.`);
      }
    }
  }

  $('#chatClose').addEventListener('click', () => { panel.hidden = true; });

  /* Scroll so a message's first line is at the top of the viewport.
     Answers can run several paragraphs; scrolling to the bottom (the natural
     chat behaviour) drops the reader at the last line and they have to scroll
     back up to find the start. Clamped so short answers don't leave a gap. */
  function scrollToStartOf(row) {
    const delta = row.getBoundingClientRect().top - messages.getBoundingClientRect().top;
    const target = messages.scrollTop + delta - 12;
    const max = messages.scrollHeight - messages.clientHeight;
    messages.scrollTop = Math.max(0, Math.min(target, max));
  }

  function addBubble(who, html, sources, { align = 'end' } = {}) {
    const row = document.createElement('div');
    row.className = `msg ${who === 'me' ? 'me' : 'bot'}`;

    const avatar = document.createElement('span');
    avatar.className = 'msg-avatar';
    avatar.textContent = who === 'me' ? 'You' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = html;

    if (sources && sources.length) {
      const wrap = document.createElement('div');
      wrap.className = 'sources';
      sources.slice(0, 4).forEach((s) => {
        const tag = document.createElement('span');
        tag.className = 'source';
        tag.textContent = s.title;
        wrap.appendChild(tag);
      });
      bubble.appendChild(wrap);
    }

    row.append(avatar, bubble);
    messages.appendChild(row);
    if (align === 'start') scrollToStartOf(row);
    else messages.scrollTop = messages.scrollHeight;
    return row;
  }

  function addTyping() {
    const row = addBubble('bot', '<div class="typing"><i></i><i></i><i></i></div>');
    row.dataset.typing = '1';
    return row;
  }

  function rememberQuestion(text) {
    if (recentList.querySelector('.recent-empty')) recentList.innerHTML = '';
    const btn = document.createElement('button');
    btn.textContent = text;
    btn.title = text;
    btn.addEventListener('click', () => ask(text));
    recentList.prepend(btn);
    while (recentList.children.length > 8) recentList.lastElementChild.remove();
  }

  async function ask(question) {
    const text = (question || '').trim();
    if (!text || busy) return;

    busy = true;
    sendBtn.disabled = true;
    input.value = '';
    openPanel();

    addBubble('me', renderMarkdown(text));
    rememberQuestion(text);
    const typing = addTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history_.slice(-8) }),
      });
      const data = await res.json();
      typing.remove();

      const answer = data.answer || 'Something went wrong. Try again in a moment.';
      addBubble('bot', renderMarkdown(answer), data.sources, { align: 'start' });

      history_.push({ role: 'user', content: text });
      history_.push({ role: 'assistant', content: answer });
    } catch (err) {
      typing.remove();
      addBubble('bot', renderMarkdown(
        "I couldn't reach the assistant. Email **jeetendrapatel1711@gmail.com** and he'll reply directly."
      ));
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  $('#composer').addEventListener('submit', (e) => {
    e.preventDefault();
    ask(input.value);
  });

  $$('.ask').forEach((card) => {
    card.addEventListener('click', () => ask(card.dataset.q));
  });

  /* hero ask-card: pick a question, then fire it */
  const options = $$('.askcard-option');
  options.forEach((opt) => {
    opt.addEventListener('click', () => {
      options.forEach((o) => o.classList.toggle('selected', o === opt));
    });
  });

  const askSelected = () => {
    const picked = $('.askcard-option.selected') || options[0];
    if (picked) ask(picked.dataset.q);
  };

  const askcardGo = $('#askcardGo');
  if (askcardGo) askcardGo.addEventListener('click', askSelected);

  const heroAsk = $('#heroAsk');
  if (heroAsk) heroAsk.addEventListener('click', () => {
    openPanel();
    input.focus();
  });

  input.addEventListener('focus', openPanel);

  /* ?ask=... opens the page with that question already answered, so a link can
     point straight at a specific answer rather than at an empty chat box. */
  const preset = new URLSearchParams(location.search).get('ask');
  if (preset) ask(preset);

  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
    }
    if (e.key === 'Escape') {
      if (!panel.hidden) panel.hidden = true;
      closeSidebar();
    }
  });
})();
