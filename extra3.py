# -*- coding: utf-8 -*-
"""Tatoeba(CC BY 2.0 FR) 에서 추출한 실생활 문장 카드. build.py 가 load3(add)로 호출한다.
 - 데이터: AppData/Local/Temp/tat/tat_good.json (mine.py -> filter.py -> refine.py)
 - 대만어(nan)·광동어(yue)는 같은 문장에 말뭉치 번역이 연결된 경우에만 채운다(자동 번역 없음).
"""
import json, os, re, sys

TAT = 'C:/Users/gjrns/AppData/Local/Temp/tat/tat_good.json'

EXTRA_UNITS3 = [
 ("t_ask",     "질문·요청 (말뭉치)",   "🙋", 1),
 ("t_health",  "건강·몸 (말뭉치)",     "💊", 1),
 ("t_food",    "음식·식사 (말뭉치)",   "🍽️", 2),
 ("t_move",    "이동·장소 (말뭉치)",   "🚆", 2),
 ("t_shop",    "쇼핑·돈 (말뭉치)",     "🛒", 2),
 ("t_daily",   "일상 대화 (말뭉치)",   "🗣️", 3),
 ("t_feel",    "감정·의견 (말뭉치)",   "💬", 3),
 ("t_home",    "집·가족 (말뭉치)",     "🏠", 3),
 ("t_weather", "날씨·자연 (말뭉치)",   "🌤️", 3),
 ("t_work",    "일·학교 (말뭉치)",     "📘", 4),
 ("t_misc",    "그 밖의 생활 문장",    "📝", 4),
]

def load3(add, existing_ko, ja_reading, t2s):
    if not os.path.exists(TAT): return 0, {}
    data = json.load(open(TAT, encoding='utf8'))
    n = 0; side = {}
    seen_zh = set(); seen_en = set()
    for o in data:
        ko = o['ko'].strip()
        if ko in existing_ko: continue
        # 기존 카드와 의미가 같은 문장 제외(영어/중국어 정규화 비교)
        en = o['en'].strip()
        zh = t2s(o['zh'].strip())
        k_en = re.sub(r'\W', '', en.lower()); k_zh = re.sub(r'[\W]', '', zh)
        if k_en in seen_en or k_zh in seen_zh: continue
        seen_en.add(k_en); seen_zh.add(k_zh)
        ja = o['ja'].strip()
        hira, _ = ja_reading(ja)
        add(o['topic'], ko, ja, hira, en, zh if re.search(r'[。？！.?!]$', zh) else zh + '。', None)
        existing_ko.add(ko)
        side[ko] = dict(tw=(o.get('nan') or [None])[0], yue=(o.get('yue') or [None])[0], zh_orig=o['zh'])
        n += 1
    return n, side
