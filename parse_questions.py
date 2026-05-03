#!/usr/bin/env python3
"""
Parser de arquivos de prova e gabarito para o Simulador DETRAN.
Gera data/questions.json e imagens_necessarias.xlsx
"""

import os
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROVAS_DIR = BASE_DIR / "provas"
GABARITOS_DIR = BASE_DIR / "gabaritos"
DATA_DIR = BASE_DIR / "data"

IMAGE_PATTERNS = [
    r'placa ao lado',
    r'figura ao lado',
    r'imagem ao lado',
    r'sinal ao lado',
    r'\([A-Z]-\d+[a-z]?\)',
]

CATEGORY_MAP = {
    'geral': {'name': 'Simulado Completo', 'color': '#1a73e8', 'icon': '📋'},
    'legislacao': {'name': 'Legislação de Trânsito', 'color': '#4caf50', 'icon': '⚖️'},
    'direcao_defensiva': {'name': 'Direção Defensiva', 'color': '#ff9800', 'icon': '🛡️'},
    'primeiros_socorros': {'name': 'Primeiros Socorros', 'color': '#f44336', 'icon': '🏥'},
    'mecanica_basica': {'name': 'Mecânica Básica', 'color': '#9c27b0', 'icon': '🔧'},
    'meio_ambiente': {'name': 'Meio Ambiente e Cidadania', 'color': '#009688', 'icon': '🌱'},
    'prova_mista': {'name': 'Prova Mista', 'color': '#607d8b', 'icon': '📝'},
}

# Distribuição DETRAN (30 questões)
DETRAN_DISTRIBUTION = {
    'legislacao': 9,
    'direcao_defensiva': 9,
    'primeiros_socorros': 4,
    'mecanica_basica': 4,
    'meio_ambiente': 4,
}


def detect_image_code(text):
    match = re.search(r'\(([A-Z]-\d+[a-z]?)\)', text)
    if match:
        return match.group(1)
    if re.search(r'placa ao lado|figura ao lado|imagem ao lado|sinal ao lado', text, re.IGNORECASE):
        return 'SEM_CODIGO'
    return None


def has_image(text):
    for pattern in IMAGE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def parse_prova(filepath):
    with open(filepath, 'r', encoding='cp1252', errors='replace') as f:
        content = f.read()

    questions = []

    # Encontra blocos de questão pelo número no início da linha
    q_start_pattern = re.compile(r'(?m)^\s{0,5}(\d{1,2})\s{3,}')
    matches = list(q_start_pattern.finditer(content))

    alt_pattern = re.compile(r'(?m)^\s{5,}([A-E])\s*-\s*(.+)$')

    for idx, match in enumerate(matches):
        num = int(match.group(1))
        if num < 1 or num > 50:
            continue

        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        block = content[start:end]

        # Offset dentro do bloco onde termina o número (início do texto da questão)
        match_inner_end = match.end() - match.start()

        # Alternativas neste bloco
        alt_matches = list(alt_pattern.finditer(block))

        if not alt_matches:
            continue

        # Texto da questão: desde após o número até a primeira alternativa
        q_text_raw = block[match_inner_end:alt_matches[0].start()]
        q_lines = [l.strip() for l in q_text_raw.split('\n') if l.strip()]
        q_text = ' '.join(q_lines)

        # Parse alternativas
        alternatives = {}
        for a_idx, a_match in enumerate(alt_matches):
            letter = a_match.group(1)
            a_text = a_match.group(2).strip()

            a_end = alt_matches[a_idx + 1].start() if a_idx + 1 < len(alt_matches) else len(block)
            continuation_raw = block[a_match.end():a_end]

            for line in continuation_raw.split('\n'):
                stripped = line.strip()
                if stripped and not re.match(r'^-\s*\d+$', stripped):
                    a_text += ' ' + stripped

            alternatives[letter] = a_text.strip()

        image_code = detect_image_code(q_text)
        needs_image = has_image(q_text) or image_code is not None

        questions.append({
            'number': num,
            'text': q_text,
            'alternatives': alternatives,
            'has_image': needs_image,
            'image_code': image_code,
            'image_path': None,
            'correct': None,
        })

    return questions


def parse_gabarito(filepath):
    with open(filepath, 'r', encoding='cp1252', errors='replace') as f:
        content = f.read()

    answers = {}
    lines = content.split('\n')

    q_pattern = re.compile(r'^\s{0,4}(\d{1,2})\s+\S')
    ans_pattern = re.compile(r'^\s{2,}([A-E])\s{2,}-')

    current_num = None
    for line in lines:
        q_match = q_pattern.match(line)
        if q_match:
            num = int(q_match.group(1))
            if 1 <= num <= 50:
                current_num = num
            continue

        if current_num is not None:
            a_match = ans_pattern.match(line)
            if a_match:
                answers[current_num] = a_match.group(1)
                current_num = None

    return answers


