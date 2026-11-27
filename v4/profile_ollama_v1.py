"""Measure one warm local generation; save raw timings and active-model memory."""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:11434'
model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')

def request(path, data=None):
    body = None if data is None else json.dumps(data).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as response:
        return json.load(response)

def main():
    started = time.perf_counter()
    answer = request('/api/generate', {'model': model, 'prompt': 'Give three simple tips for storing fresh tomatoes.', 'stream': False, 'options': {'temperature': 0, 'num_ctx': 8192, 'num_predict': 128}})
    elapsed = time.perf_counter() - started
    running = request('/api/ps')
    try:
        gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        gpu = None
    duration = answer.get('eval_duration', 0)
    result = {'model': model, 'prompt': 'Give three simple tips for storing fresh tomatoes.', 'response': answer.get('response'), 'wall_seconds': round(elapsed, 3), 'ollama': {k: answer.get(k) for k in ('total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration')}, 'output_tokens_per_second': round(answer['eval_count'] * 1e9 / duration, 2) if duration else None, 'running_models': running, 'nvidia_smi_csv': gpu}
    path = ROOT / 'results' / f"ollama_profile_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('Saved:', path)

if __name__ == '__main__': main()
