"""Score saved retrieval cases in small Ragas batches, preserving each result."""
import argparse
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextPrecisionWithReference, LLMContextRecall, Faithfulness
from ragas.run_config import RunConfig

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path, help='JSON file saved by evaluate.py')
    parser.add_argument('--offset', type=int, default=0, help='Number of retrieval cases to skip')
    parser.add_argument('--limit', type=int, default=1, help='Number of retrieval cases to score')
    args = parser.parse_args()
    if args.offset < 0 or args.limit < 1:
        parser.error('offset must be non-negative and limit positive')
    saved = json.loads(args.run.read_text(encoding='utf-8'))
    cases = [r for r in saved['cases'] if r.get('expected_route') == 'retrieve' and r.get('contexts') and r.get('answer')]
    selected = cases[args.offset:args.offset + args.limit]
    if not selected:
        parser.error('No retrieval cases in that range')
    output = {'source_run': str(args.run.resolve()), 'judge_model': os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b'), 'offset': args.offset, 'requested': args.limit, 'cases': []}
    path = ROOT / 'results' / f"ragas_batch_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1000000:06d}.json"
    path.parent.mkdir(exist_ok=True)
    judge = LangchainLLMWrapper(ChatGroq(model=os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b'), temperature=0))
    for case in selected:
        record = {'id': case['id'], 'question': case['question']}
        try:
            sample = SingleTurnSample(user_input=case['question'], reference=case['reference'], response=case['answer'], retrieved_contexts=case['contexts'])
            result = evaluate(EvaluationDataset(samples=[sample]), metrics=[LLMContextPrecisionWithReference(), LLMContextRecall(), Faithfulness()], llm=judge, run_config=RunConfig(max_workers=1, max_retries=3, timeout=180), raise_exceptions=False)
            record['scores'] = json.loads(result.to_pandas().to_json(orient='records'))[0]
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        output['cases'].append(record)
        path.write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
        print('Saved', case['id'], 'to', path, flush=True)
        metrics = ('llm_context_precision_with_reference', 'context_recall', 'faithfulness')
        if record.get('error') or all(record.get('scores', {}).get(metric) is None for metric in metrics):
            print('No usable scores for this case; stopping to avoid repeated failed requests. Retry from this offset.', flush=True)
            break

if __name__ == '__main__': main()
