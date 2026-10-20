const API_BASE = '';

const topicInput = document.getElementById('topic');
const studyLevel = document.getElementById('studyLevel');
const studyGoal = document.getElementById('studyGoal');
const clearInputBtn = document.getElementById('clearInput');
const generateAllBtn = document.getElementById('generateAll');
const generateNotesBtn = document.getElementById('generateNotes');
const generateQuestionsBtn = document.getElementById('generateQuestions');
const notesSection = document.getElementById('notesSection');
const questionsSection = document.getElementById('questionsSection');
const summarySection = document.getElementById('summarySection');
const flashcardsSection = document.getElementById('flashcardsSection');
const checklistSection = document.getElementById('checklistSection');
const notesContent = document.getElementById('notesContent');
const questionsContent = document.getElementById('questionsContent');
const summaryContent = document.getElementById('summaryContent');
const flashcardsContent = document.getElementById('flashcardsContent');
const checklistContent = document.getElementById('checklistContent');
const errorMessage = document.getElementById('error-message');
const errorText = errorMessage.querySelector('.error-text');
const contentGrid = document.getElementById('contentGrid');
const emptyState = document.getElementById('emptyState');
const toast = document.getElementById('toast');
const downloadNotesBtn = document.getElementById('downloadNotes');
const downloadQuestionsBtn = document.getElementById('downloadQuestions');
const recentTopics = document.getElementById('recentTopics');
const topicCount = document.getElementById('topicCount');

const RECENT_TOPICS_KEY = 'studyflow-recent-topics';

function updateRecentTopics() {
    const topics = JSON.parse(localStorage.getItem(RECENT_TOPICS_KEY) || '[]');
    topicCount.textContent = topics.length;

    if (!topics.length) {
        recentTopics.innerHTML = '<p class="empty-history">No recent topics yet. Start learning!</p>';
        return;
    }

    recentTopics.innerHTML = topics.slice(0, 6).map((item) => `
        <button class="recent-topic" data-topic="${item.replace(/"/g, '&quot;')}">
            <span>${item}</span>
            <span>Open</span>
        </button>
    `).join('');

    recentTopics.querySelectorAll('.recent-topic').forEach((button) => {
        button.addEventListener('click', () => {
            topicInput.value = button.dataset.topic;
            clearInputBtn.style.display = 'flex';
            topicInput.focus();
        });
    });
}

function addRecentTopic(topic) {
    const normalized = topic.trim();
    if (!normalized) return;

    const topics = JSON.parse(localStorage.getItem(RECENT_TOPICS_KEY) || '[]');
    const updated = [normalized, ...topics.filter((item) => item.toLowerCase() !== normalized.toLowerCase())].slice(0, 6);
    localStorage.setItem(RECENT_TOPICS_KEY, JSON.stringify(updated));
    updateRecentTopics();
}

function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = 'toast show';
    toast.style.background = type === 'error' ? 'rgba(191, 67, 67, 0.95)' : 'rgba(31, 42, 68, 0.92)';

    clearTimeout(showToast.timeoutId);
    showToast.timeoutId = setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 8000);
}

function hideError() {
    errorMessage.style.display = 'none';
}

function setLoading(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');

    if (isLoading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-flex';
        button.disabled = true;
    } else {
        btnText.style.display = 'inline-flex';
        btnLoader.style.display = 'none';
        button.disabled = false;
    }
}

function showContent() {
    emptyState.style.display = 'none';
    contentGrid.style.display = 'grid';
    contentGrid.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatNotes(text) {
    if (!text) return '';

    let formatted = text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>');

    formatted = formatted.replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');

    formatted = formatted.split('\n\n').map((paragraph) => {
        if (paragraph.trim() && !paragraph.match(/^<h|^<ul|^<li/)) {
            return `<p>${paragraph.trim()}</p>`;
        }
        return paragraph;
    }).join('\n');

    return formatted;
}

function getQuestionsText() {
    return Array.from(questionsContent.querySelectorAll('li')).map((li, index) => `${index + 1}. ${li.textContent.trim()}`).join('\n\n');
}

function downloadContent(type, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${topicInput.value.trim() || 'study-material'}-${type}-${Date.now()}.txt`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    showToast('Download started', 'success');
}

function buildOptions() {
    return {
        topic: topicInput.value.trim(),
        level: studyLevel.value,
        goal: studyGoal.value,
    };
}

async function generateNotes() {
    const { topic, level } = buildOptions();
    if (!topic) {
        showError('Please enter a topic to generate notes');
        topicInput.focus();
        return;
    }

    setLoading(generateNotesBtn, true);
    hideError();

    try {
        const response = await fetch(`${API_BASE}/api/generate-notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, level }),
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate notes');
        }

        notesContent.innerHTML = formatNotes(data.notes);
        notesSection.style.display = 'block';
        showContent();
        if (data.cached) {
            showToast('Loaded instantly from cache (0 tokens used) ⚡');
        } else {
            showToast('Notes generated successfully');
        }
    } catch (error) {
        handleRequestError(error, 'notes');
    } finally {
        setLoading(generateNotesBtn, false);
    }
}

