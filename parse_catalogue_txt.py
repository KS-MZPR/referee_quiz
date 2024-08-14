import json
import re


def parse_catalogue_txt(catalogue_file: str, catalogue_key_file: str, debug: bool = False):
    key_answers = parse_key_answers(catalogue_key_file=catalogue_key_file)
    catalogue_json = {'all_questions': []}
    question_id = 0
    current_question = None
    subanswers = []

    with open(catalogue_file, encoding="utf-8") as f:
        catalogue_lines = f.readlines()
    pattern = re.compile(r'^(?P<orig_id>(\d{1,2}\.\d{1,2}|(RSZ|SAR)\.\d{1,2}))(\t|\) )(?P<text>.+)\n$')
    for inx, line in enumerate(catalogue_lines):
        if matched_question := pattern.match(line):
            if current_question is None:
                current_question = matched_question
                continue
            if not subanswers:
                raise ValueError

            question_id += 1
            question = {
                "id": question_id,
                "orig_id": f"_{current_question['orig_id']}",
                "text": current_question['text'],
                "rules": key_answers[current_question['orig_id']]["rules"],
                'subanswers': subanswers
            }
            catalogue_json['all_questions'].append(question)
            subanswers = []
            current_question = matched_question

        elif matched_answer := re.match(r'^(?P<orig_id>[a-z]\))\t(?P<text>.+)$', line):
            subanswers.append(
                {
                    "orig_id": matched_answer['orig_id'],
                    "text": matched_answer['text'],
                    "correctness": int(matched_answer['orig_id'] in key_answers[current_question['orig_id']]["answers"])
                }
            )
        else:
            raise ValueError(f'{inx}: {line}')

    question_id += 1
    catalogue_json['all_questions'].append(
        {
            "id": question_id,
            "orig_id": f"_{current_question['orig_id']}",
            "text": current_question['text'],
            "rules": key_answers[current_question['orig_id']]["rules"],
            'subanswers': subanswers
        }
    )
    if debug:
        for q in catalogue_json['all_questions'][:5]:
            print(q)
    return catalogue_json


def parse_key_answers(catalogue_key_file, debug=False):
    key_answers = {}
    with open(catalogue_key_file, encoding="utf-8") as f:
        catalogue_lines = f.readlines()
    pattern = re.compile(r'(?P<orig_id>\d{1,2}\.\d{1,2}|(RSZ|SAR)\.\d{1,2})\)?\t(?P<answers>.+)\t(?P<rules>.+)')
    for inx, line in enumerate(catalogue_lines):
        matched_line = pattern.match(line)
        if not matched_line:
            raise ValueError(f'{inx}: {line}')
        answers = matched_line['answers'].replace(' ', '')
        if not re.match(r'[a-z,]+', answers):
            raise ValueError(f'{inx} answers: {answers}')
        rules = matched_line['rules'].strip()
        key_answers[matched_line['orig_id']] = {
            'answers': [f'{x})' for x in answers.split(',')],
            'rules': rules
        }
    if debug:
        for a in list(key_answers.keys())[:5]:
            print(key_answers[a])
    return key_answers


if __name__ == '__main__':
    for language in ('pl', 'en'):
        catalogue_json = parse_catalogue_txt(
            catalogue_file=f'data/catalogue_{language}_2024.txt',
            catalogue_key_file=f'data/keys_{language}_2024.txt',
            debug=True
        )
        catalogue_json_path = f'catalogue_of_rules_questions_{language}.json'
        with open(catalogue_json_path, 'w', encoding='utf8') as f:
            json.dump(catalogue_json, f, indent=2, sort_keys=False, ensure_ascii=False)

        max_length_q, max_length_a, max_length_full = 0, 0, 0
        for question in catalogue_json['all_questions']:
            max_length_q = max_length_q if max_length_q >= len(question['text']) else len(question['text'])
            length_full = len(question['text'])
            for answer in question['subanswers']:
                max_length_a = max_length_a if max_length_a >= len(answer['text']) else len(answer['text'])
                length_full += len(answer['text'])
            max_length_full = max(max_length_full, length_full)
        print(f'Max lenghts to determine database table column values length: '
              f'{language=}: {max_length_q=}, {max_length_a=}, {max_length_full=}')
