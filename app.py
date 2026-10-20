import json
import os
import re
import time

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:  # pragma: no cover - handled by dependency validation
    genai = None

# Override existing env vars so a truncated system GEMINI_API_KEY cannot
# replace the full key stored in .env.
load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

DEFAULT_MODEL = 'gemini-3-flash-preview'
MODEL_CANDIDATES = list(dict.fromkeys(
    candidate for candidate in (
        os.getenv('GEMINI_MODEL', '').strip(),
        DEFAULT_MODEL,
        'gemini-3.8-flash',
        'gemini-3.1-flash-lite',
    ) if candidate
))


def get_api_key():
    raw = (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or '').strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        raw = raw[1:-1].strip()
    return raw


def resolve_model_name():
    for candidate in MODEL_CANDIDATES:
        if candidate:
            return candidate
    return DEFAULT_MODEL


model_name = resolve_model_name()
client_error = None

try:
    if genai is None:
        raise RuntimeError('google-genai package is not installed')

    api_key = get_api_key()
    placeholder_values = {'your_gemini_api_key_here', 'your_api_key_here', 'changeme', ''}
    if api_key.lower() in {value.lower() for value in placeholder_values if value} or not api_key:
        client_error = 'Set a valid GEMINI_API_KEY in your .env file.'
        print(f'WARNING: {client_error}')
        client = None
    else:
        client = genai.Client(api_key=api_key)
        model_name = resolve_model_name()
        print(f'[OK] Gemini client ready. Using {model_name} first; other models are fallbacks.')
except Exception as exc:
    client_error = f'Failed to initialize Gemini client: {exc}'
    print(f'WARNING: {client_error}')
    client = None


# In-memory TTL cache to prevent duplicate Gemini API calls for identical requests
RESPONSE_CACHE = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache

MOCK_AI = os.getenv('MOCK_AI', '').strip().lower() in {'1', 'true', 'yes'}


def get_cached_response(cache_key):
    entry = RESPONSE_CACHE.get(cache_key)
    if entry:
        timestamp, data = entry
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return data
        del RESPONSE_CACHE[cache_key]
    return None


def set_cached_response(cache_key, data):
    # Keep cache reasonable in size (max 100 entries)
    if len(RESPONSE_CACHE) > 100:
        oldest_key = min(RESPONSE_CACHE.keys(), key=lambda k: RESPONSE_CACHE[k][0])
        del RESPONSE_CACHE[oldest_key]
    RESPONSE_CACHE[cache_key] = (time.time(), data)


def get_mock_study_pack(topic, study_level, study_goal):
    return {
        'notes': f'''# {topic} ({study_level})
## Core Overview
**{topic}** is a fundamental concept in {study_goal.lower()}.

### Key Definitions & Principles
- **Core Principle**: The central mechanism governing {topic}.
- **Primary Function**: Why {topic} is critical in this domain.
- **Key Equation/Formula or Dynamic**: Relies on systematic input, transformation, and observable output.

### Common Misconceptions
- **Myth**: Many assume {topic} operates in isolation.
- **Fact**: It functions as an interdependent element within broader systems.

### Quick Revision Summary
Remember the core 3 steps: Input -> Core Mechanism -> Practical Outcome.''',
        'questions': [
            f'What is the fundamental objective of {topic}?',
            f'Explain how {topic} behaves under varying real-world conditions.',
            f'Compare {topic} with its most closely related alternative.',
            f'What common pitfall should students avoid when analyzing {topic}?',
            f'Summarize a practical application where {topic} is indispensable.'
        ],
        'summary': f'{topic} is an essential study area for {study_level} students focusing on {study_goal}. Mastering its core principles, definitions, and standard use cases provides a solid base for both exams and practical applications.',
        'flashcards': [
            {'front': f'What is {topic}?', 'back': f'A key concept analyzed at {study_level} level for {study_goal}.'},
            {'front': f'Key mechanism of {topic}?', 'back': 'Transformation of inputs through defined principles into actionable results.'},
            {'front': f'Common misconception about {topic}?', 'back': 'Assuming static behavior instead of dynamic system interaction.'},
            {'front': f'Primary benefit of understanding {topic}?', 'back': 'Enables rapid problem solving and analytical thinking in exams.'}
        ],
        'checklist': [
            f'Memorize the core definition of {topic}',
            'Review key mechanisms and step-by-step processes',
            'Identify 2 practical real-world examples',
            'Distinguish between primary facts and common misconceptions',
            'Practice answering 5 active-recall questions'
        ]
    }


