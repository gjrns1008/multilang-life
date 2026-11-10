# -*- coding: utf-8 -*-
"""다국어 학습 앱 데이터 빌더: 문장(한/일/영/중/우한) + 발음 표기 생성 -> index.html"""
import json, re, os, sys
from pypinyin import pinyin, Style, load_phrases_dict, load_single_dict
from korean_romanizer.romanizer import Romanizer
import pykakasi

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 우한말 글자 읽기 보정 (표준 병음 근사) ----
load_single_dict({ord('冇'): 'mǎo', ord('哒'): 'dá', ord('咯'): 'gè'})
load_phrases_dict({'么事': [['mǒ'], ['shì']], '晓得': [['xiǎo'], ['dei']]})

kks = pykakasi.kakasi()

UNITS = [
 # key, 이름, 이모지, 단계(tier)
 ("greet",  "인사",            "👋", 1),
 ("basic",  "기본 응답",       "🙏", 1),
 ("survive","못 알아들을 때",  "🆘", 1),
 ("num",    "숫자",            "🔢", 1),
 ("medical","병원·응급",       "🏥", 1),
 ("money",  "가격·결제",       "💳", 2),
 ("food",   "식당·주문",       "🍜", 2),
 ("trans",  "길 찾기·교통",    "🚇", 2),
 ("shop",   "쇼핑",            "🛍️", 2),
 ("lodge",  "숙소",            "🏨", 2),
 ("intro",  "자기소개",        "🙋", 3),
 ("time",   "시간·약속",       "⏰", 3),
 ("feel",   "감정·대화",       "💬", 3),
 ("work",   "직장·학업",       "💼", 4),
]
TIERS = {1: "1단계 · 생존 (제일 먼저)", 2: "2단계 · 여행·생활", 3: "3단계 · 사람·관계", 4: "4단계 · 직장·학업"}

# 형식: (unit, ko, ja, ja읽기(히라가나; 조사 は/を/へ는 앞에 % 표시), en, zh, wu 또는 None)
C = []
def add(u, ko, ja, jr, en, zh, wu=None, m=None):
    C.append(dict(u=u, ko=ko, ja=ja, jr=jr, en=en, zh=zh, wu=wu, m=m))

# 1 인사
add("greet","안녕하세요.","こんにちは。","こんにち%は","Hello.","你好。","你好啊。")
add("greet","안녕히 가세요.","さようなら。","さようなら","Goodbye.","再见。","慢走哈。")
add("greet","좋은 아침이에요.","おはようございます。","おはよう|ございます","Good morning.","早上好。","早啊。")
add("greet","안녕히 주무세요.","おやすみなさい。","お|やすみ|なさい","Good night.","晚安。")
add("greet","처음 뵙겠습니다.","はじめまして。","はじめまして","Nice to meet you.","初次见面。")
add("greet","잘 지내세요?","お元気ですか？","お|げんきですか","How are you?","你最近怎么样？","你最近么样啊？")
add("greet","잘 지내요, 고마워요.","元気です、ありがとう。","げんきです|、|ありがとう","I'm fine, thank you.","我很好，谢谢。","我蛮好，谢谢哈。")
add("greet","식사하셨어요?","ごはんは食べましたか？","ごはん%はたべましたか","Have you eaten yet?","你吃饭了吗？","你吃哒冇？")
add("greet","오랜만이에요.","お久しぶりです。","お|ひさしぶりです","Long time no see.","好久不见。","好久冇见哒。")
# 2 기본 응답
add("basic","네.","はい。","はい","Yes.","是的。","对头。")
add("basic","아니요.","いいえ。","いいえ","No.","不是。")
add("basic","감사합니다.","ありがとうございます。","ありがとう|ございます","Thank you.","谢谢。")
add("basic","천만에요.","どういたしまして。","どう|いたしまして","You're welcome.","不客气。","莫客气。")
add("basic","미안합니다.","ごめんなさい。","ごめん|なさい","I'm sorry.","对不起。")
add("basic","실례합니다.","すみません。","すみません","Excuse me.","打扰一下。")
add("basic","괜찮아요.","大丈夫です。","だいじょうぶです","It's okay.","没关系。","冇得事。")
add("basic","부탁드립니다.","お願いします。","お|ねがい|します","Please.","麻烦你了。")
# 3 못 알아들을 때
add("survive","모르겠어요.","わかりません。","わかりません","I don't know.","我不知道。","我不晓得。")
add("survive","알겠어요.","わかりました。","わかりました","I understand.","我明白了。","晓得哒。")
add("survive","천천히 말씀해 주세요.","ゆっくり話してください。","ゆっくり|はなして|ください","Please speak slowly.","请说慢一点。","讲慢点哈。")
add("survive","한 번 더 말씀해 주세요.","もう一度お願いします。","もう|いち|ど|お|ねがい|します","Could you say that again?","请再说一遍。","再讲一遍哈。")
add("survive","영어 할 수 있어요?","英語は話せますか？","えいご%ははなせますか","Do you speak English?","你会说英语吗？","你会不会讲英语啊？")
add("survive","도와주세요!","助けてください！","たすけて|ください","Help me!","请帮帮我！","帮个忙哈！")
add("survive","이게 뭐예요?","これは何ですか？","これ%はな|んですか","What is this?","这是什么？","咯是么事？")
add("survive","화장실이 어디예요?","トイレはどこですか？","トイレ%はどこですか","Where is the restroom?","厕所在哪里？","厕所在哪块？")
# 4 숫자 (m = 표시할 뜻)
NUM = [("일","一","いち","one","一"),("이","二","に","two","二"),("삼","三","さん","three","三"),("사","四","よん","four","四"),
       ("오","五","ご","five","五"),("육","六","ろく","six","六"),("칠","七","なな","seven","七"),("팔","八","はち","eight","八"),
       ("구","九","きゅう","nine","九"),("십","十","じゅう","ten","十"),("백","百","ひゃく","hundred","百"),
       ("천","千","せん","thousand","千"),("만","万","まん","ten thousand","万")]
