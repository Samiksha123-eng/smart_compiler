/**
 * Smart Compiler Error Detective - Frontend Application Logic
 * Modular controller managing code editor, API requests, error cards,
 * interactive line jumping, automated fixes, and compiler diagnostics.
 */

// Application State
const state = {
  currentLang: 'c',
  currentAnalysis: null,
  activeFilter: 'all',
  activeTab: 'detectiveTab',
  samples: {},
  isDirty: false,
};

// DOM Element References
const elements = {
  langBtns: document.querySelectorAll('.lang-btn'),
  sampleSelect: document.getElementById('sampleSelect'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  historyToggleBtn: document.getElementById('historyToggleBtn'),
  closeHistoryBtn: document.getElementById('closeHistoryBtn'),
  clearHistoryBtn: document.getElementById('clearHistoryBtn'),
  historyDrawer: document.getElementById('historyDrawer'),
  historyList: document.getElementById('historyList'),
  historyCount: document.getElementById('historyCount'),
  historyRunsLabel: document.getElementById('historyRunsLabel'),

  codeEditor: document.getElementById('codeEditor'),
  lineGutter: document.getElementById('lineGutter'),
  editorFilename: document.getElementById('editorFilename'),
  dirtyIndicator: document.getElementById('dirtyIndicator'),
  clearEditorBtn: document.getElementById('clearEditorBtn'),
  resetCodeBtn: document.getElementById('resetCodeBtn'),
  detectErrorsBtn: document.getElementById('detectErrorsBtn'),
  currentLangTag: document.getElementById('currentLangTag'),

  cursorPos: document.getElementById('cursorPos'),
  lineCount: document.getElementById('lineCount'),
  charCount: document.getElementById('charCount'),

  tabBtns: document.querySelectorAll('.tab-btn'),
  tabContents: document.querySelectorAll('.tab-content'),

  errorCountBadge: document.getElementById('errorCountBadge'),
  tokensCountBadge: document.getElementById('tokensCountBadge'),
  symbolsCountBadge: document.getElementById('symbolsCountBadge'),

  totalErrorsCount: document.getElementById('totalErrorsCount'),
  lexicalCount: document.getElementById('lexicalCount'),
  syntaxCount: document.getElementById('syntaxCount'),
  semanticCount: document.getElementById('semanticCount'),
  warningsCount: document.getElementById('warningsCount'),

  statusSummary: document.getElementById('statusSummary'),
  statusIcon: document.getElementById('statusIcon'),
  statusText: document.getElementById('statusText'),

  filterChips: document.querySelectorAll('.filter-chip'),
  filterAllCount: document.getElementById('filterAllCount'),
  filterLexCount: document.getElementById('filterLexCount'),
  filterSynCount: document.getElementById('filterSynCount'),
  filterSemCount: document.getElementById('filterSemCount'),
  filterWarnCount: document.getElementById('filterWarnCount'),

  errorCardsList: document.getElementById('errorCardsList'),
  tokensTableBody: document.getElementById('tokensTableBody'),
  tokenFilterInput: document.getElementById('tokenFilterInput'),
  symbolsTableBody: document.getElementById('symbolsTableBody'),
};

// Language Configurations
const LANG_CONFIG = {
  c: { filename: 'main.c', tag: 'C Standard (C11)' },
  cpp: { filename: 'main.cpp', tag: 'C++ ISO Standard (C++17)' },
  java: { filename: 'Main.java', tag: 'Java Standard (JLS 17)' },
  python: { filename: 'main.py', tag: 'Python 3 Standard (PEP 8)' },
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  setupEventListeners();
  await loadSampleCodes();
  switchLanguage('c', 'buggy');
  await refreshHistory();
});

// ============================================================================
// THEME SETUP
// ============================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('compiler_detective_theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.remove('theme-dark');
    document.body.classList.add('theme-light');
  }
}

function toggleTheme() {
  if (document.body.classList.contains('theme-dark')) {
    document.body.classList.remove('theme-dark');
    document.body.classList.add('theme-light');
    localStorage.setItem('compiler_detective_theme', 'light');
  } else {
    document.body.classList.remove('theme-light');
    document.body.classList.add('theme-dark');
    localStorage.setItem('compiler_detective_theme', 'dark');
  }
}

