# -*- coding: utf-8 -*-
"""원본 사전 -> 브라우저 검색용 JSON (다국어학습/dict/*.json). 각 행은 배열."""
import re, json, csv, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
T = 'C:/Users/gjrns/AppData/Local/Temp/dict/'
OUT = 'C:/Users/gjrns/Desktop/다국어학습/dict/'
os.makedirs(OUT, exist_ok=True)

def dump(name, rows):
    p = OUT + name
    json.dump(rows, open(p, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print(name, len(rows), round(os.path.getsize(p) / 1e6, 2), 'MB')

# ---- 병음 숫자 -> 성조 기호 ----
TONE = {'a': 'āáǎà', 'e': 'ēéěè', 'i': 'īíǐì', 'o': 'ōóǒò', 'u': 'ūúǔù', 'ü': 'ǖǘǚǜ'}
def syl(s):
    m = re.match(r'^([A-Za-z:ü]+?)([1-5])$', s)
    if not m: return s
    b, t = m.group(1).replace('u:', 'ü').replace('v', 'ü'), int(m.group(2))
    if t == 5: return b
    low = b.lower()
    pos = None
    for v in ('a', 'e'):
        if v in low: pos = low.index(v); break
    if pos is None:
        if 'ou' in low: pos = low.index('o')
        else:
            for i in range(len(low) - 1, -1, -1):
                if low[i] in 'aeiouü': pos = i; break
    if pos is None: return b
    ch = low[pos]
    nc = TONE[ch][t - 1]
    if b[pos].isupper(): nc = nc.upper()
    return b[:pos] + nc + b[pos + 1:]
def pin(s): return ' '.join(syl(x) for x in s.split())

# ---- CC-CEDICT ----
import zipfile
z = zipfile.ZipFile(T + 'cedict.zip')
rows = []
for line in z.read('cedict_ts.u8').decode('utf8').split('\n'):
    if line.startswith('#') or not line.strip(): continue
    m = re.match(r'(\S+) (\S+) \[(.*?)\] /(.*)/\s*$', line.strip())
    if not m: continue
    g = '; '.join(x for x in m.group(4).split('/') if x)[:160]
    rows.append([m.group(1), m.group(2), pin(m.group(3)), g])
dump('cedict.json', rows)

# ---- CC-Canto ----
rows = []
for line in open(T + 'canto.txt', encoding='utf8'):
    if line.startswith('#') or not line.strip(): continue
    m = re.match(r'(\S+) (\S+) \[(.*?)\] \{(.*?)\} /(.*)/\s*$', line.strip())
    if not m: continue
    rows.append([m.group(1), m.group(2), m.group(4), '; '.join(x for x in m.group(5).split('/') if x)[:160]])
dump('ccanto.json', rows)

# ---- JMdict ----
BADK = {'sK', 'rK', 'iK', 'oK', 'ik', 'io', 'ateji', 'sk', 'rk'}
jm = json.load(open(T + 'jm/jmdict-eng-3.6.2.json', encoding='utf8'))['words']
rows = []
for w in jm:
    ks = [k['text'] for k in sorted([k for k in w['kanji'] if not (set(k['tags']) & BADK)], key=lambda k: not k['common'])][:3]
    ka = [k['text'] for k in sorted(w['kana'], key=lambda k: not k['common'])][:2]
    gl = []
    for s in w['sense'][:3]:
        gl.append(', '.join(g['text'] for g in s['gloss'][:3]))
    c = 1 if any(k['common'] for k in w['kanji'] + w['kana']) else 0
    rows.append(['・'.join(ks), '・'.join(ka), ' / '.join(gl)[:170], c])
dump('jmdict.json', rows)

# ---- kengdic ----
rows = []
for line in open(T + 'kengdic.tsv', encoding='utf8').read().split('\n')[1:]:
    p = line.split('\t')
    if len(p) < 4: continue
    surf, hanja, gloss = p[1].strip(), p[2].strip(), (p[3] or '').strip()
    if not surf or not gloss: continue
    rows.append([surf, hanja, gloss[:120]])
dump('kengdic.json', rows)

# ---- 台華線頂對照典 (CC BY-SA 4.0) ----
rows = []
for r in csv.DictReader(open(T + 'taigi.csv', encoding='utf-8-sig')):
    han = r['HanLoTaibunKip'].strip(); kip = r['KipUnicode'].strip(); poj = r['PojUnicode'].strip(); hoa = r['HoaBun'].strip()
    if not (han or kip) or not hoa: continue
    rows.append([han, kip, poj, hoa[:100]])
dump('taigi.json', rows)
