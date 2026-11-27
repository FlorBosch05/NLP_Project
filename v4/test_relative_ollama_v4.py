"""Exercise relative scaling through Streamlit and the real local Ollama model."""
import json
import os
import time
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('OLLAMA_MODEL', 'qwen2.5:7b')
os.environ['HF_HUB_OFFLINE'] = '1'

# The last tuple item is (target servings, base servings, key quantity), or a
# clarification prefix. Retrieval turns are inspected but need no tool result.
SCENARIOS = [
    ('followup_and_repeat', [
        ('What are the ingredients for Guacamole?', 'retrieve', None),
        ('Double it.', 'scale', (8, 4, 'Avocado: 6')),
        ('Double it again.', 'scale', (16, 8, 'Avocado: 12')),
        ('Halve it.', 'scale', (8, 16, 'Avocado: 6')),
    ]),
    ('explicit_recipe', [('Double the Ratatouille recipe.', 'scale', (8, 4, 'Tomatoes: 1200 g'))]),
    ('half', [('Halve the Ratatouille recipe.', 'scale', (2, 4, 'Tomatoes: 300 g'))]),
    ('dutch', [('Verdubbel Ratatouille.', 'scale', (8, 4, 'Tomatoes: 1200 g'))]),
    ('no_recipe', [('Double it.', 'scale', 'Please specify exactly one recipe')]),
    ('multiple_recipes', [('Double Guacamole and Ratatouille.', 'scale', 'Please specify exactly one recipe')]),
    ('conflicting', [('Double Ratatouille to 6 servings.', 'scale', 'Please specify the recipe and the exact number')]),
    ('missing_target', [('Scale Ratatouille please.', 'scale', 'How many servings would you like?')]),
    ('absolute', [('Scale Ratatouille from 4 to 8 servings.', 'scale', (8, None, 'Tomatoes: 1200 g'))]),
    ('conversion', [('How much is 2 kilograms in grams?', 'convert', None)]),
]

def main():
    rows = []
    for name, turns in SCENARIOS:
        try:
            app = AppTest.from_file(str(ROOT / 'app_ollama_v4.py'), default_timeout=600).run()
            for question, expected_route, expected in turns:
                app.chat_input[0].set_value(question).run(timeout=600)
                messages = app.session_state['messages']
                last = messages[-1] if messages else {}
                details = last.get('details', {})
                answer = last.get('content', '')
                call = details.get('mcp_call') or {}
                problems = []
                if app.exception or app.error or last.get('role') != 'assistant': problems.append('UI failure')
                if details.get('route') != expected_route: problems.append('wrong route')
                if isinstance(expected, str):
                    if not answer.startswith(expected): problems.append('missing clarification')
                    if call: problems.append('tool called on ambiguous request')
                elif isinstance(expected, tuple):
                    target, base, ingredient = expected
                    if call.get('arguments', {}).get('to_servings') != target: problems.append('wrong target')
                    if ingredient not in answer: problems.append('wrong ingredient quantity')
                    if base is not None and f'relative to {base} servings' not in answer: problems.append('wrong or missing base')
                    if 'Source cooking steps may contain quantities' not in answer: problems.append('missing warning')
                if name == 'conversion' and '2000' not in answer: problems.append('wrong conversion')
                rows.append({'scenario': name, 'question': question, 'answer': answer, 'details': details, 'problems': problems,
                             'ui_errors': [e.value for e in app.error], 'exceptions': [e.value for e in app.exception]})
                print(name, question, 'PASS' if not problems else 'FAIL: ' + ', '.join(problems), flush=True)
                if app.exception or app.error: break
        except Exception as exc:
            rows.append({'scenario': name, 'error': f'{type(exc).__name__}: {exc}', 'problems': ['test failed']})
            print(name, type(exc).__name__, str(exc)[:250], flush=True)
    path = ROOT / 'results' / f"relative_ollama_v4_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'model': os.environ['OLLAMA_MODEL'], 'app': 'app_ollama_v4.py', 'turns': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved:', path, flush=True)
    if any(row['problems'] for row in rows): raise SystemExit(1)

if __name__ == '__main__': main()