// ============================================================================
// EVENT LISTENERS SETUP
// ============================================================================
function setupEventListeners() {
  // Theme Toggle
  elements.themeToggleBtn.addEventListener('click', toggleTheme);

  // Language buttons
  elements.langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.dataset.lang;
      if (lang !== state.currentLang) {
        switchLanguage(lang);
      }
    });
  });

  // Sample loader dropdown
  elements.sampleSelect.addEventListener('change', (e) => {
    const sampleKey = e.target.value;
    if (sampleKey && state.samples[state.currentLang]) {
      const sampleCode = state.samples[state.currentLang][sampleKey];
      if (sampleCode) {
        elements.codeEditor.value = sampleCode;
        updateGutter();
        updateEditorStats();
        runAnalysis();
      }
    }
  });

  // Editor typing and scroll sync
  elements.codeEditor.addEventListener('input', () => {
    state.isDirty = true;
    elements.dirtyIndicator.classList.add('visible');
    updateGutter();
    updateEditorStats();
  });

  elements.codeEditor.addEventListener('scroll', () => {
    elements.lineGutter.scrollTop = elements.codeEditor.scrollTop;
  });

  // Cursor movements
  elements.codeEditor.addEventListener('keyup', updateCursorStats);
  elements.codeEditor.addEventListener('click', updateCursorStats);

  // Tab key indent handling in code editor
  elements.codeEditor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = elements.codeEditor.selectionStart;
      const end = elements.codeEditor.selectionEnd;
      elements.codeEditor.value = elements.codeEditor.value.substring(0, start) + '    ' + elements.codeEditor.value.substring(end);
      elements.codeEditor.selectionStart = elements.codeEditor.selectionEnd = start + 4;
      updateGutter();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runAnalysis();
    }
  });

  // Action buttons
  elements.detectErrorsBtn.addEventListener('click', runAnalysis);

  elements.clearEditorBtn.addEventListener('click', () => {
    elements.codeEditor.value = '';
    updateGutter();
    updateEditorStats();
    elements.codeEditor.focus();
  });

  elements.resetCodeBtn.addEventListener('click', () => {
    switchLanguage(state.currentLang, 'buggy');
  });

  // Inspector Tabs
  elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.tabBtns.forEach(b => b.classList.remove('active'));
      elements.tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetContent = document.getElementById(btn.dataset.tab);
      if (targetContent) {
        targetContent.classList.add('active');
      }
      state.activeTab = btn.dataset.tab;
    });
  });

  // Filter chips
  elements.filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      elements.filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.activeFilter = chip.dataset.filter;
      renderErrorCards();
    });
  });

  // Tokens search input
  elements.tokenFilterInput.addEventListener('input', (e) => {
    filterTokensTable(e.target.value);
  });

  // History Drawer Toggle
  elements.historyToggleBtn.addEventListener('click', () => {
    elements.historyDrawer.classList.toggle('open');
  });

  elements.closeHistoryBtn.addEventListener('click', () => {
    elements.historyDrawer.classList.remove('open');
  });

  elements.clearHistoryBtn.addEventListener('click', clearHistory);
}

// ============================================================================
// LANGUAGE SWITCHING & SAMPLES
// ============================================================================
async function loadSampleCodes() {
  try {
    const res = await fetch('/api/samples');
    if (res.ok) {
      const data = await res.json();
      state.samples = data.samples || {};
    }
  } catch (err) {
    console.error('Failed to load sample programs:', err);
  }
}

function switchLanguage(lang, sampleType = 'buggy') {
  state.currentLang = lang;

  // Update UI buttons
  elements.langBtns.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  // Update Header / Footer details
  const config = LANG_CONFIG[lang] || { filename: 'main.txt', tag: lang };
  elements.editorFilename.textContent = config.filename;
  elements.currentLangTag.textContent = config.tag;

  // Load sample code
  const langSamples = state.samples[lang];
  if (langSamples && langSamples[sampleType]) {
    elements.codeEditor.value = langSamples[sampleType];
  } else {
    elements.codeEditor.value = '// Type code here...';
  }

  // Reset sample dropdown to selected
  elements.sampleSelect.value = sampleType;

  state.isDirty = false;
  elements.dirtyIndicator.classList.remove('visible');

  updateGutter();
  updateEditorStats();

  // Run analysis immediately on initial switch
  runAnalysis();
}

