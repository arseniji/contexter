import pickle
import numpy as np
import zipfile
import os
from wordfreq import top_n_list
import pymorphy3


EMB_PKL_PATH = 'final3.pkl'          
OUTPUT_DIR = 'java_datasets'         
POPULAR_LIMIT = 10000              
ZIP_NAME = 'contexto_data_ru.zip'    

def main():
    print("Загрузка эмбеддингов из pickle...")
    with open(EMB_PKL_PATH, 'rb') as f:
        emb_dict = pickle.load(f)  

    if not emb_dict:
        raise ValueError("Файл final3.pkl пуст или имеет неверный формат.")

    lemmas = sorted(emb_dict.keys())
    dim = emb_dict[lemmas[0]].shape[0]
    print(f"Всего лемм в датасете: {len(lemmas):,}, размерность: {dim}")

    
    print("Формирование полной матрицы эмбеддингов...")
    lemma_to_idx = {lemma: i for i, lemma in enumerate(lemmas)}
    full_matrix = np.empty((len(lemmas), dim), dtype='<f4')  
    for i, lemma in enumerate(lemmas):
        full_matrix[i] = emb_dict[lemma]

    
    print(f"Загрузка {POPULAR_LIMIT:,} популярных слов (wordfreq)...")
    top_words = top_n_list('ru', POPULAR_LIMIT)

    morph = pymorphy3.MorphAnalyzer()
    valid_words = []
    indices = []

    print("Пересечение популярных слов и эмбеддингов...")
    for word in top_words:
        w = word.lower()
        if w not in lemma_to_idx:
            continue  

        
        parses = morph.parse(w)
        for p in parses:
            if (p.tag.POS == 'NOUN' and
                p.tag.case == 'nomn' and
                'Abbr' not in p.tag and 'Name' not in p.tag and
                'Geox' not in p.tag and 'Surn' not in p.tag and 'Patr' not in p.tag and
                p.tag.number in ('sing', 'plur')):
                valid_words.append(w)
                indices.append(lemma_to_idx[w])
                break

    
    seen = set()
    unique_words, unique_indices = [], []
    for w, idx in zip(valid_words, indices):
        if w not in seen:
            seen.add(w)
            unique_words.append(w)
            unique_indices.append(idx)

    print(f"Найдено популярных существительных в эмбеддингах: {len(unique_words):,}")

    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    emb_path = os.path.join(OUTPUT_DIR, 'embeddings.bin')
    norms = np.linalg.norm(full_matrix, axis=1, keepdims=True)
    full_matrix = full_matrix / norms
    full_matrix.tofile(emb_path)
    print(f"{emb_path} ({full_matrix.nbytes / 1024**2:.2f} MB)")

    
    idx_arr = np.array(unique_indices, dtype='<i4')  
    idx_path = os.path.join(OUTPUT_DIR, 'popular_indices.bin')
    idx_arr.tofile(idx_path)
    print(f"{idx_path} ({idx_arr.nbytes / 1024:.2f} KB)")

    
    vocab_path = os.path.join(OUTPUT_DIR, 'vocab.txt')
    with open(vocab_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lemmas))
    print(f"{vocab_path} ({len(lemmas):,} строк)")

    
    pop_words_path = os.path.join(OUTPUT_DIR, 'popular_words.txt')
    with open(pop_words_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unique_words))
    print(f"{pop_words_path} ({len(unique_words):,} строк)")

    
    print(f"Упаковка в {ZIP_NAME}...")
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(OUTPUT_DIR):
            zf.write(os.path.join(OUTPUT_DIR, fname), arcname=fname)

    print("Готово")

if __name__ == '__main__':
    main()