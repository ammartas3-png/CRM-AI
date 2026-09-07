# CRM Status Eğitim Kılavuzu

**Ne olunca hangi status?** — Agent / reviewer el kitabı

Bu rehber CRM’e status girerken doğru kararı vermen için yazıldı. Teknik sistem detayı değil; yorum satırını okuyup “bu lead’e ne koyarım?” sorusuna cevap verir.

**Altın kural:** En yeni anlamlı **müşteri** cümlesine bak. Agent’ın kendi arama notunu (`cb:vm`, `cb na`, `call again rej`) müşteri talebi sanma.

---

## 1. Önce bu sırayla bak (öncelik ağacı)

Yukarıdan aşağıdır. Üstteki durum varsa alttakine bakma.

1. Kimlik inkârı (“ben Ahmad değilim”, “wrong person”, “this is not me”) → **Denied Registration**
2. Dil bariyeri (Mandarin / Arapça / hard time in English) ve kimlik inkârı yok → **No Language**
3. 18 yaş altı / geçersiz ülke → **Under 18** / **Invalid Country**
4. Para yok + uzak/belirsiz/çıkış (`next month`, `by October`, `not serious`, `discontinue`) → **No Potential**
5. Para yok AMA yakın plan (maaş yakında, arrange funds, arkadaş yardımı) → **Call Again**
6. Evrak/ID/banka yok → **No Potential - no documents**
7. En yeni cümlede net red → **Recall** (1. gün) veya **No Interest** (2. gün)
8. Müşteri net geri arama istedi → **Call Again**
9. Sadece çalma / VM / NA / ring / dvm → **No Answer 1-5** (5+ ayrı gün → **No Answer 5 UP**)
10. Karışık / anlaşılmaz → **Manual Check**

---

## 2. Status sözlüğü

### 2.1 Call Again — takip et, henüz ölmedi
Müşteri kapıyı kapatmadı. Net devam / randevu / kısa vadeli para planı var.

**Koy**
- call me later / tomorrow / at 6pm / I’m busy, call back
- no money NOW ama until salary / will arrange funds / ask friends / will get help and deposit
- pu said to call him later

**Koyma**
- next month / by October / in 4 months / don’t know when → **No Potential**
- `cb:vm`, `cb na`, `call again rej` → agent notu, müşteri CB değil
- dont think I’m interested → **Recall**
- i will do it by myself / dont need your help (red yok) → **Call Again** (kendi yatırmak istiyor, yardım istemiyor)
- CB REJS → genelde **No Answer**

### 2.2 Recall — bugün soğuk, yarın bir daha dene
Tek günde yumuşak veya net red; henüz kalıcı No Interest değil.

**Koy:** not interested (ilk gün), doesnt want to proceed, “didnt register” (kimlik inkârı yok)

**Koyma:** iki ayrı günde red → No Interest · küfür+istemiyorum → No Interest · aile çeviri/kart yardımı tek başına third_party değil

### 2.3 No Interest — kalıcı ilgisiz
- Red iki farklı günde **veya**
- Küfür + açık istemiyorum **veya**
- Recall sonrası 3 ayrı günde NA

Tek “not interested” → Recall. Tek `hu` → red sayılmaz.

### 2.4 No Potential — para/kapasite yolu kapalı
does not have the money + next month / by October / don’t know when / not serious / discontinue / capital affordable? no + hu / sadece email ile iletişim

**Call Again kalan soft örnekler:** salary in a few days · will get help and deposit · give me time to source

### 2.5 No Potential - no documents
no id / no documents / no bank / no POR. Bare “didnt register” buraya girmez → Recall.

### 2.6 No Answer 1-5
na / vm / dvm / ring / ndt / currently busy (konuşma yok).  
Invalid email olsa bile newest ring/NA → **No Answer** (Wrong Number değil).

### 2.7 No Answer 5 UP
5+ ayrı günde cevap yok.

### 2.8 No Language
Dil tutmuyor. Aynı cümlede kimlik inkârı varsa → **Denied Registration** (identity > language).

### 2.9 Denied Registration
Kimlik inkârı şart. 1. gün Denied · 2. gün tekrar → Wrong Number.  
“didnt register” yetmez → Recall. no id → NP-no documents.

### 2.10 Wrong Number or Email
Numara/email gerçekten yanlış veya 2. kimlik inkârı günü. Telefon canlıysa Invalid email → NA.

### 2.11 Under 18 / Invalid Country
Net sinyal varsa; tahmin etme.

### 2.12 Manual Check / Decline / Duplicate / DNC
Karışık intent → Manual Check. Decline/Duplicate/DNC operasyonel; yorumdan uydurma.

---

## 3. En çok karışanlar

| Soru | Cevap |
|---|---|
| Para yok, yakın plan var mı? | Evet → Call Again · Hayır/uzak → No Potential |
| “Beni ara” mı, “istemiyorum” mu? | Ara → CA · İstemiyorum → Recall |
| 1. red günü mü 2. mü? | 1 → Recall · 2 → No Interest |
| Telefon çalıyor mu? | Evet → NA · Ölü/wrong → Wrong Number |
| Dil mi, kimlik mi? | Sadece dil → No Language · “ben o değilim” → Denied |
| didnt register / no id / not me? | register→Recall · no id→NP-docs · not me→Denied |

---

## 4. Agent notu ≠ müşteri sözü

Bunlar agent’ın kendi kaydı — müşteri “beni ara” demiş sayılmaz:

`cb : vm` · `cb na` · `cb rej` · `call again rej` · `CALLED BACK PUHU` · `when I tried to cb she rejected`

Ayıkla, kalan müşteri cümlesine bak.

---

## 5. Cep kartı

| Gördüğün sinyal | Status |
|---|---|
| call me later / busy call back | Call Again |
| no money + salary soon / arrange | Call Again |
| no money + next month / October | No Potential |
| not interested (1. gün) | Recall |
| curse + istemiyorum | No Interest |
| im not [name] / wrong person | Denied Registration |
| Mandarin / no English (kimlik yok) | No Language |
| didnt register (kimlik yok) | Recall |
| no id / no bank / no POR | No Potential - no documents |
| na / vm / dvm / ring | No Answer 1-5 |
| invalid email + ring/NA | No Answer 1-5 |
| i will do it by myself / dont need your help | Call Again |
| CB REJS | No Answer (genelde) |
| emin değilim | Manual Check |

---

## 6. Mini senaryolar

| # | Yorum | Status |
|---|---|---|
| A | pu said to call him later | Call Again |
| B | does not have the money next month not sure | No Potential |
| C | no money until salary in a few days then will start | Call Again |
| D | not interested (ilk kez) | Recall |
| E | im not Ahmad please speak Arabic | Denied Registration |
| F | said i didnt register | Recall |
| G | Invalid email - CRM … (yeni) ring, dvm | No Answer 1-5 |
| H | i will do it by myself / dont need your help | Call Again |
| I | cb:vm + never reg and hung up | Recall |
| J | cant afford now but will get help and deposit | Call Again |

---

## 7. Sık hatalar

- next month → Call Again yapmak
- Agent `cb:vm` → Call Again yapmak
- Tek not interested → No Interest basmak
- didnt register = Denied sanmak
- Invalid email = Wrong Number (telefon ring iken)
- Soft money + maaş = No Potential yapmak
- Emin değilken status uydurmak (Manual Check kullan)

---

## 8. Sistem (bir cümle)

Telegram’a Excel atınca sistem **öneri** üretir; sen kontrol edip CRM’e **elle** girersin. Öneriyi bu kılavuza göre doğrula.

*Son güncelleme: Eylül 2026*
