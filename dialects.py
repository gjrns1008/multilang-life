# -*- coding: utf-8 -*-
"""대만어(台語, Tâi-gí)·광동어(粵語) 칸 생성.
 - 대만어: 문장은 직접 쓴 대만어 한자(漢羅) + taibun 변환기로 TL 로마자, 단어는 華台 사전(CC BY-SA 4.0) 정확 일치 우선.
 - 광동어: 문장은 직접 쓴 광동어 구어체 + ToJyutping 으로 jyutping, 단어는 CC-Canto 정확 일치 우선.
build.py 가 add_dialects(C) 로 호출한다. 결과: c['tw'], c['yue'], c['r']['tw'], c['r']['yue'], c['tws'], c['yues'] (출처 표시)"""
import re, json, csv, collections, os

T = 'C:/Users/gjrns/AppData/Local/Temp/dict/'
HERE = os.path.dirname(os.path.abspath(__file__))

from opencc import OpenCC
_s2t = OpenCC('s2twp'); _s2hk = OpenCC('s2hk'); _t2s = OpenCC('t2s')
from taibun import Converter
_tl = Converter(system='Tailo', dialect='south', format='mark')
from ToJyutping import get_jyutping_text as _jp

_taigi = None; _canto = None
def _load():
    global _taigi, _canto
    if _taigi is None:
        d = collections.defaultdict(list)
        for r in csv.DictReader(open(T + 'taigi.csv', encoding='utf-8-sig')):
            hoa = r['HoaBun']
            for k in re.split(r'[、/；;,，]', hoa):
                k = k.strip()
                if k and len(k) <= 6: d[k].append((r['HanLoTaibunKip'].strip(), r['KipUnicode'].strip()))
        _taigi = d
    if _canto is None:
        d = {}
        for line in open(T + 'canto.txt', encoding='utf8'):
            if line.startswith('#'): continue
            m = re.match(r'(\S+) (\S+) \[(.*?)\] \{(.*?)\} /(.*)/', line.strip())
            if m: d.setdefault(m.group(2), []).append((m.group(1), m.group(4), m.group(5)))
        _canto = d

def _han(x): return re.findall(r'[一-鿿]', x)

def _split_tokens(t):
    """○○ / 영문 토큰을 기준으로 문장을 조각으로 나눈다. 조각은 변환기에 따로 넣고 토큰은 그대로 끼운다."""
    return re.split(r'(○○|[A-Za-z][A-Za-z0-9\-]*)', t)
def _join(out):
    r = ' '.join(x for x in out if x)
    r = re.sub(r'\s+([,.?!])', r'\1', r)
    return re.sub(r'\s+', ' ', r).strip()
def tl(t):
    out = []
    for part in _split_tokens(t):
        if not part: continue
        if part == '○○': out.append('OO'); continue
        if re.match(r'^[A-Za-z]', part): out.append(part); continue
        p = re.sub(r'[。？！，、]', lambda m: {'。': '.', '？': '?', '！': '!', '，': ',', '、': ','}[m.group(0)], part)
        try: out.append(_tl.get(p))
        except Exception: pass
    return _join(out)
def jp(t):
    out = []
    for part in _split_tokens(t):
        if not part: continue
        if part == '○○': out.append('OO'); continue
        if re.match(r'^[A-Za-z]', part): out.append(part); continue
        try: out.append(_jp(part))
        except Exception: pass
    return _join(out)

def tw_word(zh_simp):
    """華台 사전 정확 일치. 한자 길이가 같고(단어가 잘리지 않음) 문자 집합이 겹쳐야 채택.
    한 글자 단어는 대응 한자가 뜻 그대로인 경우만(훈독이 다른 글자면 제외)."""
    _load()
    base = zh_simp.rstrip('。？！')
    z = _s2t.convert(base)
    for key in (z, base):
        c = _taigi.get(key)
        if not c: continue
        good = []
        for han, kip in c:
            hs = _han(han)
            if not hs: continue                       # 로마자만 있는 항목 제외
            if len(hs) != len(_han(key)): continue    # 길이가 다르면(比 vs 比較) 제외
            if len(key) >= 2 and set(hs) != set(_han(key)): continue  # 글자 구성이 다르면(刺莓 vs 草莓) 제외
            if len(key) >= 2 and ''.join(hs) != ''.join(_han(key)) and ''.join(hs)[::-1] == ''.join(_han(key)): continue
            if len(key) == 1 and han != key and han != _s2t.convert(key): continue
            good.append((han, kip))
        if good:
            good.sort(key=lambda x: (x[0] != key, len(x[0])))
            # 같은 글자 여러 읽기(둘 이상)면 모호하므로 첫 항목만, 나머지는 무시
            return good[0]
    return None

def yue_word(zh_simp):
    _load()
    base = zh_simp.rstrip('。？！')
    c = _canto.get(base)
    if not c: return None
    c = sorted(c, key=lambda x: len(x[0]))
    # 한자 수가 같아야 채택 (多字 항목의 일부 일치 방지)
    c = [x for x in c if len(_han(x[0])) == len(_han(base))]
    return c[0] if c else None

def make(c, manual_tw, manual_yue):
    """c: 카드 dict. manual_*: {ko: 문자열} 직접 쓴 번역. 반환: tw, yue, 출처 표기"""
    is_sent = bool(re.search(r'[。？！]$', c['zh']))
    tw = yue = None; tws = yues = ''
    if c['ko'] in manual_tw:
        tw = manual_tw[c['ko']]; tws = 'm'
    if c['ko'] in manual_yue:
        yue = manual_yue[c['ko']]; yues = 'm'
    if tw is None and not is_sent:
        w = tw_word(c['zh'])
        if w: tw = w[0] if re.search(r'[\u4e00-\u9fff]', w[0]) else _s2t.convert(c['zh']); tws = 'd'; c['_twr'] = w[1]
    if yue is None and not is_sent:
        w = yue_word(c['zh'])
        if w: yue = w[0]; yues = 'd'; c['_yuer'] = w[1]
    return tw, yue, tws, yues