for i,(ko,ja,jr,en,zh) in enumerate(NUM):
    mm = ["1","2","3","4","5","6","7","8","9","10","100","1,000","10,000"][i]
    add("num",ko,ja,jr,en,zh,zh,m=mm)
# 5 병원·응급
add("medical","아파요.","痛いです。","いたいです","It hurts.","我疼。","我痛。")
add("medical","머리가 아파요.","頭が痛いです。","あたま|が|いたいです","I have a headache.","我头疼。","我头痛。")
add("medical","배가 아파요.","お腹が痛いです。","おなか|が|いたいです","I have a stomachache.","我肚子疼。","我肚子痛。")
add("medical","열이 나요.","熱があります。","ねつ|が|あります","I have a fever.","我发烧了。","我发烧哒。")
add("medical","병원에 가고 싶어요.","病院に行きたいです。","びょういん|に|いきたいです","I need to go to a hospital.","我要去医院。")
add("medical","구급차를 불러 주세요.","救急車を呼んでください。","きゅうきゅう|しゃ%をよんで|ください","Please call an ambulance.","请叫救护车。","快喊救护车。")
add("medical","약국이 어디예요?","薬局はどこですか？","やっ|きょく%はどこですか","Where is the pharmacy?","药店在哪里？","药店在哪块？")
add("medical","여권을 잃어버렸어요.","パスポートをなくしました。","パスポート%をなくしました","I lost my passport.","我的护照丢了。","我的护照丢哒。")
add("medical","경찰을 불러 주세요.","警察を呼んでください。","けいさつ%をよんで|ください","Please call the police.","请叫警察。","快喊警察。")
# 6 가격·결제
add("money","이거 얼마예요?","これはいくらですか？","これ%はいくらですか","How much is this?","这个多少钱？","咯个几多钱？")
add("money","너무 비싸요.","高すぎます。","たか|すぎます","It's too expensive.","太贵了。","太贵哒。")
add("money","좀 깎아 주세요.","少し安くなりませんか？","すこしやすく|なりませんか","Can you lower the price?","便宜一点吧。","便宜点嘛。")
add("money","카드 돼요?","カードは使えますか？","カード%はつかえますか","Can I pay by card?","可以刷卡吗？","可以刷卡不？")
add("money","현금으로 낼게요.","現金で払います。","げんきんで|はらいます","I'll pay in cash.","我付现金。")
add("money","영수증 주세요.","レシートをください。","レシート%をください","Receipt, please.","请给我小票。")
# 7 식당
add("food","메뉴판 주세요.","メニューを見せてください。","メニュー%をみせて|ください","Can I see the menu?","请给我菜单。","拿菜单给我看哈。")
add("food","이걸로 주세요.","これをください。","これ%をください","I'll have this one.","我要这个。","我要咯个。")
add("food","물 주세요.","お水をください。","お|みず%をください","Water, please.","请给我水。","给我点水哈。")
add("food","맛있어요!","おいしい！","おいしい","It's delicious!","真好吃！","好吃得很！")
add("food","맵지 않게 해 주세요.","辛くしないでください。","からく|しないで|ください","Not spicy, please.","请不要放辣。","莫放辣椒哈。")
add("food","계산해 주세요.","お会計をお願いします。","お|かい|けい|を|お|ねがい|します","The check, please.","买单。","买单哈。")
add("food","포장해 주세요.","持ち帰りでお願いします。","もちかえりで|お|ねがい|します","To go, please.","打包。","打包哈。")
add("food","배고파요.","お腹がすきました。","おなか|が|すきました","I'm hungry.","我饿了。","我饿哒。")
add("food","목말라요.","のどが渇きました。","のど|が|かわきました","I'm thirsty.","我渴了。","我渴哒。")
add("food","두 명이에요.","二人です。","ふたりです","A table for two.","两个人。")
add("food","알레르기가 있어요.","アレルギーがあります。","アレルギー|が|あります","I have an allergy.","我过敏。")
# 8 길 찾기·교통
add("trans","지하철역이 어디예요?","地下鉄の駅はどこですか？","ちか|てつ|の|えき%はどこですか","Where is the subway station?","地铁站在哪里？","地铁站在哪块？")
add("trans","여기서 멀어요?","ここから遠いですか？","ここ|から|とおいですか","Is it far from here?","离这里远吗？","离咯块远不远啊？")
add("trans","쭉 가세요.","まっすぐ行ってください。","まっすぐ|いって|ください","Go straight.","一直走。")
add("trans","왼쪽으로 가세요.","左に曲がってください。","ひだり|に|まがって|ください","Turn left.","向左转。","往左边拐。")
add("trans","오른쪽으로 가세요.","右に曲がってください。","みぎ|に|まがって|ください","Turn right.","向右转。","往右边拐。")
add("trans","여기서 세워 주세요.","ここで止めてください。","ここで|とめて|ください","Please stop here.","请在这里停车。","就在咯块停哈。")
add("trans","택시 불러 주세요.","タクシーを呼んでください。","タクシー%をよんで|ください","Please call a taxi.","请帮我叫出租车。","帮我喊个的士。")
add("trans","표 한 장 주세요.","切符を一枚ください。","きっぷ%をいちまい|ください","One ticket, please.","请给我一张票。")
add("trans","몇 시에 출발해요?","何時に出発しますか？","なん|じ|に|しゅっぱつ|しますか","What time does it leave?","几点出发？","几点钟走啊？")
# 9 자기소개
add("intro","제 이름은 ○○입니다.","私の名前は○○です。","わたし|の|なまえ%は○|○です","My name is ○○.","我叫○○。")
add("intro","저는 한국 사람이에요.","私は韓国人です。","わたし%はかんこくじんです","I'm Korean.","我是韩国人。")
add("intro","어디에서 오셨어요?","どちらから来ましたか？","どちら|から|きましたか","Where are you from?","你是哪里人？","你是哪块的人啊？")
add("intro","몇 살이에요?","何歳ですか？","なんさいですか","How old are you?","你多大了？","你多大哒？")
add("intro","무슨 일을 하세요?","お仕事は何ですか？","お|しごと%はな|んですか","What do you do?","你做什么工作？","你搞么事工作啊？")
add("intro","저는 학생이에요.","私は学生です。","わたし%はがくせいです","I'm a student.","我是学生。")
add("intro","만나서 반갑습니다.","お会いできて嬉しいです。","お|あい|できて|うれしいです","Nice to meet you.","很高兴认识你。","认得你蛮高兴。")
add("intro","저는 중국어를 공부하고 있어요.","私は中国語を勉強しています。","わたし%はちゅうごくご%をべんきょう|して|います","I'm studying Chinese.","我在学汉语。")
# 10 시간·약속
add("time","지금 몇 시예요?","今何時ですか？","い|まなんじですか","What time is it?","现在几点了？","现在几点哒？")
add("time","오늘","今日","きょう","today","今天")
add("time","내일","明日","あした","tomorrow","明天")
add("time","어제","昨日","きのう","yesterday","昨天")
add("time","몇 시에 만날까요?","何時に会いましょうか？","なん|じ|に|あいましょうか","What time shall we meet?","我们几点见面？","我们几点钟碰头？")
add("time","늦었어요.","遅れました。","おくれました","I'm late.","我迟到了。","我迟到哒。")
add("time","잠깐만요.","ちょっと待ってください。","ちょっと|まって|ください","Just a moment.","请稍等。","等哈。")
add("time","빨리 해 주세요.","急いでください。","いそいで|ください","Please hurry.","请快一点。","搞快点哈。")
# 11 쇼핑
add("shop","그냥 구경하는 거예요.","見ているだけです。","みて|いる|だけです","I'm just looking.","我随便看看。","我随便看哈。")
add("shop","입어 봐도 돼요?","試着してもいいですか？","しちゃく|して|も|いいですか","Can I try this on?","可以试穿吗？","可以试哈不？")
add("shop","더 큰 사이즈 있어요?","もっと大きいサイズはありますか？","もっと|おおきい|サイズ%はありますか","Do you have a bigger size?","有大一点的吗？","有冇大点的？")
add("shop","다른 색 있어요?","他の色はありますか？","ほか|の|いろ%はありますか","Do you have another color?","有别的颜色吗？","有冇别的颜色？")
add("shop","환불돼요?","返品できますか？","へんぴ|ん|できますか","Can I get a refund?","可以退货吗？","可以退不？")
# 12 숙소
add("lodge","예약했어요.","予約しました。","よ|やくしました","I have a reservation.","我预订了。","我订哒。")
add("lodge","빈 방 있어요?","部屋は空いていますか？","へや%はあいて|いますか","Do you have a room?","有房间吗？","有冇房？")
add("lodge","와이파이 비밀번호가 뭐예요?","Wi-Fiのパスワードは何ですか？","ワイファイ|%|の|パスワード%はな|んですか","What's the Wi-Fi password?","WiFi密码是多少？","WiFi密码是么事啊？")
add("lodge","체크아웃은 몇 시예요?","チェックアウトは何時ですか？","チェックアウト%はなんじですか","What time is checkout?","几点退房？","几点钟退房啊？")
add("lodge","에어컨이 안 돼요.","エアコンが動きません。","エアコン|が|うごきません","The air conditioner doesn't work.","空调坏了。","空调坏哒。")
add("lodge","수건 하나 더 주세요.","タオルをもう一枚ください。","タオル%をもう|いちまい|ください","One more towel, please.","请再给我一条毛巾。","再拿条毛巾给我哈。")
# 13 감정·대화
add("feel","좋아해요.","好きです。","すきです","I like it.","我喜欢。")
add("feel","재미있어요.","面白いです。","おもしろいです","It's fun.","很有意思。","蛮好玩。")
add("feel","피곤해요.","疲れました。","つかれました","I'm tired.","我累了。","我累哒。")
add("feel","정말요?","本当ですか？","ほんとうですか","Really?","真的吗？","真的啊？")
add("feel","걱정하지 마세요.","心配しないでください。","しんぱい|しないで|ください","Don't worry.","别担心。","莫担心。")
add("feel","보고 싶어요.","会いたいです。","あいたいです","I miss you.","我想你。")
add("feel","사랑해요.","愛してる。","あい|してる","I love you.","我爱你。")
add("feel","축하해요!","おめでとう！","お|めでとう","Congratulations!","恭喜！","恭喜哈！")
add("feel","건배!","乾杯！","かんぱい","Cheers!","干杯！")
# 14 직장·학업
add("work","회의가 있어요.","会議があります。","かいぎ|が|あります","I have a meeting.","我有个会。")
add("work","이메일 보낼게요.","メールを送ります。","メール%をおくります","I'll send you an email.","我给你发邮件。","我发邮件给你。")
add("work","질문이 있어요.","質問があります。","しつもん|が|あります","I have a question.","我有个问题。")
add("work","도와줘서 고마워요.","助けてくれてありがとう。","たすけて|くれて|ありがとう","Thanks for your help.","谢谢你的帮忙。","谢谢你帮忙哈。")
add("work","수고하셨어요.","お疲れさまでした。","お|つかれさまでした","Good work today.","辛苦了。","辛苦哒。")

