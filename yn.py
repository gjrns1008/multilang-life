# -*- coding: utf-8 -*-
"""광동어(yue)·대만어(nan) 독립 학습 코퍼스를 앱 데이터(D.cy, D.cn)로 만든다.
 카드: {id, u, t(원문), r(로마자), en, zh, ko, ja, s(출처 c=말뭉치/d=사전)}
 단원: 말뭉치는 영어 번역 키워드로 주제 분류, 사전 단어는 HSK 빈도 단계별.
 한국어 뜻(ko): Tatoeba 한국어 번역이 있으면 그것, 없으면 (a) 같은 영어·중국어에 연결된 기존 한국어 카드가 있으면 그 뜻, 없으면 비움.
build.py 에서 build_yn(C, t2s) 로 호출."""
import json, re, os, collections, sys

T = 'C:/Users/gjrns/AppData/Local/Temp/tat/'
YUE_RAW = T + 'yue_cards_raw.json'
NAN_RAW = T + 'nan_cards_raw.json'
NAN_W = T + 'nan_words_raw.json'

TOPICS = [
 ('q',  '질문·요청',   '🙋', 1, r'(\?|please|could you|can you|would you|how (much|many|long|do)|where|what time|do you know)'),
 ('hl',  '건강·몸',     '💊', 1, r'(doctor|hospital|sick|ill\b|pain|hurt|headache|medicine|fever|cough|cold\b|tired|sleep|health)'),
 ('fd',  '음식·식사',   '🍽️', 2, r'(eat|ate|drink|food|dinner|lunch|breakfast|meal|restaurant|hungry|thirsty|coffee|tea|beer|rice|noodle|cook|taste|delicious|bread|meat|fish|fruit)'),
 ('mv',  '이동·장소',   '🚆', 2, r'(go to|went|come|arrive|leave|left|train|bus|taxi|station|airport|road|street|walk|drive|car\b|trip|travel|hotel|where is|map)'),
 ('sh',  '쇼핑·돈',     '🛒', 2, r'(buy|bought|sell|price|cost|cheap|expensive|money|pay|paid|shop|store|dollar|yuan|cash|bank)'),
 ('hm',  '집·가족',     '🏠', 3, r'(home|house|family|father|mother|parent|brother|sister|son\b|daughter|wife|husband|child|baby|friend|neighbor|room\b|clean)'),
 ('fl',  '감정·의견',   '💬', 3, r'(love|like|hate|happy|sad|angry|afraid|worry|sorry|thank|think|feel|hope|miss|glad|surprised|funny|interesting)'),
 ('wk',  '일·학교',     '📘', 4, r'(work|job|office|company|boss|meeting|school|study|learn|teacher|student|class|exam|homework|read|write|book|language)'),
 ('wt',  '날씨·자연',   '🌤️', 3, r'(weather|rain|snow|wind|hot\b|cold\b|warm|cool|sun\b|sky|sea\b|mountain|flower|tree|river|season)'),
 ('dl',  '일상 대화',   '🗣️', 3, r'(today|tomorrow|yesterday|morning|night|evening|every day|always|never|often|sometimes|time|week|year|already|just now)'),
]
def topic(en, text):
    s = (en or '').lower()
    for k, n, e, tier, rx in TOPICS:
        if re.search(rx, s): return k
    return 'xx'
UN = {k: (n, e, tier) for k, n, e, tier, _ in TOPICS}
UN['xx'] = ('그 밖의 생활 문장', '📝', 4)
UN['dw'] = ('기본 단어 (사전)', '📖', 2)