def normalize_question_list(raw_text):
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    questions = []

    for line in lines:
        cleaned = re.sub(r'^(?:[0-9]+[\.)]|Q[0-9]+[\.):])\s*', '', line, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if cleaned and len(cleaned) > 10 and cleaned not in questions:
            questions.append(cleaned)

    if len(questions) >= 5:
        return questions[:5]

    fallback = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) > 10 and stripped not in fallback:
            fallback.append(stripped)

    return fallback[:5]


def extract_json_array(raw_text):
    if raw_text is None:
        return []

    cleaned = str(raw_text).strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.replace('```json', '').replace('```', '').strip()
    if cleaned.lower().startswith('json'):
        cleaned = cleaned[4:].strip()

    start = cleaned.find('[')
    end = cleaned.rfind(']')
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    if not cleaned:
        return []

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        raise ValueError('Response was not a JSON array')
    except json.JSONDecodeError as exc:
        raise ValueError(f'Gemini returned malformed JSON: {exc}') from exc


def extract_json_object(raw_text):
    if raw_text is None:
        return {}

    cleaned = str(raw_text).strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.replace('```json', '').replace('```', '').strip()
    if cleaned.lower().startswith('json'):
        cleaned = cleaned[4:].strip()

    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    if not cleaned:
        return {}

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError('Response was not a JSON object')
    except json.JSONDecodeError as exc:
        raise ValueError(f'Gemini returned malformed JSON: {exc}') from exc


def extract_response_text(response):
    text_parts = []
    for candidate in getattr(response, 'candidates', None) or []:
        content = getattr(candidate, 'content', None)
        for part in getattr(content, 'parts', None) or []:
            if getattr(part, 'thought', False):
                continue
            if getattr(part, 'text', None):
                text_parts.append(part.text)

    if text_parts:
        return '\n'.join(text_parts).strip()

    try:
        text = getattr(response, 'text', None)
        if text:
            return str(text).strip()
    except Exception:
        pass

    return ''


def finish_reason_name(response):
    candidates = getattr(response, 'candidates', None) or []
    if not candidates:
        return ''
    reason = getattr(candidates[0], 'finish_reason', None)
    if reason is None:
        return ''
    return str(getattr(reason, 'name', None) or reason).upper()


def build_generation_config(temperature, max_output_tokens, thinking_config):
    config = {
        'temperature': temperature,
        'max_output_tokens': max_output_tokens,
    }
    if thinking_config is not None:
        config['thinking_config'] = thinking_config
    return config


def is_retryable_model_error(error_message):
    return (
        '503' in error_message or 'UNAVAILABLE' in error_message or
        '404' in error_message or 'NOT_FOUND' in error_message or
        '429' in error_message or 'TOO_MANY_REQUESTS' in error_message
    )


def generate_content(prompt, temperature=0.7, max_output_tokens=1500):
    if client is None:
        raise RuntimeError(client_error or 'Gemini API is unavailable. Check your API key and project access.')

    # Thinking tokens count against max_output_tokens. Keep thinking off or low to conserve tokens
    thinking_options = (
        {'thinking_budget': 0},
        None,
    )

    models_to_try = [model_name] + [m for m in MODEL_CANDIDATES if m != model_name]
    last_error = None

    for index, current_model in enumerate(models_to_try):
        try_next_model = False
        for thinking_config in thinking_options:
            if try_next_model:
                break
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=build_generation_config(temperature, max_output_tokens, thinking_config),
                )
            except Exception as exc:
                error_message = str(exc)
                last_error = exc
                if thinking_config is not None and (
                    'thinking' in error_message.lower() or 'thought' in error_message.lower()
                ):
                    break
                if is_retryable_model_error(error_message):
                    if index < len(models_to_try) - 1:
                        print(f'Model {current_model} failed ({error_message[:80]}); trying next model...')
                    try_next_model = True
                    break
                if index == len(models_to_try) - 1 and thinking_config is None:
                    raise
                break

            text = extract_response_text(response)
            if text:
                return text

            last_error = RuntimeError('Gemini returned an empty response.')
            break

    raise RuntimeError(str(last_error) if last_error else 'All Gemini models failed.')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok' if client is not None or MOCK_AI else 'degraded',
        'gemini_configured': client is not None,
        'mock_mode': MOCK_AI,
        'cached_items': len(RESPONSE_CACHE),
        'model': model_name,
        'error': client_error,
    })


