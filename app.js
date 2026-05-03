/* ===== Estado Global ===== */
let DB = null;           // dados do questions.json
let session = null;      // sessão de simulado ativa

/* ===== Inicialização ===== */
document.addEventListener('DOMContentLoaded', () => {
  loadData();
});

async function loadData() {
  try {
    const resp = await fetch('data/questions.json');
    if (!resp.ok) throw new Error('Arquivo não encontrado');
    DB = await resp.json();
    renderHomeStats();
  } catch (e) {
    // questions.json ainda não gerado → mostrar aviso
    document.getElementById('home-stats').innerHTML = `
      <div style="width:100%;background:#fff3e0;border:1px solid #ffb300;border-radius:12px;padding:16px;font-size:0.9rem;color:#5d4037;">
        <strong>⚠️ Dados não encontrados</strong><br>
        Execute <code>python parse_questions.py</code> na pasta do projeto para gerar as questões.
      </div>`;
  }
}

function renderHomeStats() {
  if (!DB) return;
  const totalExams = DB.exams.length;
  const totalQ = DB.exams.reduce((a, e) => a + e.questions.length, 0);
  const totalImg = DB.exams.reduce((a, e) => a + e.questions.filter(q => q.has_image).length, 0);
  document.getElementById('home-stats').innerHTML = `
    <div class="stat-chip">📋 ${totalExams} simulados</div>
    <div class="stat-chip">❓ ${totalQ} questões</div>
    <div class="stat-chip">🖼️ ${totalImg} questões com imagem</div>`;
}

/* ===== Navegação de telas ===== */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.getElementById('modal-exit').style.display = 'none';
  window.scrollTo(0, 0);

  if (id === 'screen-categories') renderCategories();
}

/* ===== Categorias ===== */
function renderCategories() {
  if (!DB) return;
  const grid = document.getElementById('categories-grid');

  // Agrupa provas por categoria
  const catMap = {};
  DB.exams.forEach(e => {
    if (!catMap[e.category]) catMap[e.category] = [];
    catMap[e.category].push(e);
  });

  const CATS = DB.categories;
  grid.innerHTML = Object.keys(catMap).map(cat => {
    const info = CATS[cat] || { name: cat, icon: '📋', color: '#607d8b' };
    const count = catMap[cat].length;
    return `
      <div class="category-card" style="border-left-color:${info.color}"
           onclick="showExams('${cat}')">
        <div class="cat-icon">${info.icon}</div>
        <h3>${info.name}</h3>
        <p>${count} simulado${count !== 1 ? 's' : ''} disponível${count !== 1 ? 'is' : ''}</p>
      </div>`;
  }).join('');
}

/* ===== Lista de Provas ===== */
function showExams(category) {
  if (!DB) return;
  const exams = DB.exams.filter(e => e.category === category);
  const info = DB.categories[category] || { name: category, icon: '' };

  document.getElementById('exams-title').textContent = `${info.icon} ${info.name}`;
  document.getElementById('exams-list').innerHTML = exams.map(e => {
    const qCount = e.questions.length;
    const imgCount = e.questions.filter(q => q.has_image).length;
    return `
      <div class="exam-item" onclick="startExam('${e.id}')" style="border-left-color:${info.color || '#1a73e8'}">
        <div>
          <div class="exam-name">${e.name}</div>
          <div class="exam-meta">${qCount} questões${imgCount > 0 ? ` · ${imgCount} com imagem` : ''}</div>
        </div>
        <div class="exam-arrow">›</div>
      </div>`;
  }).join('');

  showScreen('screen-exams');
}

/* ===== Iniciar Prova ===== */
function startExam(examId) {
  if (!DB) return;
  const exam = DB.exams.find(e => e.id === examId);
  if (!exam) return;

  session = {
    mode: 'exam',
    examName: exam.name,
    questions: shuffleArray([...exam.questions]),
    current: 0,
    answers: [],    // {chosen, correct, isCorrect}
    correct: 0,
    wrong: 0,
  };

  document.getElementById('q-mode-label').textContent = exam.category === 'geral' ? 'SIMULADO' : exam.name.toUpperCase().split(' ')[0];
  showScreen('screen-question');
  renderQuestion();
}