# 우한말 핵심 단어: (우한말, 표준어, 한국어 뜻, 메모, 읽기용 표준어)
WORDS = [
 ("过早","吃早饭","아침 식사를 하다","우한 사람들의 아침 식사 문화. 「过早」는 우한 고유 표현이에요.","吃早饭"),
 ("热干面","热干面","우한 대표 비빔국수(참깨장 소스)","우한 아침 식사의 대표 메뉴.","热干面"),
 ("么事","什么","무엇","「么事」(mǒ shì)=什么. 「搞么事」=무엇을 해?","什么事"),
 ("咯","这","이(것)","「咯个」=这个. 「咯块」=这里.","这"),
 ("哒","了","~했다 (완료 조사)","「吃哒」=吃了. 「来哒」=来了.","了"),
 ("冇","没有","없다 / 안 ~했다","「冇得」=没有. 「冇得事」=没事. 우한·후베이에서 많이 써요.","没有"),
 ("晓得","知道","알다","「不晓得」=不知道. 「晓得哒」=알겠어요.","知道"),
 ("蛮","很","매우","「蛮好」=很好. 「蛮好吃」=很好吃.","很"),
 ("莫","别","~하지 마","「莫急」=别急. 「莫客气」=别客气.","别"),
 ("搞","做","하다 (가장 만능 동사)","「搞么事」=做什么. 「搞快点」=快一点.","做"),
 ("要得","行 / 好的","좋아요, 되요","「要得」=可以/好的. 동의할 때 자주 써요.","行"),
 ("哪块","哪里","어디","「哪块」=哪里. 「厕所在哪块?」","哪里"),
 ("几多","多少","얼마나(수량)","「几多钱」=多少钱.","多少"),
 ("么样","怎么样","어떻게 / 어때","「么样啊?」=怎么样啊?","怎么样"),
 ("哪个","谁","누구","표준어의 「哪个」(어느 것)와 달리 우한에서는 「谁」 뜻으로도 써요.","谁"),
 ("困觉","睡觉","잠자다","「困」=자다.","睡觉"),
 ("硬是","真是 / 确实","정말, 진짜","「硬是好吃」=정말 맛있다.","真是"),
 ("哈","一下","좀, 잠깐 (가볍게 ~해봐)","「等哈」=等一下. 문장 끝 「哈」는 부드러운 어조.","一下"),
 ("豆皮","豆皮","두피 (찹쌀·고기를 넣은 얇은 계란/두부피 요리)","우한 대표 아침 메뉴.","豆皮"),
 ("糊汤粉","糊汤粉","후탕펀 (생선 국물 쌀국수)","우한 전통 아침 메뉴.","糊汤粉"),
 ("面窝","面窝","미엔워 (도넛 모양 튀김)","우한 길거리 아침 간식.","面窝"),
]