@app.route('/api/generate-notes', methods=['POST'])
def generate_notes():
    try:
        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        study_level = (data.get('level') or 'Intermediate').strip()

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        cache_key = f"notes:{topic.lower()}:{study_level.lower()}"
        cached = get_cached_response(cache_key)
        if cached:
            return jsonify({'notes': cached, 'cached': True})

        if MOCK_AI:
            mock_pack = get_mock_study_pack(topic, study_level, 'Revision')
            set_cached_response(cache_key, mock_pack['notes'])
            return jsonify({'notes': mock_pack['notes'], 'mock': True})

        # Token-conserving, concise prompt with 600 token cap for lightning generation
        prompt = f'''Create high-yield, concise revision notes on "{topic}" for a {study_level} student.
Use clear headings (##) and short bullet points.
Include:
1. Core Definition (1-2 sentences)
2. Key Concepts & Principles (3 brief bullet points)
3. Essential Example (1-2 sentences)
4. Quick Takeaway Summary (1 sentence)
Keep language concise, punchy, and avoid unnecessary filler.'''

        notes = generate_content(prompt, temperature=0.4, max_output_tokens=600)
        set_cached_response(cache_key, notes)
        return jsonify({'notes': notes})

    except Exception as e:
        error_msg = str(e)
        if 'API_KEY_INVALID' in error_msg or '401' in error_msg or 'UNAUTHENTICATED' in error_msg or 'PERMISSION_DENIED' in error_msg:
            return jsonify({'error': 'Invalid or expired Gemini API key. Please update GEMINI_API_KEY in your .env file with a valid Google AI Studio key.'}), 401
        elif '429' in error_msg or 'quota' in error_msg.lower() or 'TOO_MANY_REQUESTS' in error_msg:
            return jsonify({'error': 'Gemini free-tier quota exceeded. Please wait a minute before requesting again.'}), 429
        elif '404' in error_msg or 'not found' in error_msg.lower():
            return jsonify({'error': 'Model not found. Please check your API key and model availability.'}), 404
        return jsonify({'error': f'Failed to generate notes: {error_msg}'}), 500


@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    try:
        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        study_level = (data.get('level') or 'Intermediate').strip()

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        cache_key = f"questions:{topic.lower()}:{study_level.lower()}"
        cached = get_cached_response(cache_key)
        if cached:
            return jsonify({'questions': cached, 'cached': True})

        if MOCK_AI:
            mock_pack = get_mock_study_pack(topic, study_level, 'Revision')
            set_cached_response(cache_key, mock_pack['questions'])
            return jsonify({'questions': mock_pack['questions'], 'mock': True})

        prompt = f'''Write exactly 5 concise, high-value practice questions for "{topic}" ({study_level} level).
Include a mix of 2 conceptual, 2 analytical, and 1 application questions.
Format strictly as numbered lines (1. to 5.). Keep each question direct and under 25 words.'''

        questions_text = generate_content(prompt, temperature=0.7, max_output_tokens=500)
        questions = normalize_question_list(questions_text)
        set_cached_response(cache_key, questions[:5])
        return jsonify({'questions': questions[:5]})

    except Exception as e:
        error_msg = str(e)
        if 'API_KEY_INVALID' in error_msg or '401' in error_msg or 'UNAUTHENTICATED' in error_msg:
            return jsonify({'error': 'Invalid or expired Gemini API key. Please update GEMINI_API_KEY in your .env file.'}), 401
        elif '429' in error_msg or 'quota' in error_msg.lower():
            return jsonify({'error': 'Gemini free-tier quota exceeded. Please wait a minute before requesting again.'}), 429
        return jsonify({'error': f'Failed to generate questions: {error_msg}'}), 500


@app.route('/api/generate-summary', methods=['POST'])
def generate_summary():
    try:
        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        study_level = (data.get('level') or 'Intermediate').strip()

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        cache_key = f"summary:{topic.lower()}:{study_level.lower()}"
        cached = get_cached_response(cache_key)
        if cached:
            return jsonify({'summary': cached, 'cached': True})

        if MOCK_AI:
            mock_pack = get_mock_study_pack(topic, study_level, 'Revision')
            set_cached_response(cache_key, mock_pack['summary'])
            return jsonify({'summary': mock_pack['summary'], 'mock': True})

        prompt = f'''Write a punchy, 3-4 sentence revision summary for "{topic}" ({study_level} level).
Focus purely on what it is, its core mechanism, and why it matters. Keep it under 80 words.'''

        summary = generate_content(prompt, temperature=0.4, max_output_tokens=300)
        set_cached_response(cache_key, summary)
        return jsonify({'summary': summary})
    except Exception as e:
        error_msg = str(e)
        return jsonify({'error': f'Failed to generate summary: {error_msg}'}), 500