/* ===== Modo DETRAN ===== */
function startDetranMode() {
  if (!DB) return;

  // Coleta questões por categoria conforme distribuição DETRAN
  const dist = DB.detran_distribution;
  let selectedQuestions = [];

  for (const [cat, count] of Object.entries(dist)) {
    const catExams = DB.exams.filter(e => e.category === cat);
    let pool = catExams.flatMap(e => e.questions.map(q => ({ ...q, _category: cat })));
    pool = shuffleArray(pool);
    selectedQuestions = selectedQuestions.concat(pool.slice(0, count));
  }

  // Se não tiver questões suficientes de alguma categoria, completa com outras
  const target = 30;
  if (selectedQuestions.length < target) {
    const allQ = DB.exams.flatMap(e => e.questions.map(q => ({ ...q, _category: e.category })));
    const used = new Set(selectedQuestions.map(q => q.text));
    const extra = shuffleArray(allQ.filter(q => !used.has(q.text)));
    selectedQuestions = selectedQuestions.concat(extra.slice(0, target - selectedQuestions.length));
  }

  selectedQuestions = shuffleArray(selectedQuestions).slice(0, target);

  session = {
    mode: 'detran',
    examName: 'Simulado DETRAN',
    questions: selectedQuestions,
    current: 0,
    answers: [],
    correct: 0,
    wrong: 0,
    passScore: 21,
  };

  document.getElementById('q-mode-label').textContent = 'DETRAN';
  showScreen('screen-question');
  renderQuestion();
}

/* ===== Render Questão ===== */
function renderQuestion() {
  const q = session.questions[session.current];
  const total = session.questions.length;
  const num = session.current + 1;

  document.getElementById('q-counter').textContent = `${num} / ${total}`;
  document.getElementById('q-number-label').textContent = `Questão ${num}`;
  document.getElementById('q-text').textContent = q.text;
  document.getElementById('score-live').textContent = `✓ ${session.correct}  ✗ ${session.wrong}`;

  // Barra de progresso
  document.getElementById('progress-bar').style.width = ((num - 1) / total * 100) + '%';

  // Imagem
  const imgWrap = document.getElementById('q-image-wrap');
  const imgEl = document.getElementById('q-image');
  const placeholder = document.getElementById('q-image-placeholder');

  if (q.has_image) {
    imgWrap.style.display = 'block';
    if (q.image_path) {
      // Usa <picture> para suportar WebP com fallback automático
      loadQuestionImage(imgEl, placeholder, q);
    } else {
      imgEl.style.display = 'none';
      placeholder.style.display = 'flex';
      document.getElementById('q-image-code').textContent = q.image_code || '';
    }
  } else {
    imgWrap.style.display = 'none';
  }

  // Alternativas
  const altContainer = document.getElementById('alternatives');
  altContainer.innerHTML = '';
  for (const [letter, text] of Object.entries(q.alternatives)) {
    const btn = document.createElement('button');
    btn.className = 'alt-btn';
    btn.dataset.letter = letter;
    btn.innerHTML = `
      <span class="alt-letter">${letter}</span>
      <span class="alt-text">${text}</span>`;
    btn.onclick = () => selectAnswer(letter);
    altContainer.appendChild(btn);
  }

  // Feedback e botão próxima
  document.getElementById('feedback-box').style.display = 'none';
  document.getElementById('btn-next').style.display = 'none';
}

