function setQuartzTheme(theme: 'light' | 'dark') {
  document.documentElement.setAttribute('saved-theme', theme);
  document.body?.classList.remove('theme-dark', 'theme-light');
  document.body?.classList.add(`theme-${theme}`);
  localStorage.setItem('theme', theme);
  document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
}

function setReaderMode(on: boolean) {
  const mode = on ? 'on' : 'off';
  document.documentElement.setAttribute('reader-mode', mode);
  document.dispatchEvent(new CustomEvent('readermodechange', { detail: { mode } }));
}

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"']/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanOptionText(li: HTMLElement): string {
  const ruleout = li.querySelector('.quiz-ruleout-btn');
  let text = ruleout
    ? li.innerText.replace(ruleout.textContent || '', '')
    : li.innerText;
  text = text.trim();
  text = text.replace(/^[A-Z]\s*[\.\)]\s*/i, '');
  return text.trim();
}

function getBestMatchingOption(strongText: string, options: HTMLElement[]): HTMLElement {
  const normStrong = normalizeText(strongText);
  const strongWords = normStrong.split(' ').filter(w => w.length > 0);
  
  let bestOption = options[0];
  let bestScore = -1;
  
  options.forEach(li => {
    const normOpt = normalizeText(cleanOptionText(li));
    const optWords = normOpt.split(' ').filter(w => w.length > 0);
    
    let matches = 0;
    strongWords.forEach(w => {
      if (optWords.includes(w)) {
        matches += 1;
      } else {
        if (optWords.some(ow => ow.includes(w) || w.includes(ow))) {
          matches += 0.7;
        }
      }
    });
    
    const score = matches / Math.max(strongWords.length, 1);
    if (score > bestScore) {
      bestScore = score;
      bestOption = li;
    }
  });
  
  return bestOption;
}

function findCorrectOption(q: any, lis: HTMLElement[]): HTMLElement | null {
  const strongElement = q.callout.querySelector('strong');
  if (!strongElement) return null;
  
  const strongText = strongElement.innerText.trim();
  
  const letterMatch = strongText.match(/^([A-D])\s*(?:—|-|\.)\s*/i);
  if (letterMatch) {
    const letter = letterMatch[1].toUpperCase();
    for (const li of lis) {
      const ruleout = li.querySelector('.quiz-ruleout-btn');
      const text = (ruleout ? li.innerText.replace(ruleout.textContent || '', '') : li.innerText).trim();
      if (text.toUpperCase().startsWith(letter)) {
        return li;
      }
    }
  }
  
  return getBestMatchingOption(strongText, lis);
}