async function generateQuestions() {
    const { topic, level } = buildOptions();
    if (!topic) {
        showError('Please enter a topic to generate questions');
        topicInput.focus();
        return;
    }

    setLoading(generateQuestionsBtn, true);
    hideError();

    try {
        const response = await fetch(`${API_BASE}/api/generate-questions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, level }),
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate questions');
        }

        questionsContent.innerHTML = '';
        data.questions.forEach((question) => {
            const item = document.createElement('li');
            const cleanQuestion = question.replace(/^\d+[\.\)]\s*/, '').replace(/^Q\d+[\.\):]\s*/i, '').trim();
            item.textContent = cleanQuestion;
            questionsContent.appendChild(item);
        });

        questionsSection.style.display = 'block';
        showContent();
        if (data.cached) {
            showToast('Loaded instantly from cache (0 tokens used) ⚡');
        } else {
            showToast('Questions generated successfully');
        }
    } catch (error) {
        handleRequestError(error, 'questions');
    } finally {
        setLoading(generateQuestionsBtn, false);
    }
}

async function generateAll() {
    const { topic, level, goal } = buildOptions();
    if (!topic) {
        showError('Please enter a topic to generate your study pack');
        topicInput.focus();
        return;
    }

    addRecentTopic(topic);
    setLoading(generateAllBtn, true);
    hideError();

    try {
        const response = await fetch(`${API_BASE}/api/generate-study-pack`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, level, goal }),
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate study pack');
        }

        if (data.summary) {
            summaryContent.innerHTML = `<p>${data.summary.replace(/\n/g, '<br><br>')}</p>`;
            summarySection.style.display = 'block';
        }

        if (data.notes) {
            notesContent.innerHTML = formatNotes(data.notes);
            notesSection.style.display = 'block';
        }

        if (data.questions && data.questions.length) {
            questionsContent.innerHTML = '';
            data.questions.forEach((question) => {
                const item = document.createElement('li');
                const cleanQuestion = question.replace(/^\d+[\.\)]\s*/, '').replace(/^Q\d+[\.\):]\s*/i, '').trim();
                item.textContent = cleanQuestion;
                questionsContent.appendChild(item);
            });
            questionsSection.style.display = 'block';
        }

        if (data.flashcards && data.flashcards.length) {
            flashcardsContent.innerHTML = '';
            data.flashcards.forEach((card) => {
                const flashcard = document.createElement('div');
                flashcard.className = 'flashcard';
                flashcard.innerHTML = `
                    <div class="flashcard-inner front">${card.front}</div>
                    <div class="flashcard-inner back">${card.back}</div>
                `;
                flashcard.addEventListener('click', () => flashcard.classList.toggle('is-flipped'));
                flashcardsContent.appendChild(flashcard);
            });
            flashcardsSection.style.display = 'block';
        }

        if (data.checklist && data.checklist.length) {
            checklistContent.innerHTML = data.checklist.map((item) => `<li>${item}</li>`).join('');
            checklistSection.style.display = 'block';
        }

        showContent();
        if (data.cached) {
            showToast('Loaded study pack from cache (0 tokens used) ⚡');
        } else {
            showToast('Study pack ready (conserved quota)');
        }
    } catch (error) {
        handleRequestError(error, 'study pack');
    } finally {
        setLoading(generateAllBtn, false);
    }
}

function handleRequestError(error, label) {
    let message = `An error occurred while generating ${label}`;
    if (error.message && error.message.includes('Failed to fetch')) {
        message = 'Cannot connect to the server. Please start the app and try again.';
    } else if (error.message) {
        message = error.message;
    }

    showError(message);
    showToast(message, 'error');
    console.error(`Error generating ${label}:`, error);
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    let text = '';

    if (elementId === 'notesContent') {
        text = element.textContent || element.innerText;
    } else if (elementId === 'questionsContent') {
        text = getQuestionsText();
    } else if (elementId === 'summaryContent') {
        text = element.textContent || element.innerText;
    }

    if (!text.trim()) {
        showToast('Nothing to copy yet', 'error');
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => showToast('Copied to clipboard'))
        .catch(() => {
            const temp = document.createElement('textarea');
            temp.value = text;
            temp.style.position = 'fixed';
            temp.style.opacity = '0';
            document.body.appendChild(temp);
            temp.select();
            try {
                document.execCommand('copy');
                showToast('Copied to clipboard');
            } catch (copyError) {
                showToast('Copy failed', 'error');
            }
            temp.remove();
        });
}

function init() {
    updateRecentTopics();

    topicInput.addEventListener('input', () => {
        clearInputBtn.style.display = topicInput.value.trim() ? 'flex' : 'none';
    });

    document.querySelectorAll('.topic-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
            topicInput.value = chip.dataset.topic;
            clearInputBtn.style.display = 'flex';
            topicInput.focus();
        });
    });

    clearInputBtn.addEventListener('click', () => {
        topicInput.value = '';
        clearInputBtn.style.display = 'none';
        topicInput.focus();
    });

    if (downloadNotesBtn && notesContent) {
        downloadNotesBtn.addEventListener('click', () => downloadContent('notes', notesContent.textContent || notesContent.innerText || ''));
    }
    if (downloadQuestionsBtn && questionsContent) {
        downloadQuestionsBtn.addEventListener('click', () => downloadContent('questions', getQuestionsText()));
    }

    if (generateAllBtn) generateAllBtn.addEventListener('click', generateAll);
    if (generateNotesBtn) generateNotesBtn.addEventListener('click', generateNotes);
    if (generateQuestionsBtn) generateQuestionsBtn.addEventListener('click', generateQuestions);

    topicInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            generateAll();
        }
    });
}

init();