/* ===== Selecionar Resposta ===== */
function selectAnswer(chosen) {
  const q = session.questions[session.current];
  const correct = q.correct;

  if (!correct) {
    // Sem gabarito: apenas navega
    session.answers.push({ chosen, correct: null, isCorrect: null });
    showNextButton();
    return;
  }

  const isCorrect = chosen === correct;
  if (isCorrect) session.correct++;
  else session.wrong++;

  session.answers.push({ chosen, correct, isCorrect });

  // Desabilita botões
  document.querySelectorAll('.alt-btn').forEach(btn => {
    btn.disabled = true;
    const letter = btn.dataset.letter;
    if (letter === chosen && isCorrect) btn.classList.add('correct');
    else if (letter === chosen && !isCorrect) btn.classList.add('wrong');
    if (letter === correct && !isCorrect) btn.classList.add('highlight-correct');
  });

  // Feedback
  const box = document.getElementById('feedback-box');
  const icon = document.getElementById('feedback-icon');
  const msg = document.getElementById('feedback-msg');
  const correctText = document.getElementById('feedback-correct');

  box.style.display = 'flex';
  if (isCorrect) {
    box.className = 'feedback-box correct-fb';
    icon.textContent = '✅';
    msg.textContent = 'Resposta correta!';
    correctText.textContent = '';
  } else {
    box.className = 'feedback-box wrong-fb';
    icon.textContent = '❌';
    msg.textContent = 'Resposta incorreta.';
    const correctAlt = q.alternatives[correct];
    correctText.textContent = `Resposta correta: ${correct} - ${correctAlt || ''}`;
  }

  document.getElementById('score-live').textContent = `✓ ${session.correct}  ✗ ${session.wrong}`;
  showNextButton();
}

function showNextButton() {
  const btn = document.getElementById('btn-next');
  const isLast = session.current >= session.questions.length - 1;
  btn.textContent = isLast ? 'Ver Resultado →' : 'Próxima →';
  btn.style.display = 'inline-block';
}

/* ===== Próxima questão ===== */
function nextQuestion() {
  session.current++;
  if (session.current >= session.questions.length) {
    showResult();
  } else {
    renderQuestion();
    window.scrollTo(0, 0);
  }
}

/* ===== Resultado ===== */
function showResult() {
  const total = session.questions.length;
  const correct = session.correct;
  const wrong = session.wrong;
  const pct = Math.round((correct / total) * 100);
  const passed = session.mode === 'detran' ? correct >= (session.passScore || 21) : pct >= 70;

  document.getElementById('result-icon').textContent = passed ? '🏆' : '📖';
  document.getElementById('result-title').textContent = passed ? 'Aprovado!' : 'Continue praticando!';
  document.getElementById('result-subtitle').textContent =
    session.mode === 'detran'
      ? `${passed ? 'Você atingiu a pontuação mínima de 21 acertos.' : `Você precisa de ${21 - correct} acerto${21 - correct !== 1 ? 's' : ''} a mais para aprovação.`}`
      : `${session.examName} · ${pct >= 70 ? 'Ótimo desempenho!' : 'Tente novamente para melhorar.'}`;

  document.getElementById('res-correct').textContent = correct;
  document.getElementById('res-wrong').textContent = wrong;
  document.getElementById('res-total').textContent = total;
  document.getElementById('result-pct').textContent = pct + '%';

  // Círculo animado
  const circumference = 339.3;
  const circle = document.getElementById('result-circle');
  circle.style.strokeDashoffset = circumference;
  circle.className = 'circle-fg' + (passed ? '' : ' fail');
  setTimeout(() => {
    circle.style.strokeDashoffset = circumference - (circumference * pct / 100);
  }, 100);

  // Breakdown por categoria (modo DETRAN)
  const breakdownEl = document.getElementById('result-breakdown');
  if (session.mode === 'detran') {
    const catStats = {};
    session.questions.forEach((q, i) => {
      const cat = q._category || q.category || 'geral';
      if (!catStats[cat]) catStats[cat] = { correct: 0, total: 0 };
      catStats[cat].total++;
      if (session.answers[i] && session.answers[i].isCorrect) catStats[cat].correct++;
    });

    let html = '<div class="breakdown-title">Resultado por tema:</div>';
    for (const [cat, stats] of Object.entries(catStats)) {
      const catName = (DB.categories[cat] || { name: cat }).name;
      const pctCat = Math.round((stats.correct / stats.total) * 100);
      html += `
        <div class="breakdown-row">
          <span class="breakdown-label">${catName}</span>
          <div class="breakdown-bar-wrap">
            <div class="breakdown-bar" style="width:${pctCat}%;background:${pctCat >= 70 ? '#34a853' : '#ea4335'}"></div>
          </div>
          <span class="breakdown-count">${stats.correct}/${stats.total}</span>
        </div>`;
    }
    breakdownEl.innerHTML = html;
    breakdownEl.style.display = 'block';
  } else {
    breakdownEl.style.display = 'none';
  }

  showScreen('screen-result');

  // Anima barra do resultado
  setTimeout(() => {
    document.querySelectorAll('.breakdown-bar').forEach(bar => {
      const w = bar.style.width;
      bar.style.width = '0%';
      setTimeout(() => { bar.style.width = w; }, 50);
    });
  }, 200);
}

