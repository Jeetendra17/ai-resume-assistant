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

  /* ── theme ───────────────────────────────────────────────────────────────
     The attribute is already set by the inline script in <head>; this only
     handles switching it. Reads and writes are guarded because localStorage
     throws outright in a private window with site data blocked, and a theme
     toggle is not worth taking the rest of the page down for.               */

  const root = document.documentElement;
  const themeBtn = $('#themeToggle');
  const themeMeta = $('#themeColor');
  const THEME_COLOR = { light: '#e9edf4', dark: '#080b11' };

  /* `persist` is off for the initial sync. Writing on load would record a
     preference the visitor never expressed, which then pins them to whatever
     their OS happened to be on their first visit. */
  function applyTheme(theme, persist) {
    root.setAttribute('data-theme', theme);
    if (themeMeta) themeMeta.setAttribute('content', THEME_COLOR[theme]);
    if (themeBtn) {
      themeBtn.setAttribute(
        'aria-label',
        theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'
      );
    }
    if (persist) {
      try { localStorage.setItem('theme', theme); } catch (e) { /* private mode */ }
    }
  }

  applyTheme(root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light', false);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark', true);
    });
  }

  // Follow the OS while the visitor has not expressed a preference of their own.
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    let stored = null;
    try { stored = localStorage.getItem('theme'); } catch (err) { /* private mode */ }
    if (!stored) applyTheme(e.matches ? 'dark' : 'light', false);
  });

  /* ── section routing ─────────────────────────────────────────────────── */

  function show(id) {
    $$('.section').forEach((s) => s.classList.toggle('active', s.id === `s-${id}`));
    $$('.nav-item').forEach((b) => {
      const on = b.dataset.section === id;
      b.classList.toggle('active', on);
      if (on) b.setAttribute('aria-current', 'page');
      else b.removeAttribute('aria-current');
    });
    scroll.scrollTop = 0;
    if (history.replaceState) history.replaceState(null, '', `#${id}`);
    closeSidebar();
    if (id === 'interview') loadLab();
  }

  $$('.nav-item, .jump').forEach((btn) => {
    btn.addEventListener('click', () => show(btn.dataset.section));
  });

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

  /* The badge rendered at page load reflects which provider is *configured*, not
     which one actually responds — a rejected key still shows its provider name.
     Every answer reports who really produced it, so correct the badge from that.
     Probing on page load would be honest too, but it would spend a real API call
     on every visitor. */
  function setEngine(name, live) {
    if (!name) return;
    $$('[data-engine-name]').forEach((el) => { el.textContent = name; });
    $$('[data-engine-dot]').forEach((el) => { el.classList.toggle('off', !live); });
  }

  /* The suggested questions used to sit on the overview as a six-card grid,
     which put a third "ask something" affordance on a page that already had
     the hero card and the composer. They belong here: visible once you are
     actually in the conversation, and gone as soon as it has started. */
  function addSuggestions() {
    const rest = (window.PORTFOLIO.prompts || []).slice(3);
    if (!rest.length) return;

    const row = document.createElement('div');
    row.className = 'suggest-row';
    rest.forEach((q) => {
      const chip = document.createElement('button');
      chip.className = 'suggest';
      chip.type = 'button';
      chip.textContent = q;
      chip.addEventListener('click', () => ask(q));
      row.appendChild(chip);
    });
    messages.appendChild(row);
  }

  function openPanel() {
    if (panel.hidden) {
      panel.hidden = false;
      if (!messages.childElementCount) {
        addBubble('bot', `Hi — ask me anything about ${window.PORTFOLIO.firstName}'s experience, projects or fit for a role. I answer only from his record, cite where each answer came from, and say so when something isn't covered.`);
        addSuggestions();
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

  function addBubble(who, html, sources, { align = 'end', trace = null } = {}) {
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
    if (trace && trace.trace) bubble.appendChild(renderTrace(trace));

    row.append(avatar, bubble);
    messages.appendChild(row);
    if (align === 'start') scrollToStartOf(row);
    else messages.scrollTop = messages.scrollHeight;
    return row;
  }

  /* ── how an answer was produced ──────────────────────────────────────────
     Every reply from the interview agent carries its own trace: which graph
     nodes ran, which engines, which prompt version, how long each step took.
     Rendered collapsed, so it costs the reader nothing unless they look.       */

  const el = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  };

  const OUTCOME = {
    answered: 'Answered by the model, grounded in the corpus',
    declined_by_model: 'Declined by the model: outside his record',
    declined_before_model: 'Declined before any model call: no evidence in his record',
    verified_fallback: 'Generated answer failed verification; source quoted instead',
    extractive: 'No model available; answered from the corpus directly',
    agent_unavailable: 'Agent unavailable; answered by the resume assistant',
  };

  function renderTrace(data) {
    const box = el('details', 'trace');
    const summary = el('summary', null, 'How this was answered');
    box.appendChild(summary);

    box.appendChild(el('p', 'trace-outcome', OUTCOME[data.outcome] || data.outcome || ''));

    const path = el('ol', 'trace-path');
    (data.trace || []).forEach((step) => {
      const li = el('li', `trace-node n-${step.node}`);
      li.appendChild(el('span', 'trace-name', step.node));
      li.appendChild(el('span', 'trace-ms', `${Math.round(step.ms)} ms`));
      li.title = Object.entries(step)
        .filter(([k]) => !['node', 'ms'].includes(k))
        .map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`)
        .join('\n');
      path.appendChild(li);
    });
    box.appendChild(path);

    const e = data.engines || {};
    const facts = [
      e.graph && `graph: ${e.graph}`,
      e.chain && `chain: ${e.chain}`,
      e.retrieval && `retrieval: ${e.retrieval}`,
      data.prompt_version && `prompt: ${data.prompt_version}`,
      data.provider && `model: ${data.provider}${data.model ? ` (${data.model})` : ''}`,
      data.timing && `total ${(data.timing.total_ms / 1000).toFixed(1)} s`,
      data.timing && data.timing.graph_import_ms ? `cold start +${data.timing.graph_import_ms} ms` : null,
    ].filter(Boolean);
    const meta = el('div', 'trace-meta');
    facts.forEach((f) => meta.appendChild(el('span', 'pill', f)));
    box.appendChild(meta);
    return box;
  }

  /* ── Interview Lab ───────────────────────────────────────────────────────
     Loaded the first time the section is opened, so the homepage never pays
     for it. Every number comes from the evaluation result files.              */

  let labLoaded = false;
  const pct = (x) => (x == null ? '–' : `${Math.round(x * 100)}%`);

  function setStat(key, text) {
    const node = $(`[data-stat="${key}"]`);
    if (node) node.textContent = text;
  }

  function fillTable(table, headers, rows, highlight) {
    table.innerHTML = '';
    const thead = el('thead');
    const hr = el('tr');
    headers.forEach((h) => hr.appendChild(el('th', null, h)));
    thead.appendChild(hr);
    const tbody = el('tbody');
    rows.forEach((row) => {
      const tr = el('tr', row[0] === highlight ? 'is-live' : null);
      row.forEach((cell) => tr.appendChild(el('td', null, cell)));
      tbody.appendChild(tr);
    });
    table.append(thead, tbody);
  }

  async function loadLab() {
    if (labLoaded) return;
    labLoaded = true;
    try {
      const [stats, parts] = await Promise.all([
        fetch('/api/interview/stats').then((r) => r.json()),
        fetch('/api/interview/questions').then((r) => r.json()),
      ]);
      renderLabStats(stats);
      renderCorpus(parts);
    } catch (err) {
      labLoaded = false;
      $('#corpus').textContent = 'Could not load the corpus right now. Try again in a moment.';
    }
  }

  function renderLabStats(s) {
    const c = s.corpus || {};
    setStat('questions', c.questions ?? '–');
    setStat('pages', `${c.pages} pages at 500 words/page · ${c.parts} parts`);

    const recall = s.retrieval && s.retrieval.recall_at_3;
    if (recall && recall.live) {
      setStat('recall', pct(recall.live.combined));
      setStat('recall-detail', `keyword search alone: ${pct(recall.bm25 && recall.bm25.combined)}`);
      const order = [['bm25', 'Keyword (BM25)'], ['lsa', 'LSA (corpus-only)'], ['dense', 'Embeddings'],
        ['bm25+dense', 'Embeddings + BM25, equal'], ['live', 'Live: embeddings + BM25 at 0.25']];
      fillTable($('#retrievalTable'), ['Retriever', 'Reworded', 'Exact term', 'All'],
        order.filter(([k]) => recall[k]).map(([k, label]) => [label, pct(recall[k].reworded),
          pct(recall[k].exact_term), pct(recall[k].combined)]),
        'Live: embeddings + BM25 at 0.25');
    }

    const prompts = s.prompts || {};
    const versions = prompts.versions || {};
    const selected = prompts.selected && versions[prompts.selected];
    if (selected) {
      setStat('decision', pct(selected.decision));
      setStat('decision-detail', `prompt ${prompts.selected} · junk declined ${pct(selected.declined_junk)}`);
      fillTable($('#promptTable'), ['Version', 'Right call', 'Grounded', 'Overlap', 'Tokens'],
        Object.values(versions).sort((a, b) => a.version.localeCompare(b.version)).map((v) => [
          `${v.version} · ${v.name}`, pct(v.decision), pct(v.grounded), pct(v.overlap), String(v.prompt_tokens)]),
        `${prompts.selected} · ${selected.name}`);
      $('#promptNote').textContent = `Selected: ${prompts.selected}. Rule: ${prompts.rule}.`;
    } else {
      setStat('decision', '–');
      setStat('decision-detail', 'prompt evaluation pending');
      fillTable($('#promptTable'), ['Version', 'Status'],
        [['All versions', 'Evaluation not run yet, or not enough live answers to compare.']]);
    }

    const f = s.finetune;
    if (f) {
      setStat('finetune', String(f.train + f.val));
      setStat('finetune-detail', `${f.refusal_examples} teach refusals · not yet trained`);
      const leaks = f.contamination.val_vs_train_near_duplicates.length
        + f.contamination.retrieval_eval_questions_near_verbatim_in_train.length;
      $('#finetuneText').textContent =
        `${f.train} training and ${f.val} held-out examples, built from the corpus in chat format; ` +
        `${f.refusal_examples} of them teach the model to decline. Contamination checks against the ` +
        `held-out split and the retrieval eval found ${leaks} overlaps. A LoRA trainer for ` +
        `Qwen2.5-1.5B-Instruct is written and dry-run, but has not been trained: that needs a GPU. ` +
        `Serving a tuned model is not free either, so the live assistant takes a cheaper route to part ` +
        `of the same effect: it retrieves two examples from the same training split for every question.`;
    }
  }

  function renderCorpus(parts) {
    const root = $('#corpus');
    root.innerHTML = '';
    parts.forEach((part) => {
      const block = el('details', 'part-block');
      const summary = el('summary');
      summary.appendChild(el('span', 'part-num', `Part ${part.part}`));
      summary.appendChild(el('span', 'part-topic', part.topic));
      summary.appendChild(el('span', 'part-count', String(part.questions.length)));
      block.appendChild(summary);

      const list = el('div', 'qa-list');
      part.questions.forEach((q) => {
        const item = el('details', 'qa');
        const qs = el('summary', null, q.question);
        item.appendChild(qs);
        const body = el('div', 'qa-body', 'Loading…');
        item.appendChild(body);
        item.addEventListener('toggle', async () => {
          if (!item.open || item.dataset.loaded) return;
          item.dataset.loaded = '1';
          try {
            const a = await fetch(`/api/interview/answer/${encodeURIComponent(q.id)}`).then((r) => r.json());
            body.innerHTML = renderMarkdown(a.answer);
            const fu = el('p', 'qa-follow');
            fu.innerHTML = renderMarkdown(`**Follow-up.** ${a.follow_up}`);
            body.appendChild(fu);
            body.appendChild(el('p', 'qa-grounded', `Grounded in: ${a.grounded_in.join(', ')}`));
            const askBtn = el('button', 'btn btn-ghost btn-sm', 'Ask the assistant this');
            askBtn.type = 'button';
            askBtn.addEventListener('click', () => ask(q.question));
            body.appendChild(askBtn);
          } catch (err) {
            item.dataset.loaded = '';
            body.textContent = 'Could not load this answer.';
          }
        });
        list.appendChild(item);
      });
      block.appendChild(list);
      root.appendChild(block);
    });
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

    const suggestions = messages.querySelector('.suggest-row');
    if (suggestions) suggestions.remove();

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
      setEngine(data.provider, data.live);
      addBubble('bot', renderMarkdown(answer), data.sources, { align: 'start', trace: data });

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
      options.forEach((o) => {
        const on = o === opt;
        o.classList.toggle('selected', on);
        o.setAttribute('aria-checked', String(on));
      });
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
  /* Initial route from the URL hash. Deliberately last: routing to #interview
     calls loadLab(), which reads `let`/`const` bindings declared above -- run
     any earlier and a deep link would throw a temporal-dead-zone ReferenceError. */
  const initial = location.hash.replace('#', '');
  if (initial && $(`#s-${initial}`)) show(initial);

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
