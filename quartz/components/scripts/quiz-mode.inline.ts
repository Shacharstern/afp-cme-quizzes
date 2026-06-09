function setupQuizMode() {
  const headers = Array.from(document.querySelectorAll('h2'));
  const questions: any[] = [];
  
  headers.forEach(h2 => {
    let nextNode = h2.nextElementSibling;
    let ul = null;
    let callout = null;
    let nodesInBetween = [];
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
    
    const checkbox = toggleContainer.querySelector('#quiz-mode-checkbox') as HTMLInputElement;
    const isTestMode = localStorage.getItem('quiz-mode') === 'true';
    checkbox.checked = isTestMode;
    if (isTestMode) document.body.classList.add('quiz-mode-active');
    
    checkbox.addEventListener('change', (e) => {
      const checked = (e.target as HTMLInputElement).checked;
      localStorage.setItem('quiz-mode', checked ? 'true' : 'false');
      if (checked) {
        document.body.classList.add('quiz-mode-active');
        showQuestion(currentQuestionIndex);
      } else {
        document.body.classList.remove('quiz-mode-active');
        // Unhide everything
        questions.forEach(q => {
          q.allNodes.forEach((n: Element) => (n as HTMLElement).style.display = '');
        });
      }
    });
  }

  // Setup Questions
  let currentQuestionIndex = 0;

  function showQuestion(index: number) {
    if (!document.body.classList.contains('quiz-mode-active')) return;
    questions.forEach((q, i) => {
      const isVisible = i === index;
      q.allNodes.forEach((n: Element) => {
        if (isVisible) {
          n.classList.remove('quiz-question-hidden');
        } else {
          n.classList.add('quiz-question-hidden');
        }
      });
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

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

      const lis = Array.from(q.ul.querySelectorAll('li'));
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
          if (li.classList.contains('ruled-out')) return; // Don't allow selecting ruled out option
          lis.forEach(l => l.classList.remove('selected'));
          li.classList.add('selected');
          selectedLi = li;
        });
      });

      const btnContainer = document.createElement('div');
      btnContainer.className = 'quiz-btn-container';

      const prevBtn = document.createElement('button');
      prevBtn.className = 'quiz-prev-btn';
      prevBtn.innerText = '⬅️ Prev';
      if (index === 0) prevBtn.style.visibility = 'hidden';
      
      const submitBtn = document.createElement('button');
      submitBtn.className = 'quiz-submit-btn';
      submitBtn.innerText = 'Submit';
      
      const nextBtn = document.createElement('button');
      nextBtn.className = 'quiz-next-btn';
      nextBtn.innerText = 'Next ➡️';
      if (index === questions.length - 1) nextBtn.style.visibility = 'hidden';

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
        submitBtn.innerText = 'Submitted';
        q.callout.classList.add('revealed');
        
        const topicSpan = q.h2.querySelector('.quiz-topic');
        if (topicSpan) topicSpan.classList.add('revealed');

        // Programmatically expand the Quartz callout
        q.callout.classList.remove('is-collapsed');
        const content = q.callout.querySelector('.callout-content');
        if (content) {
          (content as HTMLElement).style.display = 'block';
        }
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

      q.ul.parentNode?.insertBefore(btnContainer, q.ul.nextSibling);
      q.allNodes.push(btnContainer); // Ensure it gets hidden/shown with the question
    }
  });

  if (document.body.classList.contains('quiz-mode-active')) {
    showQuestion(0);
  }
}

document.addEventListener("nav", setupQuizMode);