/* ===== Revisão ===== */
function reviewAnswers() {
  const list = document.getElementById('review-list');
  list.innerHTML = session.questions.map((q, i) => {
    const ans = session.answers[i] || {};
    const isCorrect = ans.isCorrect;
    const itemClass = isCorrect === true ? 'correct-item' : isCorrect === false ? 'wrong-item' : '';
    const icon = isCorrect === true ? '✓' : isCorrect === false ? '✗' : '?';
    const chosenText = ans.chosen ? `${ans.chosen} - ${q.alternatives[ans.chosen] || ''}` : 'Não respondida';
    const correctText = ans.correct ? `${ans.correct} - ${q.alternatives[ans.correct] || ''}` : 'Sem gabarito';

    return `
      <div class="review-item ${itemClass}">
        <div class="review-q-header">
          <div class="review-num">${icon}</div>
          <div class="review-q-text">${i + 1}. ${q.text}</div>
        </div>
        <div class="review-answers">
          <div class="review-answer-row">
            <span class="lbl">Sua resposta:</span>
            <span class="val ${isCorrect === true ? 'ok' : isCorrect === false ? 'err' : ''}">${chosenText}</span>
          </div>
          ${!isCorrect && ans.correct ? `
          <div class="review-answer-row">
            <span class="lbl">Resposta correta:</span>
            <span class="val ok">${correctText}</span>
          </div>` : ''}
        </div>
      </div>`;
  }).join('');

  showScreen('screen-review');
}

/* ===== Sair ===== */
function confirmExit() {
  document.getElementById('modal-exit').style.display = 'flex';
}
function closeModal() {
  document.getElementById('modal-exit').style.display = 'none';
}

/* ===== Carregamento de imagem com suporte a WebP ===== */
function loadQuestionImage(imgEl, placeholder, q) {
  const path = q.image_path;
  const codeEl = document.getElementById('q-image-code');

  // Tenta carregar o caminho informado (PNG, JPG ou WebP)
  imgEl.src = path;
  imgEl.style.display = 'block';
  placeholder.style.display = 'none';

  imgEl.onerror = () => {
    // Falhou: tenta variantes de extensão antes de exibir placeholder
    const variants = alternativeExtensions(path);
    tryNextVariant(imgEl, placeholder, variants, 0, codeEl, q.image_code || '');
  };
}

function alternativeExtensions(originalPath) {
  const EXTS = ['.webp', '.png', '.jpg', '.jpeg'];
  const base = originalPath.replace(/\.[^.]+$/, '');
  const original = originalPath.match(/\.[^.]+$/)?.[0]?.toLowerCase() || '';
  return EXTS.filter(e => e !== original).map(e => base + e);
}

function tryNextVariant(imgEl, placeholder, variants, index, codeEl, code) {
  if (index >= variants.length) {
    imgEl.style.display = 'none';
    placeholder.style.display = 'flex';
    codeEl.textContent = code;
    return;
  }
  imgEl.src = variants[index];
  imgEl.onerror = () => tryNextVariant(imgEl, placeholder, variants, index + 1, codeEl, code);
  imgEl.onload = () => {
    imgEl.style.display = 'block';
    placeholder.style.display = 'none';
  };
}

/* ===== Utilitários ===== */
function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
