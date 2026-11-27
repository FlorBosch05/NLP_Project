"""Generate a separate local-agent revision for relative serving requests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
agent = (ROOT / 'chef/agent_ollama_v3.py').read_text(encoding='utf-8')
agent = agent.replace('    timings: dict\n', '    timings: dict\n    previous_scale: dict\n    relative_base: float\n')
marker = 'def create_graph(index, model=None, top_k=5):'
helper = '''def relative_factor(question):
    """Recognize a small explicit set; ambiguous requests need clarification."""
    text = question.casefold()
    double = bool(re.search(r"\\b(?:double|doubled|doubling|twice|verdubbel|verdubbelen|dubbel)\\b", text))
    half = bool(re.search(r"\\b(?:halve|halved|halving|half|halveer|halveren|helft)\\b", text))
    if not (double or half):
        return None
    if double and half or re.search(r"\\b(?:not|don't|dont|do not|never|niet|geen)\\b", text):
        return 0
    if re.search(r"(?<![\\w.])\\d+(?:[.,]\\d+)?", text):
        return 0  # Multiple possible bases or a conflicting explicit target.
    return 2.0 if double else 0.5

def resolve_recipe(question, history):
    recipes = read_recipes()
    # Use the most recent message mentioning a recipe, not model-invented context.
    for text in [question] + [m.get('content', '') for m in reversed(history[-8:])]:
        matches = [r for r in recipes if r['name'].casefold() in str(text).casefold()]
        if len(matches) > 1:
            return None
        if matches:
            return matches[0]
    return None

'''
agent = agent.replace(marker, helper + marker)
needle = "        question_lower = s['question'].casefold()\n"
agent = agent.replace(needle, needle + "        if relative_factor(s['question']) is not None:\n            path = 'scale'\n")
needle = "        # Refuse to invent a scaling target from retrieved recipes or old messages.\n"
relative = '''        factor = relative_factor(s['question']) if s['route'] == 'scale' else None
        if factor is not None:
            if factor == 0:
                return {'tool_result': 'Please specify the recipe and the exact number of servings you want.', 'calls': s.get('calls', [])}
            recipe = resolve_recipe(s['question'], s.get('history', []))
            if recipe is None:
                return {'tool_result': 'Please specify exactly one recipe from the collection and the desired serving count.', 'calls': s.get('calls', [])}
            base = recipe['servings']
            previous = s.get('previous_scale') or {}
            # Only the immediately preceding scaled result is eligible as a base.
            if previous.get('recipe_name') == recipe['name'] and previous.get('target', 0) > 0:
                base = previous['target']
            target = base * factor
            params = {'ingredients': recipe['ingredients'], 'from_servings': recipe['servings'], 'to_servings': target}
            call = {'name': 'scale_recipe', 'arguments': params, 'recipe_name': recipe['name']}
            t0 = time.perf_counter()
            try:
                output = json.dumps(asyncio.run(invoke_mcp('scale_recipe', params)), ensure_ascii=False)
            except Exception as exc:
                output = f'Tool failed: {type(exc).__name__}: {exc}'
            return {'calls': s.get('calls', []), 'tool_call': call, 'tool_result': output,
                    'relative_base': base, 'timings': {**s.get('timings', {}), 'mcp_seconds': round(time.perf_counter()-t0, 3)}}
'''
agent = agent.replace(needle, relative + needle)
agent = agent.replace('            call = {"name": name, "arguments": params}', '            call = {"name": name, "arguments": params}')  # preserve indentation below
agent = agent.replace('        call = {"name": name, "arguments": params}\n', '        call = {"name": name, "arguments": params}\n        if name == "scale_recipe":\n            call["recipe_name"] = recipe["name"]\n')
agent = agent.replace('                lines = [f"Scaled ingredients for {target:g} servings:"]', '                base = s.get("relative_base")\n                heading = f"Scaled ingredients for {target:g} servings"\n                if base is not None:\n                    heading += f" (relative to {base:g} servings)"\n                lines = [heading + ":"]')
(ROOT / 'chef/agent_ollama_v4.py').write_text(agent, encoding='utf-8')

app = (ROOT / 'app_ollama_v3.py').read_text(encoding='utf-8')
app = app.replace('chef.agent_ollama_v3', 'chef.agent_ollama_v4').replace('OLLAMA_v3.md', 'OLLAMA_v4.md')
old = "            result = get_graph(strategy, top_k).invoke({'question': question, 'history': history})"
new = '''            previous_scale = {}
            if st.session_state.messages and st.session_state.messages[-1]['role'] == 'user' and len(st.session_state.messages) >= 2:
                prior = st.session_state.messages[-2]
                call = prior.get('details', {}).get('mcp_call') or {}
                if prior.get('role') == 'assistant' and prior.get('content', '').startswith('Scaled ingredients for ') and call.get('name') == 'scale_recipe' and call.get('recipe_name'):
                    previous_scale = {'recipe_name': call['recipe_name'], 'target': call['arguments']['to_servings']}
            result = get_graph(strategy, top_k).invoke({'question': question, 'history': history, 'previous_scale': previous_scale})'''
assert old in app
app = app.replace(old, new)
(ROOT / 'app_ollama_v4.py').write_text(app, encoding='utf-8')
