#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_anchors.py - Parses markdown past papers into structured JSONL anchors.
"""

import glob
import re
import json

TITLES = {
    '2010': ('泰德·宁与可持续性', '商业与人物成长'),
    '2011': ('绿色科技与环境倡议', '科技与生态'),
    '2012': ('发展中国家企业与跨国创新', '商业与全球经济'),
    '2013': ('记忆力训练与自我提升', '科普与心理'),
    '2014': ('乐观主义与心理健康', '心理与生活'),
    '2015': ('公路旅行与家庭传统', '生活与亲情'),
    '2016': ('超市商品布局与消费心理', '商业与消费'),
    '2017': ('时尚与出版业职业探索', '职业与个人成长'),
    '2018': ('比尔·盖茨感恩父母', '人物传记与亲情'),
    '2019': ('作家吉米·哈利与写作之路', '文学与人物传记'),
    '2020': ('名校对低收入家庭学生的资助', '教育与社会'),
    '2021': ('与陌生人交谈的积极心理效应', '心理与人际交往'),
    '2022': ('如何优雅地接受赞美', '社会交往与礼仪'),
    '2023': ('华兹华斯与自然诗歌', '文学艺术与美学'),
    '2024': ('农贸市场的魅力与社区价值', '生活与社区经济')
}

def split_english_sentences(text: str) -> list:
    """Split English text into natural sentences."""
    # Normalize whitespaces inside paragraphs
    cleaned = re.sub(r'[ \t]+', ' ', text.strip())
    # Split on sentence terminals followed by whitespace and capital letter / quote
    pattern = r'(?<=[.!?])\s+(?=[A-Z0-9“\"\'\(\[])'
    sentences = [s.strip() for s in re.split(pattern, cleaned) if s.strip()]
    return sentences

def split_chinese_sentences(text: str) -> list:
    """Split Chinese text into natural sentences."""
    cleaned = re.sub(r'[ \t]+', ' ', text.strip())
    pattern = r'(?<=[。！？])\s*'
    sentences = [s.strip() for s in re.split(pattern, cleaned) if s.strip()]
    return sentences

def main():
    files = sorted(glob.glob('英二真题/翻译/*/*-翻译.md'))
    out_path = 'knowledge_base/anchors/translation_past_papers.jsonl'
    records = []

    for f in files:
        with open(f, 'r', encoding='utf-8') as fp:
            c = fp.read()
        year_m = re.search(r'#\s*(\d{4})\s*年', c)
        if not year_m:
            continue
        year = year_m.group(1)
        en_m = re.search(r'## 英文原文\s*\n\n(.*?)(?=\n## 参考译文|\Z)', c, re.DOTALL)
        cn_m = re.search(r'## 参考译文\s*\n\n(.*?)(?=\n>|\Z)', c, re.DOTALL)
        en = en_m.group(1).strip() if en_m else ''
        cn = cn_m.group(1).strip() if cn_m else ''

        title, theme = TITLES.get(year, ('考研英语二翻译真题', '综合'))
        en_sents = split_english_sentences(en)
        cn_sents = split_chinese_sentences(cn)

        sents = []
        for i, es in enumerate(en_sents):
            cs = cn_sents[i] if i < len(cn_sents) else ''
            sents.append({
                'id': f'{year}-S{i+1}',
                'english': es,
                'chinese': cs
            })

        record = {
            'year': year,
            'exam_type': 'English II',
            'title': f'{year} {title}',
            'theme': theme,
            'word_count': len(en.split()),
            'source_text': en,
            'reference_translation': cn,
            'sentences': sents
        }
        records.append(record)

    with open(out_path, 'w', encoding='utf-8') as out_fp:
        for r in records:
            out_fp.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f'Successfully built {out_path} with {len(records)} past papers.')

if __name__ == '__main__':
    main()
