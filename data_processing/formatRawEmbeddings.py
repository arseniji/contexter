import re
import numpy as np
import pickle
from pymorphy3 import MorphAnalyzer
from functools import lru_cache
from multiprocessing import Pool, cpu_count
from collections import defaultdict

CYRILLIC_RE = re.compile(r'^[а-яёА-ЯЁ]{3,20}$')
VEC_DIM = 300
MIN_NOUN_SCORE = 0.1
MIN_COUNT = 3  

_morph = None

def init_worker():
    global _morph
    _morph = MorphAnalyzer()

@lru_cache(maxsize=500_000)
def _cached_lemma(word: str):
    parses = _morph.parse(word)
    if not parses:
        return None, 'no_parse'

    noun_parses = [p for p in parses
        if p.tag.POS == 'NOUN'
        and p.tag.case == 'nomn'
        and 'Abbr' not in p.tag
        and 'Name' not in p.tag
        and 'Geox' not in p.tag
        and 'Surn' not in p.tag
        and 'Patr' not in p.tag
        and p.tag.number in ('sing', 'plur') ]
    if not noun_parses:
        best_pos = parses[0].tag.POS
        return None, f'not_noun:{best_pos}'

    best = max(noun_parses, key=lambda p: p.score)
    if best.score < MIN_NOUN_SCORE:
        return None, f'low_score:{best.score:.3f}'

    lemma = best.normal_form.replace('ё', 'е')
    return lemma, None


def process_line(line: str):
    line = line.strip()
    if not line:
        return None

    parts = line.split(' ')
    if len(parts) != VEC_DIM + 1:
        return ('skip_parts', None)

    word = parts[0]
    if not CYRILLIC_RE.match(word):
        return ('skip_regex', word)

    lemma, reason = _cached_lemma(word.lower())
    if lemma is None:
        return ('skip_morph', word, reason)

    vec = np.array(parts[1:], dtype=np.float32)
    return ('ok', lemma, vec)


def read_lines_chunked(filepath: str, chunk_size: int = 50_000):
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f)  
        chunk = []
        for line in f:
            chunk.append(line)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk


def main():
    filepath = 'C:/Users/Krytoi/IdeaProjects/contexter/src/main/resources/vector/cc.ru.300.vec'
    output_path = 'final3.pkl'
    debug_log_path = 'debug_filter.log'

    n_workers = max(1, cpu_count() - 1)
    chunk_size = 50_000

    lemma_sums = {}
    lemma_counts = {}
    total_lines = 0

    
    stats = defaultdict(int)
    
    examples = defaultdict(list)
    MAX_EXAMPLES = 10

    print(f"Запускаем {n_workers} воркеров...")

    with Pool(processes=n_workers, initializer=init_worker) as pool:
        for chunk in read_lines_chunked(filepath, chunk_size):
            results = pool.map(process_line, chunk)

            for result in results:
                if result is None:
                    stats['empty_line'] += 1
                    continue

                tag = result[0]

                if tag == 'ok':
                    _, lemma, vec = result
                    if lemma in lemma_sums:
                        lemma_sums[lemma] += vec
                        lemma_counts[lemma] += 1
                    else:
                        lemma_sums[lemma] = vec.copy()
                        lemma_counts[lemma] = 1
                    stats['ok'] += 1

                elif tag == 'skip_parts':
                    stats['skip_parts'] += 1

                elif tag == 'skip_regex':
                    word = result[1]
                    stats['skip_regex'] += 1
                    if len(examples['skip_regex']) < MAX_EXAMPLES:
                        examples['skip_regex'].append(word)

                elif tag == 'skip_morph':
                    _, word, reason = result
                    
                    reason_key = reason.split(':')[0] if reason else 'unknown'
                    stats[f'skip_morph:{reason_key}'] += 1
                    if len(examples[f'skip_morph:{reason_key}']) < MAX_EXAMPLES:
                        examples[f'skip_morph:{reason_key}'].append(f'{word} ({reason})')

            total_lines += len(chunk)
            print(
                f"  обработано: {total_lines:,} | "
                f"лемм: {len(lemma_sums):,} | "
                f"ok: {stats['ok']:,} | "
                f"skip_regex: {stats['skip_regex']:,} | "
                f"skip_morph:not_noun: {stats['skip_morph:not_noun']:,} | "
                f"skip_morph:low_score: {stats['skip_morph:low_score']:,}"
            )

    
    noun_vectors = {
        lemma: lemma_sums[lemma] / lemma_counts[lemma]
        for lemma in lemma_sums
        if lemma_counts[lemma] >= MIN_COUNT
    }

    filtered_by_count = len(lemma_sums) - len(noun_vectors)
    print(f"\nИтог:")
    print(f"Уникальных лемм до фильтра частотности: {len(lemma_sums):,}")
    print(f"Отброшено по MIN_COUNT={MIN_COUNT}: {filtered_by_count:,}")
    print(f"Сохранено существительных: {len(noun_vectors):,}")

    
    with open(debug_log_path, 'w', encoding='utf-8') as log:
        log.write("=== СТАТИСТИКА ФИЛЬТРАЦИИ ===\n\n")
        for key, count in sorted(stats.items(), key=lambda x: -x[1]):
            log.write(f"{key}: {count:,}\n")
            if key in examples:
                for ex in examples[key]:
                    log.write(f"    • {ex}\n")
        log.write(f"\n=== ОТБРОШЕНО ПО ЧАСТОТНОСТИ (MIN_COUNT={MIN_COUNT}) ===\n")
        log.write(f"Количество: {filtered_by_count:,}\n")

    print(f"\nЛог причин отсева: {debug_log_path}")

    with open(output_path, 'wb') as out:
        pickle.dump(noun_vectors, out)

    print(f"Сохранено в {output_path}")


if __name__ == '__main__':
    main()