def build_yn(C, t2s):
    from ToJyutping import get_jyutping_text as jp
    # 기존 한국어 카드의 영어/중국어를 색인해 한국어 뜻 보강
    ko_by_en = {}; ko_by_zh = {}
    for c in C:
        ko_by_en[re.sub(r'\W', '', c['en'].lower())] = c['ko']
        ko_by_zh[re.sub(r'[\W]', '', c['zh'])] = c['ko']
    cy = []; cn = []

    def ko_for(en, zh, ko):
        if ko: return ko, 'c'
        k = ko_by_en.get(re.sub(r'\W', '', (en or '').lower()))
        if k: return k, 'm'
        k = ko_by_zh.get(re.sub(r'[\W]', '', t2s(zh or '')))
        if k: return k, 'm'
        return '', ''

    # ----- 광동어 -----
    if os.path.exists(YUE_RAW):
        for i, c in enumerate(json.load(open(YUE_RAW, encoding='utf8'))):
            t = c['text']
            try: r = jp(re.sub(r'[A-Za-z][A-Za-z0-9]*', lambda m: m.group(0), t))
            except Exception: r = ''
            if not r or re.search(r'[\u4e00-\u9fff]', r) or '[…]' in r: continue
            ko, ks = ko_for(c['en'], c['zh'], c['ko'])
            cy.append(dict(id=200000 + i, u=topic(c['en'], t), t=t, r=r, en=c['en'], zh=c['zh'], ko=ko, ks=ks, ja=c['ja'], s='c'))
    # ----- 대만어 -----
    if os.path.exists(NAN_RAW):
        for i, c in enumerate(json.load(open(NAN_RAW, encoding='utf8'))):
            ko, ks = ko_for(c['en'], c['zh'], c['ko'])
            if re.search(r'[一-鿿]', c['rom']): continue          # 변환기가 못 읽는 글자가 남은 문장은 제외
            if re.search(r'[A-Za-z]{2,}', re.sub(r'[A-Za-z]*[āáǎàâēéěèêīíǐìîōóǒòôūúǔùûa-zA-Z̀-ͯⁿ]+', '', c['text'])) and c['kind'] == 'hanzi': pass
            cn.append(dict(id=300000 + i, u=topic(c['en'], c['text']), t=c['text'], r=c['rom'], en=c['en'], zh=c['zh'], ko=ko, ks=ks, ja=c['ja'], s='c', k=c['kind']))
    if os.path.exists(NAN_W):
        for i, w in enumerate(json.load(open(NAN_W, encoding='utf8'))):
            if not w['exact'] or w['n'] > 2: continue           # 한자 구성이 같고 대응이 거의 하나뿐인 것만
            if len(re.findall(r'[一-鿿]', w['text'])) < 2: continue   # 한 글자는 뜻이 어긋나기 쉬워 제외
            if re.search(r'surname|variant of|abbr|classifier|CL:|^see |used in|Taiwan|city in|town in|county|district|province|sb|sth|old variant|archaic|Japanese|Cantonese', w['en'], re.I): continue
            if re.search(r'[A-Za-z&#]', w['text']): continue
            ko, ks = ko_for(w['en'], w['zh'], '')
            cn.append(dict(id=310000 + i, u='dw', t=w['text'], r=w['rom'], en=w['en'], zh=w['zh'], ko=ko, ks=ks, ja='', s='d', k='hanzi'))
    # 중복 제거
    def dedup(lst):
        seen = set(); out = []
        for c in lst:
            k = re.sub(r'\W', '', c['t'].lower())
            if k in seen: continue
            seen.add(k); out.append(c)
        return out
    cy = dedup(cy); cn = dedup(cn)
    units_y = [dict(k='y_' + k, n=UN[k][0], e=UN[k][1], t=UN[k][2]) for k in dict.fromkeys(c['u'] for c in cy)]
    units_n = [dict(k='n_' + k, n=UN[k][0], e=UN[k][1], t=UN[k][2]) for k in dict.fromkeys(c['u'] for c in cn)]
    for c in cy: c['u'] = 'y_' + c['u']
    for c in cn: c['u'] = 'n_' + c['u']
    units_y.sort(key=lambda u: (u['t'], u['n'])); units_n.sort(key=lambda u: (u['t'], u['n']))
    return dict(cy=cy, cn=cn, uy=units_y, un=units_n)
