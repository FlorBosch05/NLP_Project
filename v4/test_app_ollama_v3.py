"""Live local Ollama V4 UI sample; results are saved separately on every run."""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')
os.environ.setdefault('OLLAMA_MODEL', 'qwen2.5:7b')
os.environ['HF_HUB_OFFLINE'] = '1'

SCENARIOS = [
    ('ingredients_and_followup', [
        ('What are the ingredients for Guacamole?', 'retrieve'),
        ('How many servings is that recipe for?', 'retrieve'),
        ('Scale it to 8 servings.', 'scale'),
    ]),
    ('recipe_steps', [('How does the source say to prepare Spanish tortilla?', 'retrieve')]),
    ('dietary_tag', [('Is Ratatouille tagged vegan in the source?', 'retrieve')]),
    ('conversion', [('How much is 2 kilograms in grams?', 'convert')]),
    ('missing_servings', [('Scale Ratatouille please.', 'scale')]),
    ('scaled_recipe', [('Scale Ratatouille from 4 to 8 servings.', 'scale')]),
]

def main():
    rows = []
    for name, turns in SCENARIOS:
        try:
            app = AppTest.from_file(str(ROOT / 'app_ollama_v3.py'), default_timeout=600).run()
            for question, expected in turns:
                app.chat_input[0].set_value(question).run(timeout=600)
                messages = app.session_state['messages']
                last = messages[-1] if messages else {}
                details = last.get('details', {})
                problems = []
                if app.exception or app.error: problems.append('UI error or exception')
                if last.get('role') != 'assistant': problems.append('no assistant answer')
                if details.get('route') != expected: problems.append('unexpected route')
                if not last.get('content'): problems.append('empty answer')
                if name == 'missing_servings' and last.get('content') != 'How many servings would you like?': problems.append('missing or invented target')
                if name == 'scaled_recipe' and '1200 g' not in last.get('content', ''): problems.append('incorrect scaled tomatoes')
                if question == 'Scale it to 8 servings.' and 'Avocado: 6' not in last.get('content', ''): problems.append('incorrect follow-up scaling')
                if name == 'conversion' and '2000' not in last.get('content', ''): problems.append('incorrect conversion')
                rows.append({'scenario': name, 'question': question, 'expected_route': expected,
                             'answer': last.get('content'), 'details': details, 'problems': problems,
                             'ui_errors': [e.value for e in app.error], 'exceptions': [e.value for e in app.exception]})
                print(name, question, 'PASS' if not problems else 'CHECK', flush=True)
                if app.exception or app.error: break
        except Exception as exc:
            rows.append({'scenario': name, 'error': f'{type(exc).__name__}: {exc}', 'problems': ['test failed']})
            print(name, type(exc).__name__, str(exc)[:250], flush=True)
            if 'rate_limit' in str(exc).lower() or 'ratelimit' in type(exc).__name__.lower(): break
    path = ROOT / 'results' / f"app_live_ollama_v3_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'model': os.environ['OLLAMA_MODEL'], 'app': 'app_ollama_v3.py', 'turns': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved:', path, flush=True)

if __name__ == '__main__': main()