// ============================================================================
// GUTTER & STATS MANAGEMENT
// ============================================================================
function updateGutter(errorLines = new Map()) {
  const lines = elements.codeEditor.value.split('\n');
  const count = lines.length;
  let html = '';

  for (let i = 1; i <= count; i++) {
    const errorType = errorLines.get(i);
    let markerClass = '';
    if (errorType === 'Lexical') markerClass = 'has-lexical';
    else if (errorType === 'Syntax' || errorType === 'Semantic') markerClass = 'has-error';
    else if (errorType === 'warning') markerClass = 'has-warning';

    html += `<div class="gutter-line ${markerClass}" data-line="${i}">${i}</div>`;
  }

  elements.lineGutter.innerHTML = html;
}

function updateEditorStats() {
  const text = elements.codeEditor.value;
  const lines = text.split('\n').length;
  elements.lineCount.textContent = `${lines} lines`;
  elements.charCount.textContent = `${text.length} chars`;
}

function updateCursorStats() {
  const pos = elements.codeEditor.selectionStart;
  const text = elements.codeEditor.value.substring(0, pos);
  const lines = text.split('\n');
  const line = lines.length;
  const col = lines[lines.length - 1].length + 1;
  elements.cursorPos.textContent = `Ln ${line}, Col ${col}`;
}

