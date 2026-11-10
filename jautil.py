# -*- coding: utf-8 -*-
"""일본어 문장(한자+가나) -> (히라가나 읽기, 문절 띄어쓰기 헵번 로마자). fugashi(unidic-lite) + pykakasi."""
import re
import fugashi, pykakasi
_tag = fugashi.Tagger()
_kks = pykakasi.kakasi()
_PART = {'は': 'wa', 'を': 'o', 'へ': 'e'}
_CASE = {'は','を','へ','が','に','で','も','の','と','から','まで','や','より','って'}
_DIG = str.maketrans('０１２３４５６７８９', '0123456789')
_NUMREAD = {'0':'ぜろ','1':'いち','2':'に','3':'さん','4':'よん','5':'ご','6':'ろく','7':'なな','8':'はち','9':'きゅう'}

def _kata2hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)

def _tok_reading(w):
    s = w.surface
    if s == '私': return 'わたし'
    if s == '僕': return 'ぼく'
    if s == '彼女': return 'かのじょ'
    if re.fullmatch(r'[ぁ-んー]+', s): return s
    if re.fullmatch(r'[ァ-ヶー]+', s): return s            # 외래어는 가타카나 그대로(로마자 변환 시 처리)
    f = w.feature
    rd = getattr(f, 'kana', None)
    if not rd or rd == '*': rd = getattr(f, 'pron', None)
    if rd and rd != '*': return _kata2hira(rd)
    return s

def segment(t):
    """[(표면형, 읽기, is_particle)] 문절 리스트"""
    t = t.translate(_DIG)
    t = re.sub(r'([0-9])つ', lambda m: {'1':'ひと','2':'ふた','3':'みっ','4':'よっ','5':'いつ','6':'むっ','7':'なな','8':'やっ','9':'ここの'}.get(m.group(1), m.group(1)) + 'つ', t)
    bs = []  # 문절: [surface, reading, pos, particle_kind]
    for w in _tag(t):
        sf, pos = w.surface, w.feature.pos1
        rd = _tok_reading(w)
        if pos == '接頭辞' and sf in ('お','ご','御'):
            bs.append([sf, rd, '接頭辞', '', None]); continue
        if pos in ('補助記号',) :
            if bs: bs[-1][3] += sf
            continue
        attach = False
        if bs and bs[-1][2] == '接頭辞' and not bs[-1][3] and bs[-1][4] is None and bs[-1][0] in ('お','ご','御'):
            attach = True
        elif bs:
            if pos in ('助動詞', '接尾辞'): attach = True
            elif pos == '助詞' and sf not in _CASE: attach = True
            elif pos in ('名詞', '接頭辞') and bs[-1][2] in ('名詞', '接頭辞'): attach = True
            elif pos in ('動詞', '形容詞') and bs[-1][2] == '動詞' and sf in ('いる','ある','しまう','おく','くる','いく','みる','くれる','もらう'): attach = True
        if pos == '助詞' and sf in _CASE: 
            bs.append([sf, rd, '助詞', '', sf])
        elif attach:
            bs[-1][0] += sf; bs[-1][1] += rd
            if pos in ('名詞',): bs[-1][2] = '名詞'
        else:
            bs.append([sf, rd, pos, '', None])
    return bs

def romanize(t):
    bs = segment(t)
    parts = []; hira = []
    for sf, rd, pos, tail, p in bs:
        hira.append(rd)
        if p in _PART: parts.append(_PART[p]); continue
        if p: parts.append(''.join(x['hepburn'] for x in _kks.convert(rd))); continue
        r = ''.join(x['hepburn'] for x in _kks.convert(rd))
        if re.fullmatch(r'[0-9]+', rd): r = rd
        r = re.sub(r'^([0-9]+)tsu$', lambda m: m.group(1), r)
        parts.append(r)
    rom = re.sub(r'\s+', ' ', ' '.join(parts)).strip()
    return ''.join(hira), rom

if __name__ == '__main__':
    import sys; sys.stdout.reconfigure(encoding='utf-8')
    for t in ['ケイトはとても速く英語を話します。', 'コーヒーはお好きですか？', 'ビールを２つください。', '私は猫を二匹飼っています。', '明日お会いしましょう。', '彼は野球選手だ。', 'もう一度お願いします。']:
        print(t, '->', romanize(t))