function setupQuizMode() {
  const headers = Array.from(document.querySelectorAll('h2'));
  const questions: any[] = [];
  
  headers.forEach(h2 => {
    let nextNode = h2.nextElementSibling;
    let ul: Element | null = null;
    let callout: Element | null = null;
    const nodesInBetween: Element[] = [];
    while (nextNode && nextNode.tagName !== 'H2' && nextNode.tagName !== 'HR') {
      if (nextNode.tagName === 'UL' && !ul) {
        ul = nextNode;
      } else if (nextNode.classList?.contains('callout') && !callout) {
        callout = nextNode;
      }
      nodesInBetween.push(nextNode);
      nextNode = nextNode.nextElementSibling;
    }
    if (ul && callout) {
      questions.push({ h2, ul, callout, allNodes: [h2, ...nodesInBetween] });
    }
  });

  if (questions.length === 0) return;

  let currentQuestionIndex = 0;

  // Base font size (saved independently of test mode)
  const BASE_FONT_KEY = 'quiz-base-font-size';
  const TEST_FONT_BOOST = 0.3; // +3 steps of 0.1 each

  function getBaseScale(): number {
    return parseFloat(localStorage.getItem(BASE_FONT_KEY) || '1');
  }

  function applyFontScale(inTestMode: boolean) {
    const base = getBaseScale();
    const scale = inTestMode ? base + TEST_FONT_BOOST : base;
    document.documentElement.style.setProperty('--quiz-font-scale', String(scale));
  }

  function updateScoreAndProgressBar() {
    const progressContainer = document.getElementById('quiz-progress-container');
    if (!progressContainer) return;
    
    let total = questions.length;
    let submitted = 0;
    let correct = 0;
    
    questions.forEach(q => {
      if (q.ul.dataset.submitted === 'true') {
        submitted++;
        const lis = Array.from(q.ul.querySelectorAll('li')) as HTMLElement[];
        const selectedLi = lis.find(li => li.classList.contains('selected'));
        const correctLi = findCorrectOption(q, lis);
        if (selectedLi && correctLi && selectedLi === correctLi) {
          correct++;
        }
      }
    });
    
    const percentage = submitted > 0 ? Math.round((correct / submitted) * 100) : 0;
    const progressPercent = total > 0 ? Math.round((submitted / total) * 100) : 0;
    
    const textEl = document.getElementById('quiz-progress-text');
    if (textEl) {
      if (submitted === 0) {
        textEl.innerText = `Score: 0/0 (0%)`;
      } else {
        textEl.innerText = `Score: ${correct}/${submitted} (${percentage}%)`;
      }
    }
    
    const fillEl = document.getElementById('quiz-progress-bar-fill');
    if (fillEl) {
      fillEl.style.width = `${progressPercent}%`;
    }
  }

  function hideAllQuestions() {
    questions.forEach(q => {
      q.allNodes.forEach((n: Element) => n.classList.add('quiz-question-hidden'));
    });
  }

  function showAllQuestions() {
    questions.forEach(q => {
      q.allNodes.forEach((n: Element) => n.classList.remove('quiz-question-hidden'));
    });
  }

  function showQuestion(index: number) {
    hideAllQuestions();
    questions[index].allNodes.forEach((n: Element) => n.classList.remove('quiz-question-hidden'));
    // No scroll: keep the user's reading position
  }

  // Create Toggle UI if not exists
  let toggleContainer = document.getElementById('quiz-mode-toggle-container');
  if (!toggleContainer) {
    toggleContainer = document.createElement('div');
    toggleContainer.id = 'quiz-mode-toggle-container';
    toggleContainer.innerHTML = `
      <div id="quiz-font-controls">
        <button id="quiz-font-decrease" title="Decrease font size">A−</button>
        <button id="quiz-font-increase" title="Increase font size">A+</button>
      </div>
      <div id="quiz-mode-toggle">
        <label for="quiz-mode-checkbox">Test Mode 📝</label>
        <input type="checkbox" id="quiz-mode-checkbox">
      </div>
      <div id="quiz-progress-container">
        <div id="quiz-progress-text">Score: 0/0 (0%)</div>
        <div id="quiz-progress-bar-bg">
          <div id="quiz-progress-bar-fill"></div>
        </div>
      </div>
    `;
    document.body.appendChild(toggleContainer);

    const decreaseBtn = toggleContainer.querySelector('#quiz-font-decrease') as HTMLButtonElement;
    const increaseBtn = toggleContainer.querySelector('#quiz-font-increase') as HTMLButtonElement;
    const isTestModeNow = () => document.body.classList.contains('quiz-mode-active');

    decreaseBtn.addEventListener('click', () => {
      const newBase = Math.max(0.6, getBaseScale() - 0.1);
      localStorage.setItem(BASE_FONT_KEY, String(newBase));
      applyFontScale(isTestModeNow());
    });

    increaseBtn.addEventListener('click', () => {
      const newBase = Math.min(1.7, getBaseScale() + 0.1);
      localStorage.setItem(BASE_FONT_KEY, String(newBase));
      applyFontScale(isTestModeNow());
    });
  }

  // Apply initial font scale
  const isTestMode = localStorage.getItem('quiz-mode') === 'true';
  applyFontScale(isTestMode);

  const checkbox = toggleContainer.querySelector('#quiz-mode-checkbox') as HTMLInputElement;
  checkbox.checked = isTestMode;

  if (isTestMode) {
    document.body.classList.add('quiz-mode-active');
    setQuartzTheme('light');
    setReaderMode(true);
  }

  checkbox.addEventListener('change', (e) => {
    const checked = (e.target as HTMLInputElement).checked;
    localStorage.setItem('quiz-mode', checked ? 'true' : 'false');
    if (checked) {
      document.body.classList.add('quiz-mode-active');
      setQuartzTheme('light');
      setReaderMode(true);
      applyFontScale(true);
      showQuestion(currentQuestionIndex);
      updateScoreAndProgressBar();
    } else {
      document.body.classList.remove('quiz-mode-active');
      const savedTheme = (localStorage.getItem('quiz-saved-theme') as 'light' | 'dark') || 'light';
      setQuartzTheme(savedTheme);
      setReaderMode(false);
      applyFontScale(false);
      showAllQuestions();
    }
  });

  // Save user's current theme before test mode can override it
  // Only save if we're NOT already in test mode (to avoid saving 'light' that we forced)
  if (!isTestMode) {
    const currentTheme = (document.documentElement.getAttribute('saved-theme') as 'light' | 'dark') || 'light';
    localStorage.setItem('quiz-saved-theme', currentTheme);
    // Listen for theme changes by user and keep the saved copy in sync
    document.addEventListener('themechange', (e: Event) => {
      if (!document.body.classList.contains('quiz-mode-active')) {
        const theme = (e as CustomEvent).detail?.theme;
        if (theme) localStorage.setItem('quiz-saved-theme', theme);
      }
    });
  }

  // Build each question's interactive elements (only once)
  questions.forEach((q, index) => {
    if (!q.h2.dataset.quizProcessed) {
      q.h2.dataset.quizProcessed = 'true';
      const text = q.h2.innerHTML;
      const splitIdx = text.indexOf('—');
      if (splitIdx !== -1) {
        const left = text.substring(0, splitIdx + 1);
        const right = text.substring(splitIdx + 1);
        q.h2.innerHTML = `${left} <span class="quiz-topic">${right}</span>`;
      }
    }

    if (!q.ul.dataset.quizProcessed) {
      q.ul.dataset.quizProcessed = 'true';
      q.ul.classList.add('quiz-options-list');
      q.callout.classList.add('quiz-answer-callout');

      const lis = Array.from(q.ul.querySelectorAll('li')) as HTMLElement[];
      let selectedLi: HTMLElement | null = null;

      lis.forEach(li => {
        const ruleOutBtn = document.createElement('button');
        ruleOutBtn.className = 'quiz-ruleout-btn';
        ruleOutBtn.innerHTML = '❌';
        ruleOutBtn.title = 'Rule out this option';
        ruleOutBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          li.classList.toggle('ruled-out');
        });
        li.appendChild(ruleOutBtn);

        li.addEventListener('click', () => {
          if (q.ul.dataset.submitted === 'true') return;
          if (li.classList.contains('ruled-out')) return;
          lis.forEach(l => l.classList.remove('selected'));
          li.classList.add('selected');
          selectedLi = li;
        });
      });

      const btnContainer = document.createElement('div');
      btnContainer.className = 'quiz-btn-container';

      const prevBtn = document.createElement('button');
      prevBtn.className = 'quiz-nav-btn quiz-prev-btn';
      prevBtn.innerText = '⬅️ Prev';
      prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';

      const submitBtn = document.createElement('button');
      submitBtn.className = 'quiz-submit-btn';
      submitBtn.innerText = 'Submit';

      const copyBtn = document.createElement('button');
      copyBtn.className = 'quiz-copy-btn';
      copyBtn.innerText = '📋 Copy';
      copyBtn.title = 'Copy question to clipboard for AI verification';

      copyBtn.addEventListener('click', () => {
        // Title: full H2 text (topic unblurred for copying)
        const titleText = q.h2.innerText.trim();

        // Question body: all text between h2 and the UL (paragraphs)
        const bodyParts: string[] = [];
        let node = q.h2.nextElementSibling as HTMLElement | null;
        while (node && node !== q.ul) {
          const text = node.innerText?.trim();
          if (text) bodyParts.push(text);
          node = node.nextElementSibling as HTMLElement | null;
        }
        const bodyText = bodyParts.join('\n');

        // Options: li text without the ❌ button character
        const optionLines = lis.map(li => {
          const ruleout = li.querySelector('.quiz-ruleout-btn');
          const optText = ruleout
            ? li.innerText.replace(ruleout.textContent || '', '').trim()
            : li.innerText.trim();
          return optText;
        }).join('\n');

        const fullText = `${titleText}\n\n${bodyText}\n\n${optionLines}`;

        navigator.clipboard.writeText(fullText).then(() => {
          copyBtn.innerText = '✅ Copied!';
          setTimeout(() => { copyBtn.innerText = '📋 Copy'; }, 2000);
        }).catch(() => {
          copyBtn.innerText = '❌ Failed';
          setTimeout(() => { copyBtn.innerText = '📋 Copy'; }, 2000);
        });
      });

      const nextBtn = document.createElement('button');
      nextBtn.className = 'quiz-nav-btn quiz-next-btn';
      nextBtn.innerText = 'Next ➡️';
      nextBtn.style.visibility = index === questions.length - 1 ? 'hidden' : 'visible';

      prevBtn.addEventListener('click', () => {
        if (currentQuestionIndex > 0) {
          currentQuestionIndex--;
          showQuestion(currentQuestionIndex);
        }
      });

      submitBtn.addEventListener('click', () => {
        if (!selectedLi) {
          alert("Please select an answer first!");
          return;
        }
        q.ul.dataset.submitted = 'true';
        submitBtn.disabled = true;
        submitBtn.innerText = 'Submitted ✓';

        const correctLi = findCorrectOption(q, lis);
        if (correctLi) {
          correctLi.classList.add('correct-answer');
          if (selectedLi === correctLi) {
            selectedLi.classList.add('user-correct');
          } else {
            selectedLi.classList.add('user-incorrect');
          }
        } else {
          selectedLi.classList.add('user-correct');
        }

        const topicSpan = q.h2.querySelector('.quiz-topic');
        if (topicSpan) topicSpan.classList.add('revealed');

        q.callout.classList.add('revealed');
        q.callout.classList.remove('is-collapsed');
        const content = q.callout.querySelector('.callout-content') as HTMLElement | null;
        if (content) content.style.display = '';

        updateScoreAndProgressBar();
      });

      nextBtn.addEventListener('click', () => {
        if (currentQuestionIndex < questions.length - 1) {
          currentQuestionIndex++;
          showQuestion(currentQuestionIndex);
        }
      });

      btnContainer.appendChild(prevBtn);
      btnContainer.appendChild(submitBtn);
      btnContainer.appendChild(copyBtn);
      btnContainer.appendChild(nextBtn);

      q.ul.parentNode?.insertBefore(btnContainer, q.ul.nextSibling);
      q.allNodes.push(btnContainer);
    }
  });

  if (document.body.classList.contains('quiz-mode-active')) {
    showQuestion(currentQuestionIndex);
  }
  updateScoreAndProgressBar();
}

document.addEventListener("nav", setupQuizMode);