// ============================================================================
// COMPILER ANALYSIS API CALL
// ============================================================================
async function runAnalysis() {
  const code = elements.codeEditor.value;
  elements.detectErrorsBtn.classList.add('loading');
  elements.detectErrorsBtn.innerHTML = `<span>Scanning...</span>`;

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: state.currentLang,
        source_code: code,
      }),
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.error || 'Server compilation error');
    }

    const result = await response.json();
    state.currentAnalysis = result;
    state.isDirty = false;
    elements.dirtyIndicator.classList.remove('visible');

    renderAnalysisResults(result);
    await refreshHistory();
  } catch (error) {
    console.error('Analysis failed:', error);
    elements.statusSummary.className = 'status-summary error';
    elements.statusIcon.textContent = '❌';
    elements.statusText.textContent = `Analysis error: ${error.message}`;
  } finally {
    elements.detectErrorsBtn.classList.remove('loading');
    elements.detectErrorsBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Detect Errors</span>
      <kbd class="shortcut-kbd">Ctrl+Enter</kbd>
    `;
  }
}

// ============================================================================
// RENDERING ANALYSIS RESULTS
// ============================================================================
function renderAnalysisResults(result) {
  // Update Metrics
  elements.totalErrorsCount.textContent = result.total_errors;
  elements.lexicalCount.textContent = result.lexical_errors_count;
  elements.syntaxCount.textContent = result.syntax_errors_count;
  elements.semanticCount.textContent = result.semantic_errors_count;
  elements.warningsCount.textContent = result.warnings_count;

  elements.errorCountBadge.textContent = result.total_errors;
  elements.tokensCountBadge.textContent = result.tokens ? result.tokens.length : 0;
  elements.symbolsCountBadge.textContent = result.symbol_table ? result.symbol_table.length : 0;

  // Filter count chips
  elements.filterAllCount.textContent = result.total_errors + result.warnings_count;
  elements.filterLexCount.textContent = result.lexical_errors_count;
  elements.filterSynCount.textContent = result.syntax_errors_count;
  elements.filterSemCount.textContent = result.semantic_errors_count;
  elements.filterWarnCount.textContent = result.warnings_count;

  // Status Summary Bar
  if (result.success && result.warnings_count === 0) {
    elements.statusSummary.className = 'status-summary success';
    elements.statusIcon.textContent = '🎉';
    elements.statusText.textContent = result.summary || 'Code compiled successfully with 0 errors!';
  } else if (result.success && result.warnings_count > 0) {
    elements.statusSummary.className = 'status-summary';
    elements.statusIcon.textContent = '⚠️';
    elements.statusText.textContent = result.summary;
  } else {
    elements.statusSummary.className = 'status-summary error';
    elements.statusIcon.textContent = '🚨';
    elements.statusText.textContent = result.summary;
  }

  // Update Gutter Markers
  const errorLines = new Map();
  (result.errors || []).forEach(err => {
    if (!errorLines.has(err.line)) {
      errorLines.set(err.line, err.phase);
    }
  });
  (result.warnings || []).forEach(w => {
    if (!errorLines.has(w.line)) {
      errorLines.set(w.line, 'warning');
    }
  });
  updateGutter(errorLines);

  // Render Sub-Views
  renderErrorCards();
  renderTokensTable(result.tokens || []);
  renderSymbolsTable(result.symbol_table || []);
}

// ============================================================================
// ERROR CARDS VIEW
// ============================================================================
function renderErrorCards() {
  if (!state.currentAnalysis) return;

  const allItems = [
    ...(state.currentAnalysis.errors || []),
    ...(state.currentAnalysis.warnings || []),
  ];

  // Apply Phase Filter
  const filtered = allItems.filter(item => {
    if (state.activeFilter === 'all') return true;
    if (state.activeFilter === 'warning') return item.severity === 'warning';
    return item.phase === state.activeFilter;
  });

  if (filtered.length === 0) {
    if (state.currentAnalysis.total_errors === 0 && state.currentAnalysis.warnings_count === 0) {
      elements.errorCardsList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">✅</div>
          <h3>Compilation Successful!</h3>
          <p>No lexical, syntax, or semantic errors were found. Your code conforms to ${state.currentAnalysis.language} grammar rules.</p>
        </div>
      `;
    } else {
      elements.errorCardsList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <h3>No ${state.activeFilter} Issues</h3>
          <p>There are no errors matching the "${state.activeFilter}" filter category.</p>
        </div>
      `;
    }
    return;
  }

  let cardsHtml = '';
  filtered.forEach(err => {
    const phaseLower = err.phase.toLowerCase();
    const isWarning = err.severity === 'warning';
    const phaseClass = isWarning ? 'phase-warning' : `phase-${phaseLower}`;
    const badgeClass = isWarning ? 'badge-warning' : `badge-${phaseLower}`;
    const badgeLabel = isWarning ? 'Warning' : `${err.phase} Phase`;

    cardsHtml += `
      <div class="error-card ${phaseClass}" id="card_${err.id}">
        <div class="card-top">
          <div class="card-badges">
            <span class="phase-badge ${badgeClass}">${badgeLabel}</span>
            <span class="card-title">${escapeHtml(err.title)}</span>
          </div>
          <button class="jump-location-chip" onclick="jumpToLine(${err.line}, ${err.column})" title="Jump to Line in Editor">
            <span>📍 Line ${err.line}, Col ${err.column}</span>
          </button>
        </div>

        <div class="card-message">
          <code>${escapeHtml(err.message)}</code>
        </div>

        <div class="card-explanation">
          <strong>💡 Why this happened:</strong> ${escapeHtml(err.explanation)}
        </div>

        <div class="card-suggestion">
          <div class="suggestion-header">
            <span class="suggestion-title">Recommended Correction</span>
            ${err.suggested_fix ? `<button class="btn-apply-fix" onclick="applyFix('${err.id}', ${err.line})">⚡ Apply Fix</button>` : ''}
          </div>
          <div class="suggestion-desc">${escapeHtml(err.suggestion)}</div>
          ${err.suggested_fix ? `<div class="suggestion-code">${escapeHtml(err.suggested_fix)}</div>` : ''}
        </div>

        <div class="card-footer">
          <span class="rule-ref">📖 ${escapeHtml(err.rule_reference)}</span>
          <span>ID: ${err.id}</span>
        </div>
      </div>
    `;
  });

  elements.errorCardsList.innerHTML = cardsHtml;
}

// ============================================================================
// INTERACTIVE CODE NAVIGATION & FIX APPLICATION
// ============================================================================
window.jumpToLine = function(lineNum, colNum = 1) {
  const textarea = elements.codeEditor;
  const lines = textarea.value.split('\n');
  if (lineNum > lines.length) return;

  // Calculate character offset to lineNum
  let offset = 0;
  for (let i = 0; i < lineNum - 1; i++) {
    offset += lines[i].length + 1; // +1 for newline
  }
  offset += Math.max(0, colNum - 1);

  textarea.focus();
  textarea.setSelectionRange(offset, offset);

  // Scroll textarea to line
  const lineHeight = 22; // matches line-height in css
  textarea.scrollTop = Math.max(0, (lineNum - 5) * lineHeight);

  // Flash line marker in gutter
  const gutterLines = elements.lineGutter.querySelectorAll('.gutter-line');
  if (gutterLines[lineNum - 1]) {
    const targetGutter = gutterLines[lineNum - 1];
    targetGutter.style.backgroundColor = 'var(--accent-primary)';
    targetGutter.style.color = '#fff';
    setTimeout(() => {
      targetGutter.style.backgroundColor = '';
      targetGutter.style.color = '';
    }, 1200);
  }
};

window.applyFix = function(errId, lineNum) {
  if (!state.currentAnalysis) return;
  const allItems = [
    ...(state.currentAnalysis.errors || []),
    ...(state.currentAnalysis.warnings || []),
  ];
  const errorItem = allItems.find(e => e.id === errId);
  if (!errorItem || !errorItem.suggested_fix) return;

  const lines = elements.codeEditor.value.split('\n');
  if (lineNum <= lines.length) {
    // If the fix is a complete replacement line
    if (errorItem.suggested_fix.includes('\n') || errorItem.suggested_fix.includes(';')) {
      lines[lineNum - 1] = errorItem.suggested_fix;
    } else {
      // Insertion / append fix
      lines[lineNum - 1] = errorItem.suggested_fix;
    }

    elements.codeEditor.value = lines.join('\n');
    updateGutter();
    updateEditorStats();
    jumpToLine(lineNum, 1);

    // Re-detect errors automatically to show immediate progress
    runAnalysis();
  }
};

// ============================================================================
// TOKENS & SYMBOL TABLES
// ============================================================================
function renderTokensTable(tokens) {
  if (!tokens || tokens.length === 0) {
    elements.tokensTableBody.innerHTML = `<tr><td colspan="5" class="table-empty">No tokens scanned.</td></tr>`;
    return;
  }

  let html = '';
  tokens.forEach(tok => {
    html += `
      <tr>
        <td>${tok.id}</td>
        <td><span class="lang-tag">${escapeHtml(tok.type)}</span></td>
        <td><code>${escapeHtml(tok.value)}</code></td>
        <td>${tok.line}</td>
        <td>${tok.column}</td>
      </tr>
    `;
  });
  elements.tokensTableBody.innerHTML = html;
}

function filterTokensTable(query) {
  const q = query.toLowerCase().trim();
  const rows = elements.tokensTableBody.querySelectorAll('tr');
  rows.forEach(row => {
    if (!q) {
      row.style.display = '';
      return;
    }
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

function renderSymbolsTable(symbols) {
  if (!symbols || symbols.length === 0) {
    elements.symbolsTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">No symbols recorded in symbol table.</td></tr>`;
    return;
  }

  let html = '';
  symbols.forEach(sym => {
    html += `
      <tr>
        <td><strong>${escapeHtml(sym.name)}</strong></td>
        <td><span class="lang-tag">${escapeHtml(sym.data_type)}</span></td>
        <td><code>${escapeHtml(sym.scope)}</code></td>
        <td>Line ${sym.line_declared}</td>
        <td>${sym.initialized ? '✅ Yes' : '❌ No'}</td>
        <td>${sym.usage_count}</td>
      </tr>
    `;
  });
  elements.symbolsTableBody.innerHTML = html;
}

