#!/usr/bin/env python3

import csv
import json
import re
import sys
import time
from pathlib import Path
from icrawler.builtin import BingImageCrawler

BASE_DIR   = Path(__file__).parent
IMAGES_DIR = BASE_DIR / 'images'
CSV_PATH   = BASE_DIR / 'imagens_necessarias.csv'
JSON_PATH  = BASE_DIR / 'data' / 'questions.json'

DELAY      = 0.3
MAX_IMAGES = 5


# ── Bing Image Search ───────────────────────────────────────────────────────

def build_query(code: str) -> str:
    letter = code[0].upper()

    type_map = {
        'R': 'regulamentação',
        'A': 'advertência',
        'I': 'indicação',
        'P': 'pedestre',
    }

    tipo = type_map.get(letter, 'trânsito')

    return f"{code} placa de trânsito Brasil {tipo} oficial sinalização PNG fundo branco"


def download_from_bing(code: str) -> tuple[Path | None, str]:
    temp_dir = IMAGES_DIR / f"_tmp_{code}"
    temp_dir.mkdir(exist_ok=True)

    query = build_query(code)

    crawler = BingImageCrawler(
        storage={'root_dir': str(temp_dir)},
        downloader_threads=4,
        parser_threads=2
    )

    try:
        crawler.crawl(
            keyword=query,
            max_num=MAX_IMAGES,
            min_size=(200, 200)
        )
    except Exception:
        return None, ""

    files = list(temp_dir.glob("*"))

    if not files:
        return None, ""

    # escolhe maior imagem (melhor qualidade)
    best_file = max(files, key=lambda f: f.stat().st_size)

    ext = best_file.suffix.replace('.', '').lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        ext = 'jpg'

    return best_file, ext


# ── Utils ──────────────────────────────────────────────────────────────────

def safe_filename(code: str, ext: str) -> str:
    clean = re.sub(r'[^\w\-]', '_', code)
    return f'placa_{clean}.{ext}'


def find_existing(code: str) -> Path | None:
    pattern = re.compile(re.escape(code.replace('-', '_')), re.IGNORECASE)
    for f in IMAGES_DIR.iterdir():
        if pattern.search(f.stem):
            return f
    return None


# ── CSV / JSON ─────────────────────────────────────────────────────────────

def load_csv() -> list[dict]:
    if not CSV_PATH.exists():
        print(f'❌ CSV não encontrado: {CSV_PATH}')
        sys.exit(1)

    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def save_csv(rows: list[dict]):
    fields = list(rows[0].keys())

    with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def apply_paths_to_json(code_to_path: dict[str, str]):
    if not JSON_PATH.exists():
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0

    for exam in data['exams']:
        for q in exam['questions']:
            if q.get('image_code') and q['image_code'] in code_to_path:
                q['image_path'] = code_to_path[q['image_code']]
                updated += 1

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'✅ questions.json atualizado ({updated} entradas)')


# ── Main ───────────────────────────────────────────────────────────────────

def run(force: bool = False):
    IMAGES_DIR.mkdir(exist_ok=True)
    rows = load_csv()

    pending: dict[str, list[int]] = {}

    for i, row in enumerate(rows):
        code = row.get('image_code', '').strip()

        if not code or code == 'SEM_CODIGO':
            continue

        if row.get('image_path') and not force:
            continue

        pending.setdefault(code, []).append(i)

    if not pending:
        print('✅ Nenhuma imagem pendente.')
        return

    print(f'Imagens a baixar: {len(pending)}\n')

    code_to_path = {}
    ok = 0

    for n, (code, indices) in enumerate(pending.items(), 1):
        prefix = f'[{n:>3}/{len(pending)}] {code:<10}'

        if not force:
            existing = find_existing(code)
            if existing:
                rel = f'images/{existing.name}'
                for i in indices:
                    rows[i]['image_path'] = rel
                code_to_path[code] = rel
                print(f'{prefix} já existe → {existing.name}')
                ok += 1
                continue

        print(f'{prefix} baixando...', end=' ', flush=True)

        try:
            temp_file, ext = download_from_bing(code)

            if not temp_file:
                print('falhou')
                continue

            fname = safe_filename(code, ext)
            final_path = IMAGES_DIR / fname

            final_path.write_bytes(temp_file.read_bytes())

            # limpa pasta temporária
            for f in temp_file.parent.glob("*"):
                f.unlink()
            temp_file.parent.rmdir()

            rel = f'images/{fname}'

            for i in indices:
                rows[i]['image_path'] = rel

            code_to_path[code] = rel

            print(f'✅ {fname}')
            ok += 1

        except Exception as e:
            print(f'erro: {e}')

        time.sleep(DELAY)

    save_csv(rows)

    if code_to_path:
        apply_paths_to_json(code_to_path)

    print(f'\nResumo: {ok}/{len(pending)} baixadas')


if __name__ == '__main__':
    force = '--force' in sys.argv
    print('=== Download via Bing Images (icrawler) ===\n')
    run(force=force)