import extra
UNITS.extend(extra.EXTRA_UNITS)
extra.load(add)
WORDS.extend(extra.EXTRA_WORDS)
import extra2
import extra3
UNITS.extend(extra3.EXTRA_UNITS3)
UNITS.extend(extra2.EXTRA_UNITS2)
UNITS.append(("dict","사전 기본 어휘 (빈도순)","📖",4))
extra2.load2(add)
WORDS.extend(extra2.EXTRA_WORDS2)
_seen=set(); _w=[]
for _x in WORDS:
    if _x[0] in _seen: continue
    _seen.add(_x[0]); _w.append(_x)
WORDS[:]=_w

def zh_py(t):
    t = re.sub(r'[。，、？！]', lambda m: {'。':'.','，':',','、':',','？':'?','！':'!'}[m.group(0)], t)
    out = []
    for p in pinyin(t, style=Style.TONE, errors=lambda x: [x]):
        out.append(p[0])
    s = ' '.join(out)
    s = re.sub(r'\s+([.,?!])', r'\1', s)
    return s

def ko_rom(t):
    t = t.replace('○○', '이름')
    try: r = Romanizer(t).romanize()
    except Exception: r = ''
    return r.replace('ireum', 'OO') if '○○' in t else r

PART = {'は': 'wa', 'を': 'o', 'へ': 'e'}
# 문절 단위 로마자: 형태소 분석(fugashi) 결과를 문절로 묶는다.
#  - 조사(は를が에で...)는 앞 단어와 띄어 쓰고, 助動詞·接尾辞·活用語尾는 앞 말에 붙인다.
#  - 명사+명사(複合語)는 붙인다.
import fugashi
_tag = fugashi.Tagger()
_PARTICLE = {'は','を','へ','が','に','で','も','の','と','から','まで','や','より'}
def _bunsetsu(t):
    """형태소 분석 결과를 문절 단위로 묶는다. 각 원소: [표면형, 품사]"""
    out = []
    for w in _tag(t):
        sf, pos = w.surface, w.feature.pos1
        if not out:
            out.append([sf, pos]); continue
        prev_pos = out[-1][1]
        attach = False
        if pos in ('助動詞', '接尾辞'):
            attach = True
        elif pos == '助詞' and sf not in _PARTICLE:
            attach = True
        elif pos in ('名詞', '接頭辞') and prev_pos in ('名詞', '接頭辞'):
            attach = True
        if attach:
            out[-1][0] += sf
            if pos == '名詞': out[-1][1] = '名詞'
        else:
            out.append([sf, pos])
    return [o[0] for o in out]