// ============================================================================
// SESSION HISTORY
// ============================================================================
async function refreshHistory() {
  try {
    const res = await fetch('/api/history');
    if (res.ok) {
      const data = await res.json();
      const history = data.history || [];
      elements.historyCount.textContent = history.length;
      elements.historyRunsLabel.textContent = `${history.length} runs recorded`;

      if (history.length === 0) {
        elements.historyList.innerHTML = `<p class="history-empty">No detection runs recorded in this session yet.</p>`;
        return;
      }

      let html = '';
      history.forEach((run, idx) => {
        const badgeColor = run.total_errors === 0 ? 'var(--color-success)' : 'var(--color-semantic)';
        html += `
          <div class="history-card">
            <div class="history-top">
              <span class="history-lang">${escapeHtml(run.language)} (${run.id})</span>
              <span class="history-time">${escapeHtml(run.timestamp)}</span>
            </div>
            <div class="history-summary" style="color: ${badgeColor}; font-weight: 600;">
              ${run.total_errors === 0 ? '✅ 0 Errors' : `🚨 ${run.total_errors} Errors (${run.lexical_errors} Lex, ${run.syntax_errors} Syn, ${run.semantic_errors} Sem)`}
            </div>
            <div class="history-snippet" style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">
              ${escapeHtml(run.code_snippet)}
            </div>
          </div>
        `;
      });
      elements.historyList.innerHTML = html;
    }
  } catch (err) {
    console.error('Failed to load history:', err);
  }
}

async function clearHistory() {
  try {
    await fetch('/api/history', { method: 'DELETE' });
    await refreshHistory();
  } catch (err) {
    console.error('Failed to clear history:', err);
  }
}

// Helper: Escape HTML to avoid injection
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
