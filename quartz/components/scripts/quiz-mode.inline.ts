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
      questions.push({
        h2,
        ul,
        callout,
        allNodes: [h2, ...nodesInBetween]
      });
    }
  });

  if (questions.length === 0) return; // Not a quiz page

  let currentQuestionIndex = 0;

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
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Create Toggle if not exists
  let toggleContainer = document.getElementById('quiz-mode-toggle-container');
  if (!toggleContainer) {
    toggleContainer = document.createElement('div');
    toggleContainer.id = 'quiz-mode-toggle-container';
    toggleContainer.innerHTML = `
      <label for="quiz-mode-checkbox">Test Mode 📝</label>
      <input type="checkbox" id="quiz-mode-checkbox">
    `;
    document.body.appendChild(toggleContainer);
  }

  const checkbox = toggleContainer.querySelector('#quiz-mode-checkbox') as HTMLInputElement;
  const isTestMode = localStorage.getItem('quiz-mode') === 'true';
  checkbox.checked = isTestMode;
  if (isTestMode) {
    document.body.classList.add('quiz-mode-active');
  }

  checkbox.addEventListener('change', (e) => {
    const checked = (e.target as HTMLInputElement).checked;
    localStorage.setItem('quiz-mode', checked ? 'true' : 'false');
    if (checked) {
      document.body.classList.add('quiz-mode-active');
      showQuestion(currentQuestionIndex);
    } else {
      document.body.classList.remove('quiz-mode-active');
      showAllQuestions(); // Remove all quiz-question-hidden classes
    }
  });

  // Build each question's interactive elements (only once)
  questions.forEach((q, index) => {
    // Wrap topic in blurrable span
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

      // Build button container
      const btnContainer = document.createElement('div');
      btnContainer.className = 'quiz-btn-container';

      const prevBtn = document.createElement('button');
      prevBtn.className = 'quiz-nav-btn quiz-prev-btn';
      prevBtn.innerText = '⬅️ Prev';
      prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';

      const submitBtn = document.createElement('button');
      submitBtn.className = 'quiz-submit-btn';
      submitBtn.innerText = 'Submit';

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

        // Reveal topic
        const topicSpan = q.h2.querySelector('.quiz-topic');
        if (topicSpan) topicSpan.classList.add('revealed');

        // Reveal callout and expand it
        q.callout.classList.add('revealed');
        q.callout.classList.remove('is-collapsed');
        const content = q.callout.querySelector('.callout-content') as HTMLElement | null;
        if (content) content.style.display = '';
      });

      nextBtn.addEventListener('click', () => {
        if (currentQuestionIndex < questions.length - 1) {
          currentQuestionIndex++;
          showQuestion(currentQuestionIndex);
        }
      });

      btnContainer.appendChild(prevBtn);
      btnContainer.appendChild(submitBtn);
      btnContainer.appendChild(nextBtn);

      // Insert after the UL and register with allNodes
      q.ul.parentNode?.insertBefore(btnContainer, q.ul.nextSibling);
      q.allNodes.push(btnContainer);
    }
  });

  // Apply initial state
  if (document.body.classList.contains('quiz-mode-active')) {
    showQuestion(currentQuestionIndex);
  }
}

document.addEventListener("nav", setupQuizMode);