@app.route('/api/generate-flashcards', methods=['POST'])
def generate_flashcards():
    try:
        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        study_level = (data.get('level') or 'Intermediate').strip()

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        cache_key = f"flashcards:{topic.lower()}:{study_level.lower()}"
        cached = get_cached_response(cache_key)
        if cached:
            return jsonify({'flashcards': cached, 'cached': True})

        if MOCK_AI:
            mock_pack = get_mock_study_pack(topic, study_level, 'Revision')
            set_cached_response(cache_key, mock_pack['flashcards'])
            return jsonify({'flashcards': mock_pack['flashcards'], 'mock': True})

        prompt = f'''Create 4 high-yield flashcards for "{topic}" ({study_level}).
Output ONLY a JSON array with format:
[
  {{"front": "Concise question or term", "back": "Clear, concise answer (under 20 words)"}}
]'''

        raw = generate_content(prompt, temperature=0.5, max_output_tokens=600)
        flashcards = extract_json_array(raw)
        set_cached_response(cache_key, flashcards)
        return jsonify({'flashcards': flashcards})
    except Exception as e:
        error_msg = str(e)
        return jsonify({'error': f'Failed to generate flashcards: {error_msg}'}), 500


@app.route('/api/generate-study-pack', methods=['POST'])
def generate_study_pack():
    try:
        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        study_level = (data.get('level') or 'Intermediate').strip()
        study_goal = (data.get('goal') or 'Revision').strip()

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        cache_key = f"pack:{topic.lower()}:{study_level.lower()}:{study_goal.lower()}"
        cached = get_cached_response(cache_key)
        if cached:
            return jsonify({**cached, 'cached': True})

        if MOCK_AI:
            mock_data = get_mock_study_pack(topic, study_level, study_goal)
            set_cached_response(cache_key, mock_data)
            return jsonify({**mock_data, 'mock': True})

        # Streamlined study pack: concise Notes, Summary, and Checklist for max speed & lowest token usage
        unified_prompt = f'''You are a high-speed study assistant. Create a high-yield study pack for "{topic}".
Student Level: {study_level}
Study Goal: {study_goal}

Return ONLY valid JSON with this exact structure:
{{
  "summary": "Clear 2-sentence summary explaining the concept and importance (under 50 words).",
  "notes": "## Key Concepts\\n- Point 1\\n- Point 2\\n- Point 3\\n\\n### Definition & Core Law\\nConcise definition\\n\\n### Key Takeaway\\n1 sentence conclusion.",
  "checklist": [
    "Step 1 to master this topic",
    "Step 2 to master this topic",
    "Step 3 to master this topic"
  ]
}}'''

        raw_output = generate_content(unified_prompt, temperature=0.4, max_output_tokens=800)
        parsed = extract_json_object(raw_output)

        notes = parsed.get('notes') or f"# {topic}\nStudy notes generated."
        summary = parsed.get('summary') or f"Summary for {topic}."
        checklist = parsed.get('checklist') or []

        result = {
            'notes': notes,
            'summary': summary,
            'checklist': checklist[:4],
        }

        # Cache the pack and sub-components
        set_cached_response(cache_key, result)
        set_cached_response(f"notes:{topic.lower()}:{study_level.lower()}", notes)
        set_cached_response(f"summary:{topic.lower()}:{study_level.lower()}", summary)

        return jsonify(result)

    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg or 'quota' in error_msg.lower() or 'TOO_MANY_REQUESTS' in error_msg:
            return jsonify({'error': 'Gemini free-tier quota limit reached. Please wait a minute or try a cached topic.'}), 429
        return jsonify({'error': f'Failed to generate study pack: {error_msg}'}), 500


@app.route('/api/generate-all', methods=['POST'])
def generate_all():
    return generate_study_pack()


if __name__ == '__main__':
    print('\n' + '=' * 50)
    print('Starting AI Study Helper Server...')
    print('=' * 50)
    print('Server will be available at: http://localhost:5000')
    if client is None:
        print('WARNING: Gemini client not initialized. Please check your .env file.')
        print('Make sure GEMINI_API_KEY is set in your .env file with a valid Google AI Studio key.')
    else:
        print(f'[OK] Gemini API configured successfully using {model_name}')
    print('=' * 50 + '\n')
    try:
        app.run(debug=True, port=5000, host='127.0.0.1')
    except Exception as e:
        print(f'ERROR: Failed to start server: {e}')
        import traceback
        traceback.print_exc()