def get_file_pairs():
    pairs = []
    for prova_file in sorted(PROVAS_DIR.glob('*.txt')):
        stem = prova_file.stem

        if re.match(r'^prova_(\d+)$', stem):
            num = stem.split('_')[1]
            gab_file = GABARITOS_DIR / f'gab_{num}.txt'
            category = 'geral'
            exam_name = f'Simulado {int(num):02d}'
        elif stem.startswith('dd'):
            num = stem[2:]
            gab_file = GABARITOS_DIR / f'gab_dd{num}.txt'
            category = 'direcao_defensiva'
            exam_name = f'Direção Defensiva {int(num):02d}'
        elif stem.startswith('le'):
            num = stem[2:]
            gab_file = GABARITOS_DIR / f'gab_le{num}.txt'
            category = 'legislacao'
            exam_name = f'Legislação {int(num):02d}'
        elif stem.startswith('pm'):
            num = stem[2:]
            gab_file = GABARITOS_DIR / f'gab_pm{num}.txt'
            category = 'prova_mista'
            exam_name = f'Prova Mista {int(num):02d}'
        elif stem.startswith('mb'):
            num = stem[2:]
            gab_file = GABARITOS_DIR / f'gab_mb{num}.txt'
            category = 'mecanica_basica'
            exam_name = f'Mecânica Básica {int(num):02d}'
        elif stem.startswith('mc'):
            num = stem[2:]
            gab_file = GABARITOS_DIR / f'gab_mc{num}.txt'
            category = 'meio_ambiente'
            exam_name = f'Meio Ambiente {int(num):02d}'
        elif stem.startswith('ps'):
            num = stem[2:]
            gab_file = GABARITOS_DIR / f'gab_ps{num}.txt'
            category = 'primeiros_socorros'
            exam_name = f'Primeiros Socorros {int(num):02d}'
        else:
            continue

        if gab_file.exists():
            pairs.append((prova_file, gab_file, category, exam_name, stem))
        else:
            print(f'AVISO: Gabarito não encontrado para {stem}')

    return pairs


CSV_PATH = BASE_DIR / 'imagens_necessarias.csv'
CSV_FIELDS = ['exam_id', 'exam_name', 'question_number', 'question_text',
              'image_code', 'image_path', 'observacoes']


def load_existing_image_paths():
    """Lê o CSV existente e retorna dict {(exam_id, question_number): image_path}."""
    import csv
    paths = {}
    if not CSV_PATH.exists():
        return paths
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            path = row.get('image_path', '').strip()
            if path:
                key = (row['exam_id'], int(row['question_number']))
                paths[key] = path
    return paths


def build_questions_json():
    import csv
    DATA_DIR.mkdir(exist_ok=True)

    # Carrega caminhos já preenchidos (download_images.py ou manual)
    existing_paths = load_existing_image_paths()

    exams = []
    all_questions_with_images = []

    for prova_file, gab_file, category, exam_name, exam_id in get_file_pairs():
        print(f'Processando: {exam_id} ...')

        questions = parse_prova(prova_file)
        answers = parse_gabarito(gab_file)

        for q in questions:
            q['correct'] = answers.get(q['number'])
            if q['has_image']:
                # Aplica caminho já conhecido, se existir
                q['image_path'] = existing_paths.get((exam_id, q['number']))
                all_questions_with_images.append({
                    'exam_id': exam_id,
                    'exam_name': exam_name,
                    'question_number': q['number'],
                    'question_text': q['text'][:120] + '...' if len(q['text']) > 120 else q['text'],
                    'image_code': q['image_code'],
                    'image_path': q['image_path'] or '',
                    'observacoes': '',
                })

        exam = {
            'id': exam_id,
            'name': exam_name,
            'category': category,
            'questions': questions,
        }
        exams.append(exam)

    data = {
        'exams': exams,
        'categories': CATEGORY_MAP,
        'detran_distribution': DETRAN_DISTRIBUTION,
    }

    out_path = DATA_DIR / 'questions.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    filled = sum(1 for q in all_questions_with_images if q['image_path'])
    print(f'\n✅ questions.json gerado: {out_path}')
    print(f'   Total de provas: {len(exams)}')
    total_q = sum(len(e["questions"]) for e in exams)
    print(f'   Total de questões: {total_q}')
    print(f'   Questões com imagens: {len(all_questions_with_images)} ({filled} com caminho)')

    return all_questions_with_images


def build_csv(image_questions):
    import csv
    # Preserva linhas do CSV existente que já tenham image_path preenchido
    existing = {}
    if CSV_PATH.exists():
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                key = (row['exam_id'], row['question_number'])
                if row.get('image_path', '').strip():
                    existing[key] = row

    for q in image_questions:
        key = (q['exam_id'], str(q['question_number']))
        if key in existing:
            q['image_path'] = existing[key]['image_path']
            q['observacoes'] = existing[key].get('observacoes', '')

    with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(image_questions)
    print(f'✅ CSV gerado: {CSV_PATH}')


if __name__ == '__main__':
    print('=== Parser do Simulador DETRAN ===\n')
    image_questions = build_questions_json()

    print('\nGerando CSV de imagens...')
    build_csv(image_questions)

    print('\n✅ Pronto! Execute agora:')
    print('   Abra index.html no navegador para usar o simulador.')