def ja_rom(h):
    toks = []; pos = 0
    for m in re.finditer(r'%([はをへ])', h):
        toks.append(('t', h[pos:m.start()])); toks.append(('p', PART[m.group(1)])); pos = m.end()
    toks.append(('t', h[pos:]))
    parts = []
    for kind, t in toks:
        if kind == 'p': parts.append(t); continue
        t = t.replace('○○', 'ほげ').replace('%', '')
        t = re.sub(r'[ 　|]+', '', t)
        if not t: continue
        for piece in _bunsetsu(t):
            parts.append(''.join(x['hepburn'] for x in kks.convert(piece)).replace('hoge', 'OO'))
    return re.sub(r'\s+', ' ', ' '.join(parts)).strip()

def run():
    import dialects as DL, dialect_sentences as DS
    # ---- 말뭉치(Tatoeba) 문장 카드 ----
    import jautil
    side3 = {}
    tp = r'C:/Users/gjrns/AppData/Local/Temp/tat/tat_verified2.json'
    if os.path.exists(tp):
        extra3.TAT = tp
        n3, side3 = extra3.load3(add, set(c['ko'] for c in C), jautil.romanize, DL._t2s.convert)
        print('corpus sentences added', n3)
    # ---- 사전 기반 확장 단어(중·일·한 한자 일치 + 영어 뜻 교차 검증) ----
    vp = r'C:/Users/gjrns/AppData/Local/Temp/dict/vocab_verified.json'
    if os.path.exists(vp):
        have = set(c['zh'] for c in C)
        voc = json.load(open(vp, encoding='utf8'))
        voc.sort(key=lambda x: (x['lv'], x['q']))
        extra_n = 0
        for v in voc:
            zhs = DL._t2s.convert(v['t'])
            if zhs in have or len(zhs) > 4 or len(zhs) < 2: continue   # 한 글자는 한·중·일 뜻이 어긋나기 쉬워 제외
            ko = v['ko'] if not v['ko'].endswith('하다') else v['ko']
            if any(c['ko'] == ko for c in C): continue
            en = re.sub(r'\s*\(.*?\)', '', v['en'][0]).split(';')[0].strip()
            if not en or len(en) > 40: continue
            if re.search(r'surname|variant of|abbr\.|used in|classifier|CL:|see also|Taiwan pr|old variant|archaic|dialect|Japanese|Cantonese|diminutive|\bsb\b|\bsth\b', en, re.I): continue
            if len(DL._han(v['t'])) < 2 and en.split()[0] in ('to', 'a', 'the') : continue
            unit = 'adv' if False else 'dict'
            add(unit, ko, v['ja'], v['jr'], en, zhs, None)
            have.add(zhs); extra_n += 1
        print('dictionary-verified words added', extra_n)
    for i, c in enumerate(C):
        c['id'] = i
        c['r'] = {
            'ko': ko_rom(c['ko']) if '○○' not in c['ko'] else '',
            'jh': re.sub(r'[ 　|]+','',c['jr'].replace('%','')),
            'jr': (jautil.romanize(c['ja'])[1] if c['u'].startswith('t_') else (ja_rom(c['jr']) if '○○' not in c['jr'] else ja_rom(c['jr']))),
            'zh': zh_py(c['zh']),
            'wu': zh_py(c['wu']) if c['wu'] else '',
        }
        if '○○' in c['ko']:
            c['r']['ko'] = 'je ireumeun OO imnida'
        del c['jr']
        # ---- 대만어·광동어 ----
        sd = side3.get(c['ko'])
        if sd:
            tw = sd['tw'] if sd['tw'] and re.search(r'[\u4e00-\u9fff]', sd['tw']) else None
            yue = sd['yue']
            tws = 'c' if tw else ''; yues = 'c' if yue else ''
        else:
            tw, yue, tws, yues = DL.make(c, DS.TW, DS.YUE)
        if tw: 
            c['tw'] = tw; c['tws'] = tws
            c['r']['tw'] = DL.tl(tw) if tws in ('m', 'c') else (c.pop('_twr', '') or DL.tl(tw))
        if yue:
            c['yue'] = yue; c['yues'] = yues
            c['r']['yue'] = DL.jp(yue) if yues in ('m', 'c') else (c.pop('_yuer', '') or DL.jp(yue))
        c.pop('_twr', None); c.pop('_yuer', None)
    words = []
    for j, (wu, zh, ko, note, sp) in enumerate(WORDS):
        words.append(dict(id=100000 + j, wu=wu, zh=zh, ko=ko, note=note, sp=sp, py=zh_py(wu)))
    import yn
    YN = yn.build_yn(C, DL._t2s.convert)
    print('standalone Cantonese', len(YN['cy']), 'Taiwanese', len(YN['cn']))
    # 독립 카드를 기존 카드 구조에 맞춰 D.c 에 합친다. 필드: ko, ja, en, zh 가 비어 있을 수 있어 "표시 가능한 값"으로 채운다.
    def to_card(x, lang):
        c = dict(id=x['id'], u=x['u'], ko=x['ko'], en=x['en'], zh=x['zh'] or '', ja=x['ja'] or '', wu=None, L=lang, s=x['s'], ks=x.get('ks', ''))
        c['r'] = dict(ko='', jh='', jr='', zh=zh_py(c['zh']) if c['zh'] else '', wu='')
        c[lang] = x['t']; c['r'][lang] = x['r']
        if lang == 'yue': c['yue'] = x['t']; c['yues'] = 'c'
        if lang == 'tw':  c['tw'] = x['t'];  c['tws'] = 'c' if x['s'] == 'c' else 'd'
        return c
    for x in YN['cy']: C.append(to_card(x, 'yue'))
    for x in YN['cn']: C.append(to_card(x, 'tw'))
    UNITS.extend((u['k'], u['n'], u['e'], u['t']) for u in YN['uy'])
    UNITS.extend((u['k'], u['n'], u['e'], u['t']) for u in YN['un'])
    data = dict(units=[dict(k=k, n=n, e=e, t=t) for k, n, e, t in UNITS], tiers=TIERS, c=C, words=words)
    tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    html = tpl.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False))
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(html)
    n_tw = sum(1 for c in C if c.get('tw')); n_yue = sum(1 for c in C if c.get('yue'))
    print('concepts', len(C), 'words', len(words), 'tw', n_tw, 'yue', n_yue, 'bytes', len(html.encode('utf-8')))

if __name__ == '__main__':
    run()
