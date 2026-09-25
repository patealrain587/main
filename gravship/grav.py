import csv, re, json, math, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
from collections import deque, defaultdict

CSV = os.path.join(HERE, "data", "facilities.csv")
ROWS = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
BYDEF = {r["defName"]: r for r in ROWS}

def spec(key):
    r = BYDEF.get(key)
    if r is None:
        m = [x for x in ROWS if x["이름"] == key]
        if not m: raise KeyError(key)
        r = m[0]
    w, h = map(int, r["크기"].split("x"))
    inter = None
    m = re.search(r"작업칸 \(\s*([-+]?\d+)\s*,\s*0\s*,\s*([-+]?\d+)\s*\)", r["특징"])
    if m:
        inter = (int(m.group(1)), int(m.group(2)))
        if inter == (0, 0): inter = None
    excl = None
    m = re.search(r"뒤 금지구역 \((\d+),\s*0,\s*(\d+)\)", r["중력선"])
    if m: excl = (int(m.group(1)), int(m.group(2)))
    power = 0.0
    pm = re.match(r"([-+]\d+) W", r["전력"])
    if pm: power = float(pm.group(1))
    act = r["실제 적용값(모드 설정)"]
    m = re.search(r"발전 (\d+) W", act)
    if m: power = float(m.group(1))
    m = re.search(r"전력 (\d+) W", act)
    if m and power <= 0: power = -float(m.group(1))
    return dict(defName=r["defName"], name=r["이름"], mod=r["출처 모드"], w=w, h=h, inter=inter, excl=excl,
                power=power, noroof="NotUnderRoof" in r["특징"], invalid="InvalidOverSubstructure" in r["특징"])

# ---------------------------------------------------------------- layout
rooms, doors, pillars, decks, blds = [], [], [], [], []

def R(name, short, cat, x, y, w, h, note=""):
    rooms.append(dict(id=len(rooms), name=name, short=short, cat=cat, x=x, y=y, w=w, h=h, note=note, pillars=[]))
    return rooms[-1]

def D(*pts):
    for p in pts: doors.append(tuple(p))

def DK(name, short, x, y, w, h, note=""):
    decks.append(dict(id=len(decks), name=name, short=short, x=x, y=y, w=w, h=h, note=note))
    return decks[-1]

# corridors
V1 = R("세로 통로 1", "", "corridor", 46, 1, 3, 117)
V2 = R("세로 통로 2", "", "corridor", 99, 1, 3, 117)
H1 = R("가로 통로 1", "", "corridor", 1, 46, 146, 3)
H2 = R("가로 통로 2", "", "corridor", 1, 89, 146, 3)
R("거주 통로", "", "corridor", 72, 10, 3, 36)
R("코어 진입 통로", "", "corridor", 72, 49, 3, 13)
R("실체 구역 통로", "", "corridor", 102, 26, 45, 3)
R("남동 통로", "", "corridor", 115, 92, 3, 26)

# NW: farm / aquarium / drug / expansion B / sensor deck
DK("센서 갑판", "센서 갑판", 1, 1, 22, 11, "지붕 없음")
farm_ext = R("공실 (농장 확장)", "농장 확장", "spare", 1, 13, 22, 9, "외곽 공실"); D((11, 22), (11, 12))
expB = R("확장 블록 B", "확장 B", "expand", 24, 1, 21, 21, "대형 모드 자리 (연구·바이오)"); D((45, 10), (23, 6))
farm = R("수경 농장", "수경 농장", "farm", 1, 23, 22, 22); D((11, 45), (23, 38))
R("약품 가공실", "약품 가공", "work", 24, 23, 10, 22, "전기 약물 연구대"); D((28, 45))
aqua = R("수족관", "수족관", "farm", 35, 23, 10, 22); D((45, 33), (39, 45))

# N: quarters (4 rows)
R("공용 침실 A", "공용 침실", "bed", 50, 10, 21, 8); D((49, 13), (71, 13))
R("공용 침실 B", "공용 침실", "bed", 50, 19, 21, 8); D((49, 22), (71, 22))
R("조각·예술실", "예술", "lab", 76, 37, 10, 8); D((75, 40))
pn = 1
for (x, y, w, dx) in ((76, 10, 10, 75), (87, 10, 11, 98), (76, 19, 10, 75), (87, 19, 11, 98), (50, 28, 10, 49), (61, 28, 10, 71), (76, 28, 10, 75),
                      (87, 28, 11, 98), (50, 37, 10, 49), (61, 37, 10, 71)):
    R(f"개인 침실 {pn}", "개인", "bed", x, y, w, 8); D((dx, y + 3)); pn += 1
R("보호막실 N", "보호막", "defense", 87, 37, 11, 8); D((98, 40))

# NE: research + entity
R("의식실", "의식실", "entity", 103, 1, 12, 24); D((108, 25))
contain = R("실체보관실", "실체보관실", "entity", 116, 1, 26, 24, "중력 구속대 30기")
R("실체 격리 전실", "전실", "entity", 143, 1, 4, 24); D((142, 12), (144, 25))
R("연구실 A", "연구", "lab", 103, 30, 12, 15); D((108, 29), (108, 45), (102, 37))
R("연구실 B", "연구", "lab", 116, 30, 12, 15); D((121, 29), (121, 45))
R("실체 연구실", "실체 연구", "entity", 129, 30, 12, 15); D((134, 29), (134, 45))
R("생체강 가공실", "생체강", "entity", 142, 30, 5, 15); D((144, 29))

# W: expansion A / charging / simple work / waste / shield
R("확장 블록 A", "확장 A", "expand", 1, 50, 21, 25, "대형 모드 자리 (외곽)"); D((11, 49))
R("단순작업실", "단순작업", "work", 1, 76, 21, 12); D((11, 88), (22, 81))
R("보호막실 W", "보호막", "defense", 23, 50, 10, 12); D((27, 49))
R("폐기물 처리실", "폐기물", "mech", 34, 50, 11, 12); D((39, 49), (45, 55))
R("충전 격납고 A", "충전 A", "mech", 23, 63, 22, 12); D((45, 68))
R("충전 격납고 B", "충전 B", "mech", 23, 76, 22, 12); D((45, 81), (33, 88))

# Core
R("북서 반응로실", "반응로", "power", 50, 50, 8, 12, "특이점 반응로 2"); D((54, 49), (49, 55))
R("오락·도서실", "오락", "living", 59, 50, 12, 12); D((64, 49))
R("대식당", "대식당", "living", 76, 50, 13, 12); D((82, 49))
R("북동 반응로실", "반응로", "power", 90, 50, 8, 12, "특이점 반응로 3"); D((93, 49), (98, 55))
R("간부실 A", "간부실", "bed", 50, 63, 12, 12); D((49, 68))
engine = R("중력구동기실", "구동기실", "command", 63, 63, 21, 12, "중력 단조대 3기 포함"); D((73, 62), (84, 68), (70, 75))
bridge = R("조종실", "조종실", "command", 85, 63, 13, 12); D((98, 68))
R("간부실 B", "간부실", "bed", 50, 76, 12, 12); D((49, 81))
R("반응로실", "반응로", "power", 63, 76, 15, 12); D((70, 88), (78, 81))
R("기계실", "기계실", "power", 79, 76, 19, 12, "자기 보호막 발생기·냉각"); D((98, 81), (88, 88))

# E: prison hub
R("주방", "주방", "living", 103, 50, 11, 11); D((102, 55), (108, 49), (108, 61))
R("교도 통로", "", "prison", 115, 50, 3, 11); D((116, 49), (116, 61))
R("치료실", "치료실", "med", 119, 50, 13, 11); D((125, 49), (125, 61))
R("성장 배양실", "성장 배양", "bio", 133, 50, 14, 11); D((139, 49), (140, 61))
R("냉동고", "냉동고", "living", 103, 62, 11, 14); D((102, 68), (114, 68), (108, 76))
hall = R("수감 홀", "수감 홀", "prison", 115, 62, 19, 14, "통짜 공용 감방")
R("유전자 연구소", "유전자", "bio", 135, 62, 12, 14); D((134, 68))
R("시체·부산물 가공실", "가공실", "work", 103, 77, 14, 11); D((109, 88), (117, 82))
R("의류 제작실", "의류 제작", "work", 118, 77, 11, 11); D((123, 88))
R("화학 제작실", "화학 제작", "work", 130, 77, 17, 11); D((138, 88))

# SE: trade / reserve power / fuel / storage / defense
R("상선 교역실", "교역실", "store", 103, 93, 11, 12); D((102, 98), (108, 92))
R("연료실", "연료실", "power", 119, 93, 12, 12, "진입로에서 한 칸 안쪽"); D((118, 98))
R("예비 발전실", "예비 발전", "power", 132, 93, 15, 12, "영점 반응로 2기 자리"); D((138, 92))
R("일반 창고", "창고", "store", 103, 106, 11, 12); D((102, 110), (114, 111))
R("방어 설비실", "방어 설비", "defense", 119, 106, 28, 12, "무기 거치대·수리대·보호막 E"); D((118, 111))

# S: production
R("금속·부품 작업실", "금속·부품", "work", 50, 93, 24, 12, "같은 재료 작업대 모음"); D((49, 98), (61, 92))
R("밀리라 작업실", "밀리라", "work", 75, 93, 23, 12); D((98, 98), (86, 92))
R("보호막실 S", "보호막", "defense", 50, 106, 10, 12); D((49, 111))
R("공실 S", "생산 확장", "spare", 61, 106, 24, 12, "두 작업실 확장용 외곽 공실"); D((67, 105), (80, 105))
R("초월공학 작업실", "초월공학", "work", 86, 106, 12, 12); D((98, 111))

# SW: mining / mech production
R("채굴실", "채굴", "farm", 1, 93, 22, 12, "자동 공허 채굴기"); D((11, 92))
R("메카 제작실", "메카 제작", "mech", 24, 93, 21, 12); D((45, 98), (34, 92))

# outside decks
DK("추진기 갑판", "추진기 갑판", -12, 30, 12, 80, "지붕 없음"); D((0, 47), (0, 90))
DK("격납·착륙 갑판", "격납·착륙 갑판", 148, 30, 26, 46, "지붕 없음 · 전투기·셔틀"); D((147, 47))
DK("방어 진입 갑판", "방어 진입 갑판", 168, 77, 34, 33, "지붕 없음 · 습격 유도 진입로")
# east defence module: guard posts, zigzag kill corridor, side path
R("북측 경비실", "경비실", "defense", 148, 77, 19, 7, "근거리 방어"); D((157, 76))
R("킬존 회랑", "킬존", "killzone", 148, 85, 19, 11, "지그재그 총안 벽"); D((147, 90), (167, 90))
R("남측 경비실", "경비실", "defense", 148, 97, 19, 7, "근거리 방어"); D((157, 104))
R("경비 통로", "옆길", "sidepath", 148, 105, 19, 3, "정착민용 옆길"); D((147, 106), (167, 106))
VAC_DOORS = {(147, 90), (167, 90)}
PORT_WALLS = [(x, 84) for x in range(148, 167)] + [(x, 96) for x in range(148, 167)] + \
             [(152, y) for y in range(85, 93)] + [(156, y) for y in range(88, 96)] + \
             [(160, y) for y in range(85, 93)] + [(164, y) for y in range(88, 96)]
DECK_WALLS = [(x, 76) for x in range(168, 174)] + [(x, 86) for x in range(172, 197)] + [(x, 94) for x in range(172, 197)]
R("북측 에어록 1", "에어록", "airlock", 40, -6, 9, 6, "격벽 이중문"); D((47, 0), (44, -7))
R("북측 에어록 2", "에어록", "airlock", 99, -6, 9, 6, "격벽 이중문"); D((100, 0), (103, -7))
R("남측 에어록 1", "에어록", "airlock", 43, 119, 9, 6, "격벽 이중문"); D((47, 118), (47, 125))
R("남측 에어록 2", "에어록", "airlock", 96, 119, 9, 6, "격벽 이중문"); D((100, 118), (100, 125))
OUTER_DOORS = {(44, -7), (103, -7), (47, 125), (100, 125)}   # unpowered doors: the defence grid may run under them
DK("북서 포대 갑판", "북서 포대", 1, -12, 38, 12, "지붕 없음 · 장거리 포탑"); D((39, -3))
DK("북측 포대 갑판", "북측 포대", 50, -12, 48, 21, "지붕 없음 · 장거리 포탑"); D((49, -3), (98, -3))
DK("북동 포대 갑판", "북동 포대", 109, -12, 38, 12, "지붕 없음 · 장거리 포탑"); D((108, -3))
DK("남서 포대 갑판", "남서 포대", 1, 106, 44, 12, "지붕 없음 · 장거리 포탑"); D((44, 118))
DK("남측 포대 갑판", "남측 포대", 53, 119, 42, 12, "지붕 없음 · 장거리 포탑"); D((52, 121), (95, 121))
DK("남동 포대 갑판", "남동 포대", 106, 119, 41, 12, "지붕 없음 · 장거리 포탑"); D((105, 121))
DK("남동 연결 갑판", "연결", 148, 109, 20, 10, "지붕 없음 · 방어 전력망 통로")
# defence power grid: C-shaped route outside the hull, never touching the main grid
DEF_PORTALS = [(x, -7) for x in range(39, 50)] + [(x, -7) for x in range(98, 109)] + \
              [(0, y) for y in range(-1, 30)] + [(-1, 29), (-2, 29)] + [(0, 108)] + \
              [(42, y) for y in range(118, 126)] + [(x, 125) for x in range(43, 53)] + [(x, 125) for x in range(95, 106)] + \
              [(147, 119), (147, 118)]
DEF_DECKS = {"북서 포대 갑판", "북측 포대 갑판", "북동 포대 갑판", "남서 포대 갑판", "남측 포대 갑판", "남동 포대 갑판",
             "추진기 갑판", "방어 진입 갑판", "남동 연결 갑판"}

# ---------------------------------------------------------------- grid
OX, OY = 40, 16
GW, GH = 252, 176
EMPTY, INT, WALL, DOOR, PILL, DECK = 0, 1, 2, 3, 4, 5
kind = [[EMPTY] * GW for _ in range(GH)]
owner = [[None] * GW for _ in range(GH)]   # ('r', id) or ('d', id)
occ = [[None] * GW for _ in range(GH)]      # building index
errors = []

def G(x, y): return x + OX, y + OY
def cells_of(o):
    for yy in range(o["y"], o["y"] + o["h"]):
        for xx in range(o["x"], o["x"] + o["w"]):
            yield xx, yy
def K(x, y):
    gx, gy = G(x, y)
    if 0 <= gx < GW and 0 <= gy < GH: return kind[gy][gx]
    return None
def O(x, y):
    gx, gy = G(x, y)
    return owner[gy][gx] if 0 <= gx < GW and 0 <= gy < GH else None
def setk(x, y, k, o=None):
    gx, gy = G(x, y); kind[gy][gx] = k
    if o is not None: owner[gy][gx] = o

iscorr = lambda rid: rooms[rid]["cat"] == "corridor"
for r in rooms:
    for (x, y) in cells_of(r):
        o = O(x, y)
        if o is not None and not (iscorr(o[1]) and iscorr(r["id"])):
            errors.append(f"overlap {rooms[o[1]]['name']} / {r['name']} @{x},{y}")
        if o is None: setk(x, y, INT, ("r", r["id"]))
cid = lambda o: ("C",) if o and o[0] == "r" and iscorr(o[1]) else o
for r in rooms:
    for (x, y) in cells_of(r):
        a = O(x, y)
        for dx, dy in ((1, 0), (0, 1)):
            b = O(x + dx, y + dy)
            if b is not None and b[0] == "r" and cid(a) != cid(b):
                errors.append(f"no wall {rooms[a[1]]['name']} / {rooms[b[1]]['name']} @{x},{y}")
for gy in range(GH):
    for gx in range(GW):
        if kind[gy][gx] == EMPTY:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = gy + dy, gx + dx
                    if 0 <= nx < GW and 0 <= ny < GH and kind[ny][nx] == INT:
                        kind[gy][gx] = WALL
for d in decks:
    for (x, y) in cells_of(d):
        if K(x, y) != EMPTY: errors.append(f"deck {d['name']} over {K(x, y)} @{x},{y}")
        setk(x, y, DECK, ("d", d["id"]))

for (x, y) in DECK_WALLS:
    setk(x, y, WALL); gx, gy = G(x, y); owner[gy][gx] = None
for (x, y) in PORT_WALLS:
    if K(x, y) not in (INT, WALL): errors.append(f"port wall on {K(x, y)} @{x},{y}")
    setk(x, y, WALL); gx, gy = G(x, y); owner[gy][gx] = None
DECK_RING = []
for d in decks:
    for x in range(d["x"] - 1, d["x"] + d["w"] + 1):
        for y in range(d["y"] - 1, d["y"] + d["h"] + 1):
            if d["x"] <= x < d["x"] + d["w"] and d["y"] <= y < d["y"] + d["h"]: continue
            if d["name"] == "추진기 갑판" and x == d["x"] - 1: continue
            if d["name"] == "방어 진입 갑판" and x == d["x"] + d["w"] and 87 <= y <= 93: continue
            if K(x, y) == EMPTY:
                setk(x, y, WALL); DECK_RING.append((x, y))
door_side = {}  # door -> list of (owner, approach cell)
for (x, y) in doors:
    if K(x, y) != WALL: errors.append(f"door not on wall @{x},{y} ({K(x, y)})"); continue
    setk(x, y, DOOR)
    sides = []
    for (ax, ay, bx, by) in ((x - 1, y, x + 1, y), (x, y - 1, x, y + 1)):
        a, b = O(ax, ay), O(bx, by)
        if a is not None and b is not None and cid(a) != cid(b):
            sides = [(a, (ax, ay)), (b, (bx, by))]
    if not sides and (x, y) in OUTER_DOORS:
        for (ax, ay, bx, by) in ((x - 1, y, x + 1, y), (x, y - 1, x, y + 1)):
            a, b = O(ax, ay), O(bx, by)
            if (a is None) != (b is None) and K(*((ax, ay) if a is None else (bx, by))) == EMPTY:
                sides = [(a or b, (ax, ay) if a else (bx, by))]
    if not sides: errors.append(f"door @{x},{y} connects nothing")
    door_side[(x, y)] = sides

def room_cells(o):
    src = rooms[o[1]] if o[0] == "r" else decks[o[1]]
    return [(x, y) for (x, y) in cells_of(src) if O(x, y) == o and K(x, y) in (INT, DECK)]

# ---------------------------------------------------------------- pillars
def support_ok(cellset, pil):
    sup = set()
    for (x, y) in cellset:
        pass
    return None

def auto_pillars(r, maxp=4):
    cells = [(x, y) for (x, y) in cells_of(r)]
    def wall_d(x, y):
        return min(x - r["x"] + 1, r["x"] + r["w"] - x, y - r["y"] + 1, r["y"] + r["h"] - y)
    unc = [(x, y) for (x, y) in cells if wall_d(x, y) > 6]
    chosen = []
    while unc:
        if len(chosen) >= maxp: errors.append(f"pillars >{maxp} needed in {r['name']}"); break
        best, bestc = None, -1
        for (px, py) in cells:
            if (px, py) in chosen: continue
            c = sum(1 for (x, y) in unc if (x - px) ** 2 + (y - py) ** 2 <= 36)
            if c > bestc: best, bestc = (px, py), c
        chosen.append(best)
        unc = [(x, y) for (x, y) in unc if (x - best[0]) ** 2 + (y - best[1]) ** 2 > 36]
    return chosen

def add_pillars(r, pts):
    for p in pts:
        if O(*p) != ("r", r["id"]): errors.append(f"pillar outside {r['name']} {p}")
        setk(p[0], p[1], PILL); pillars.append(p); r["pillars"].append(p)

# ---------------------------------------------------------------- buildings
def rot_vec(x, y, rot):
    for _ in range(rot % 4): x, y = -y, x
    return x, y

def footprint(sp, cx, cy, rot):
    w, h = sp["w"], sp["h"]
    cells = []
    for dx in range(-((w - 1) // 2), w // 2 + 1):
        for dz in range(-((h - 1) // 2), h // 2 + 1):
            rx, ry = rot_vec(dx, -dz, rot)
            cells.append((cx + rx, cy + ry))
    inter = None
    if sp["inter"]:
        ix, iz = sp["inter"]; rx, ry = rot_vec(ix, -iz, rot); inter = (cx + rx, cy + ry)
    excl = []
    if sp["excl"]:
        ew, el = sp["excl"]
        ys = [ry for (_, ry) in [(dx, -dz) for dx in range(-((w - 1) // 2), w // 2 + 1) for dz in range(-((h - 1) // 2), h // 2 + 1)]]
        base = max(ys) + 1
        for dx in range(-((ew - 1) // 2), ew // 2 + 1):
            for k in range(el):
                rx, ry = rot_vec(dx, base + k, rot); excl.append((cx + rx, cy + ry))
    return cells, inter, excl

reserved = set()  # interaction cells + door approaches
for dp, sides in door_side.items():
    for (o, c) in sides: reserved.add(c)

def owner_of_cell(c): return O(*c)

def free(c, o):
    if O(*c) != o: return False
    k = K(*c)
    if k not in (INT, DECK): return False
    gx, gy = G(*c)
    return occ[gy][gx] is None

def reach_ok(o, extra_cells, extra_inter, extra_access):
    cells = room_cells(o)
    blocked = set(extra_cells)
    def walk(c):
        if c in blocked: return False
        gx, gy = G(*c)
        return O(*c) == o and K(*c) in (INT, DECK) and occ[gy][gx] is None
    starts = [c for dp, s in door_side.items() for (oo, c) in s if oo == o]
    if not starts: return True
    seen = set(s for s in starts if walk(s)); dq = deque(seen)
    while dq:
        x, y = dq.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n not in seen and walk(n): seen.add(n); dq.append(n)
    targets = [b for b in blds if b["o"] == o]
    for b in targets:
        if b["inter"] and b["inter"] not in seen: return False
        if not b["inter"] and not any(n in seen for n in b["adj"]): return False
    if extra_inter and extra_inter not in seen: return False
    if extra_access is not None and not any(n in seen for n in extra_access): return False
    return True

def adj_of(cells):
    s = set(cells); out = []
    for (x, y) in cells:
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n not in s: out.append(n)
    return out

def try_place(sp, o, cx, cy, rot, tag="", check_reach=True):
    cells, inter, excl = footprint(sp, cx, cy, rot)
    for c in cells:
        if not free(c, o) or c in reserved: return None
    if inter:
        if not free(inter, o) or inter in reserved and not any(inter == b["inter"] for b in blds): return None
        if inter in cells: return None
    if sp["noroof"] and o[0] != "d": return None
    for c in excl:
        if K(*c) not in (EMPTY, None): return None
    adj = [n for n in adj_of(cells)]
    if check_reach and not reach_ok(o, cells, inter, None if inter else adj): return None
    b = dict(i=len(blds), sp=sp, o=o, cx=cx, cy=cy, rot=rot, cells=cells, inter=inter, excl=excl, adj=adj, tag=tag)
    blds.append(b)
    for c in cells:
        gx, gy = G(*c); occ[gy][gx] = b["i"]
    if inter: reserved.add(inter)
    return b

def place(key, o, cx, cy, rot=0, tag=""):
    sp = spec(key)
    b = try_place(sp, o, cx, cy, rot, tag)
    if b is None: errors.append(f"cannot place {sp['name']} in {oname(o)} @{cx},{cy} r{rot}")
    return b

def oname(o): return rooms[o[1]]["name"] if o[0] == "r" else decks[o[1]]["name"]

def autofill(o, items, tag="", optional=False):
    cells = room_cells(o)
    src = rooms[o[1]] if o[0] == "r" else decks[o[1]]
    def wd(c):
        x, y = c
        return min(x - src["x"], src["x"] + src["w"] - 1 - x, y - src["y"], src["y"] + src["h"] - 1 - y)
    order = sorted(cells, key=lambda c: (wd(c), c[1], c[0]))
    for key, n in items:
        sp = spec(key)
        for _ in range(n):
            done = False
            for (cx, cy) in order:
                for rot in (0, 2, 1, 3):
                    if try_place(sp, o, cx, cy, rot, tag):
                        done = True; break
                if done: break
            if not done:
                if not optional: errors.append(f"autofill: no room for {sp['name']} in {oname(o)}")
                break

RO = lambda name: ("r", next(r["id"] for r in rooms if r["name"] == name))
DO = lambda name: ("d", next(d["id"] for d in decks if d["name"] == name))

# pillars for big rooms (farm/containment/hall manual, rest automatic)
add_pillars(farm, [(6, 30), (17, 30), (6, 37), (17, 37)])
add_pillars(contain, [(124, 8), (133, 8), (124, 17), (133, 17)])
for r in rooms:
    if r["cat"] == "corridor" or r["pillars"]: continue
    if min(r["w"], r["h"]) > 12:
        add_pillars(r, auto_pillars(r))

for r in rooms:
    r["area"] = r["w"] * r["h"] - len(r["pillars"])

# --- core fixed placements
eo = RO("중력구동기실")
ENG = place("GravEngine", eo, 73, 69, 0, "engine")
place("AdvShip_GravForge" if "AdvShip_GravForge" in BYDEF else "중력 단조대", eo, 73, 66, 2)
place("중력 단조대", eo, 70, 69, 1)
place("중력 단조대", eo, 76, 69, 3)
bo = RO("조종실")
place("PilotConsole", bo, 91, 72, 2)
autofill(bo, [("AdvShip_ComputerCore", 1), ("CommsConsole", 1), ("CMC_CommandBench", 1),
              ("CM_ManagerDatabase", 1), ("SignalJammer", 1), ("alt4s_UniversalTradeConsole", 1)])
place("AdvShip_GravReactor", RO("반응로실"), 69, 81, 0)
place("AdvShip_GravReactor", RO("북서 반응로실"), 54, 56, 0)
place("AdvShip_GravReactor", RO("북동 반응로실"), 94, 56, 0)
# --- power protection: solar-flare magnetic shields, fuses/breakers sized to stored energy
STORE_WD = {"GravBattery": 100000, "NCL_Large_Battery": 12000, "NCL_Battery": 2000, "Battery": 600, "MAG_ArchotechBatteryS": 10000}
stored_wd = sum(STORE_WD.get(b["sp"]["defName"], 0) for b in blds)
fuse_need = 0  # RT Fuse removed from the mod list
autofill(RO("기계실"), [("Building_RTMagneticShield", 1), ("CoolerPylon_GT", 2)])

# --- quarters
def dresser():
    for k in ("Dresser", "서랍장", "밀리라 서랍장"):
        try: spec(k); return k
        except KeyError: pass
DR = dresser()
for r in rooms:
    if r["name"].startswith("개인 침실"):
        autofill(("r", r["id"]), [("Bed_AdvDoubleBed", 1), (DR, 1), ("EndTable", 2)])
    if r["name"].startswith("간부실"):
        autofill(("r", r["id"]), [("Bed_Kingsize", 1), (DR, 2), ("EndTable", 2)])
    if r["name"].startswith("공용 침실"):
        autofill(("r", r["id"]), [("Bed", 6), ("EndTable", 3), (DR, 2)])
autofill(RO("조각·예술실"), [("TableSculpting", 2)])
autofill(RO("연구실 A"), [("HiTechResearchBench", 1), ("AdvancedMultiAnalyzer", 2), ("MultiAnalyzer", 1)])
autofill(RO("연구실 B"), [("HiTechResearchBench", 1), ("CMC_CommConsole", 1), ("EccentricAuroraCore", 1)])

# --- entity
co = RO("실체보관실")
plat = 0
for row_y in (3, 7, 11, 15, 19):  # platform top-left rows, aisles between
    for col_x in range(117, 141, 4):
        if plat >= 30: break
        cx, cy = col_x + 1, row_y + 1  # 2x2 centre convention: cells cx..cx+1? handled by footprint
        b = try_place(spec("GravHoldingPlatform"), co, col_x, row_y, 0, check_reach=False)
        if b:
            plat += 1
            try_place(spec("BioferriteHarvester"), co, col_x + 2, row_y, 0, check_reach=False)
contain["note"] = f"중력 구속대 {plat}기"
for (x, y) in ((117, 2), (129, 2), (140, 2), (117, 22), (129, 22), (140, 22)):
    try_place(spec("GravShardInhibitor"), co, x, y, 0, check_reach=False)
autofill(RO("실체 연구실"), [("SerumCentrifuge", 1), ("HiTechResearchBench", 1)])
autofill(RO("생체강 가공실"), [("BioferriteShaper", 1), ("BioferriteGenerator", 1)])
autofill(RO("의식실"), [("AL_RitualSpot", 1), ("PsychicRitualSpot", 1), ("GravShardBeacon", 2)])
place("GravFieldExtender", RO("실체 격리 전실"), 145, 3, 0, "extender")

# --- shields
for n in ("보호막실 N", "보호막실 W", "보호막실 S"):
    autofill(RO(n), [("AdvShip_ShieldGenerator", 1)])

# --- prison hub
autofill(RO("주방"), [("VFE_TableStoveLarge", 1), ("ElectricStove", 1), ("VCE_CondimentPrepTable", 1), ("VCE_CanningMachine", 1)])
autofill(RO("냉동고"), [("jdgg_RefCargoHold", 4), ("CoolerPylon_GT", 2)])
autofill(RO("치료실"), [("MedPodStandard", 4), ("Bed_OperatingTable", 2), ("Facility_VitalsCentre", 1)])
autofill(RO("성장 배양실"), [("MEXY_EssenceCultivationPod", 1), ("MEXY_BioCultivationModule", 1), ("GrowthVat", 6)])
autofill(RO("유전자 연구소"), [("UniversalGeneCompiler", 1), ("GeneAssembler", 1), ("GeneExtractor", 1), ("MAG_ArchoGeneExtractor", 1),
                             ("MEXY_GeneCultivator", 1), ("MEXY_GeneComprehensiveAnalyzer", 1), ("GeneProcessor", 2),
                             ("GeneBank", 4), ("UGC_GeneStorageExtender", 2)])
autofill(RO("수감 홀"), [("Bed", 8)])
autofill(RO("시체·부산물 가공실"), [("VFE_TableButcherElectric", 1), ("TableAutopsy", 1), ("ElectricCrematorium", 1),
                                 ("MiliraExpandedXY_LifeEssenceExtractor", 1)])
autofill(RO("의류 제작실"), [("VFE_TableTailorLarge", 1), ("ElectricTailoringBench", 1), ("Axolotl_HandBench", 1),
                            ("Axolotl_ElectricHandBench", 1), ("VFE_TailorCabinet", 1), ("jdgg_MassCargoHold", 1)])
autofill(RO("화학 제작실"), [("BiofuelRefinery", 2), ("Spaceports_FuelProcessor", 1), ("jdgg_MassCargoHold", 1)])

# --- SE
autofill(RO("상선 교역실"), [("OrbitalTradeBeacon", 2), ("jdgg_MassCargoHold", 1)])
autofill(RO("예비 발전실"), [("CMC_ZPReactor_Large", 2)])
autofill(RO("연료실"), [("AdvShip_GravChemfuelTank", 2), ("LargeChemfuelTank", 4)])
autofill(RO("일반 창고"), [("jdgg_MassCargoHold", 2), ("Shelf", 2)])
autofill(RO("방어 설비실"), [("MechaWeaponChanger", 1), ("Shelf_RepairRack", 2), ("Shelf_WeaponRack", 6)])
place("GravFieldExtender", RO("방어 설비실"), 144, 115, 0, "extender")
place("AdvShip_ShieldGenerator", RO("방어 설비실"), 144, 108, 0, "shieldE")

# --- W

# --- S production
autofill(RO("금속·부품 작업실"), [("CMC_FacBench", 1), ("VFE_TableMachiningLarge", 1), ("FabricationBench", 1),
                               ("CMC_TableMachining", 1), ("EccentricNanofabricator", 1), ("EccentricNanoassembler", 1),
                               ("ElectricSmelter", 1), ("ElectricSmithy", 1), ("VFE_ComponentFabricationBench", 1),
                               ("CMC_WeaponModificationBench", 1), ("VFE_MachiningCabinet", 1), ("VFE_FabricationCabinet", 1), ("jdgg_MassCargoHold", 2)])
autofill(RO("밀리라 작업실"), [("Milira_GravityLoom", 1), ("Milira_SunBlastFurnace", 1), ("MEXY_ParticleConstructor", 1),
                             ("MiliraExpandedXY_MatterDecomposer", 1), ("MiliraExpandedXY_MatterRecomposer", 1),
                             ("Milira_UniversalBench", 1), ("Milira_TailoringBench", 1), ("Milira_DroneBench", 1),
                             ("Milira_SunBlasterBoosterJar", 2), ("jdgg_MassCargoHold", 2)])
autofill(RO("초월공학 작업실"), [("MAG_ArchoReproductorLarge", 1), ("BasicArchotechWorkbench", 1), ("ArchBench", 1), ("jdgg_MassCargoHold", 1)])

# --- SW mech
autofill(RO("채굴실"), [("VoidMiner", 1), ("AutoVoidMiner", 8), ("jdgg_MassCargoHold", 1)])
autofill(RO("메카 제작실"), [("LargeMechGestator", 3), ("Milian_Gestator", 2), ("MechGestator", 1), ("AdvancedMechGestator", 1),
                           ("SubcoreEncoder", 1), ("SubcoreSoftscanner", 1), ("SubcoreRipscanner", 1), ("jdgg_MassCargoHold", 1)])
autofill(RO("충전 격납고 A"), [("StandardRecharger", 4), ("VivianRecharger", 3), ("VivianRechargerB", 3), ("BandNode", 6)])
autofill(RO("충전 격납고 B"), [("Milian_Recharger", 8), ("Milira_DroneRecharger", 4), ("StandardRecharger", 2),
                             ("BandNode", 4), ("AT_FlagStation", 1)])
autofill(RO("단순작업실"), [("VFE_TableStonecutterElectric", 1), ("VRecyclingE_ElectricRecyclingWorkbench", 2), ("jdgg_MassCargoHold", 1)])
autofill(RO("폐기물 처리실"), [("WastepackAtomizer", 2)])

autofill(RO("약품 가공실"), [("VFE_TableDrugLabElectric", 1), ("VFE_DrugCabinet", 1), ("jdgg_MassCargoHold", 1)])

# --- east defence module (non-explosive close-range turrets only) + maid/milian standby
autofill(RO("북측 경비실"), [("CMC_ReinforcedBunker_Fire", 1), ("MiliraImperiumTurret_PointDefense", 1), ("CMC_ReinforcedBunker", 1),
                          ("MiliraImperiumTurret_MiniGun", 2), ("Milian_Recharger", 3)])
autofill(RO("남측 경비실"), [("CMC_ReinforcedBunker_Fire", 1), ("CMC_ReinforcedBunkerAGS_R", 1), ("CMC_ReinforcedBunker", 1),
                          ("MiliraImperiumTurret_MiniGun", 2), ("Milian_Recharger", 3)])
autofill(RO("경비 통로"), [("Milira_DarkMatterBattery", 4)])
for rn, row in (("북측 경비실", 83), ("남측 경비실", 97)):
    for x in range(149, 166, 2):
        try_place(spec("Barricade"), RO(rn), x, row, 0)
FIRE = {"반응로실": 1, "북서 반응로실": 1, "북동 반응로실": 1, "기계실": 1, "연료실": 2, "예비 발전실": 1, "화학 제작실": 1, "주방": 1, "중력구동기실": 1, "조종실": 1,
        "금속·부품 작업실": 1, "밀리라 작업실": 1, "메카 제작실": 1, "북측 경비실": 1, "남측 경비실": 1, "방어 설비실": 1, "유전자 연구소": 1}
for rn, n in FIRE.items():
    autofill(RO(rn), [("ExtinguisherHunterDrone", n)], tag="fire")
# --- dispersed interior strongpoints where colonists spend time (drop pods land near a random colonist)
GUARD = {"대식당": [("MiliraImperiumTurret_PointDefense", 1), ("MiliraImperiumTurret_MiniGun", 1), ("Milian_Recharger", 2)],
         "오락·도서실": [("MiliraImperiumTurret_PointDefense", 1), ("Milian_Recharger", 2)],
         "공용 침실 A": [("MiliraImperiumTurret_MiniGun", 1)], "공용 침실 B": [("MiliraImperiumTurret_MiniGun", 1)],
         "금속·부품 작업실": [("MiliraImperiumTurret_MiniGun", 1), ("Milian_Recharger", 2)],
         "밀리라 작업실": [("MiliraImperiumTurret_MiniGun", 1), ("Milian_Recharger", 2)],
         "연구실 A": [("MiliraImperiumTurret_MiniGun", 1)], "주방": [("MiliraImperiumTurret_MiniGun", 1)],
         "초월공학 작업실": [("MiliraImperiumTurret_MiniGun", 1)], "유전자 연구소": [("MiliraImperiumTurret_MiniGun", 1)]}
for rn, items in GUARD.items():
    autofill(RO(rn), items, tag="guard")

# --- farm pattern: 1x4 basins
fo = RO("수경 농장")
basins = 0
for x in (2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21):
    for y0 in (24, 28, 32, 36, 40):
        b = try_place(spec("HydroponicsBasin"), fo, x, y0 + 1, 0, check_reach=False)
        if b: basins += 1
farm["note"] = f"수경재배기 {basins}기 (경작 {basins * 4}칸)"
ao = RO("수족관")
aqn = 0
for x in (36, 40):
    for y in (24, 28, 32, 36, 40):
        if try_place(spec("FMAquariumL"), ao, x + 1, y + 1, 0, check_reach=False): aqn += 1
aqua["note"] = f"대형 바닥 수족관 {aqn}기"

# --- decks
so = DO("센서 갑판")
autofill(so, [("LongRangeMineralScanner", 1), ("GroundPenetratingScanner", 1), ("OrbitalScanner", 1), ("CMC_CommTower", 1),
              ("AT_RecallStation", 1), ("GHFomulaConsole", 1), ("GHTuningConsole", 1)])
to = DO("추진기 갑판")
thr = 0
for cy in range(33, 108, 4):
    if cy in (46, 47, 48, 89, 90, 91): continue
    if try_place(spec("AdvShip_GravThruster"), to, -11, cy, 1, check_reach=False): thr += 1
    if thr >= 12: break
ho = DO("격납·착륙 갑판")
COMBAT = {r["defName"]: r for r in csv.DictReader(open(os.path.join(HERE, "data", "combat.csv"), encoding="utf-8-sig"))}
def expl_r(dn):
    c = COMBAT.get(dn)
    m = re.search(r"파괴 시 폭발 반경 ([\d.]+)", c["특징"]) if c else None
    return float(m.group(1)) if m else 0.0
SHIP_RECTS = [(r["x"], r["y"], r["x"] + r["w"] - 1, r["y"] + r["h"] - 1) for r in rooms]
def ship_dist(x, y):
    best = 1e9
    for (a, b, c, d) in SHIP_RECTS:
        dx = max(a - x, 0, x - c); dy = max(b - y, 0, y - d)
        best = min(best, math.hypot(dx, dy))
    return best
def place_far(o, key, n, optional=False):
    sp = spec(key); R_ = expl_r(sp["defName"]); done = 0
    cells = sorted(room_cells(o), key=lambda c: -ship_dist(*c))
    for (cx, cy) in cells:
        if done >= n: break
        if R_ and ship_dist(cx, cy) <= R_ + 1.5: continue
        for rot in (0, 1, 2, 3):
            b = try_place(sp, o, cx, cy, rot)
            if b:
                xs = [c[0] for c in b["cells"]]; ys = [c[1] for c in b["cells"]]
                if R_ and ship_dist((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2) <= R_ + 0.5:
                    blds.pop()
                    for c in b["cells"]:
                        gx, gy = G(*c); occ[gy][gx] = None
                    if b["inter"]: reserved.discard(b["inter"])
                    continue
                done += 1; break
    if done < n and not optional: errors.append(f"place_far: {sp['name']} {done}/{n} in {oname(o)}")
    return done
def interleave(groups):
    out = []; groups = [list(g) for g in groups]
    while any(groups):
        for g in groups:
            if g: out.append(g.pop(0))
    return out
def place_spread(o, keys, rect=None, far_w=0.35, optional_keys=()):
    cells = room_cells(o)
    if rect:
        rx, ry, rw, rh = rect
        cells = [c for c in cells if rx <= c[0] < rx + rw and ry <= c[1] < ry + rh]
    xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
    x0, x1_, y0, y1_ = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    w, h = x1_ - x0, y1_ - y0
    n = len(keys)
    cols = max(1, min(n, round(math.sqrt(n * w / h)) or 1)); rows = math.ceil(n / cols)
    slots = []
    for r_ in range(rows):
        k = min(cols, n - r_ * cols)
        for c_ in range(k):
            slots.append((x0 + (c_ + 0.5) * w / k, y0 + (r_ + 0.5) * h / rows))
    dist = {c: ship_dist(*c) for c in cells}; maxd = max(dist.values())
    placed = 0
    for key, (sx, sy) in zip(keys, slots):
        sp = spec(key); R_ = expl_r(sp["defName"])
        cand = sorted(cells, key=lambda c: math.hypot(c[0] - sx, c[1] - sy) + far_w * (maxd - dist[c]))
        ok = False
        for (cx, cy) in cand[:600]:
            for rot in (0, 1, 2, 3):
                fc, _, _ = footprint(sp, cx, cy, rot)
                if rect and not all(rx <= c[0] < rx + rw and ry <= c[1] < ry + rh for c in fc): continue
                if R_:
                    fx = [c[0] for c in fc]; fy = [c[1] for c in fc]
                    if ship_dist((min(fx) + max(fx)) / 2, (min(fy) + max(fy)) / 2) <= R_ + 0.5: continue
                if blast_conflict(fc, R_, o): continue
                if try_place(sp, o, cx, cy, rot):
                    ok = True; break
            if ok: break
        if ok: placed += 1
        elif key not in optional_keys: errors.append(f"spread: no spot for {sp['name']} in {oname(o)}")
    return placed
def fp_centre(fc):
    fx = [c[0] for c in fc]; fy = [c[1] for c in fc]
    return ((min(fx) + max(fx)) / 2, (min(fy) + max(fy)) / 2)
def blast_conflict(fc, R_, o):
    c_new = fp_centre(fc)
    for b in blds:
        if b["o"][0] != "d": continue
        cb = fp_centre(b["cells"])
        if abs(cb[0] - c_new[0]) > 30 or abs(cb[1] - c_new[1]) > 30: continue
        if R_ and min(math.dist(c_new, c) for c in b["cells"]) <= R_: return True
        Rb = expl_r(b["sp"]["defName"])
        if Rb and min(math.dist(cb, c) for c in fc) <= Rb: return True
    return False
def rep_(k, n): return [k] * n
FIGHTERS = ("Milira_DragonFighter", "Milira_WyvernFighter", "Milira_GriffinFighter", "Milira_HarrierFighter")
place_spread(DO("방어 진입 갑판"), ["CMC_ReinforcedBunker", "MI_Building_ArcEmitter", "BrrtTurret", "CMC_Svcannon", "CMCcannon", "CMC_ReinforcedBunker_Fire"], rect=(168, 77, 34, 9), far_w=0)
place_spread(DO("방어 진입 갑판"), ["CMC_ReinforcedBunker", "CMC_ReinforcedBunkerAGS_R", "BrrtTurret", "MI_Building_ArcEmitter", "PLAMilira_Field_Tower_Player", "CMC_Svcannon", "CMCcannon", "CMC_ReinforcedBunker_Fire"], rect=(168, 95, 34, 15), far_w=0)
place_spread(ho, interleave([["Spaceports_ShuttleLandingPad", "PassengerShuttle", "PassengerShuttle", "Spaceports_Beacon"],
                             ["Milira_DragonFighter", "Milira_WyvernFighter", "Milira_DragonFighter", "Milira_WyvernFighter", "Milira_GriffinFighter", "Milira_GriffinFighter"],
                             ["Milira_SunLightDefenceTowerII", "NCL_LaserDefenceTurret", "PLAMilira_Field_Tower_Player", "Milira_SunLightDefenceTowerII", "NCL_LaserDefenceTurret"],
                             ["Milira_HarrierFighter"] * 4, ["DropSpotTradeShip", "PodLauncher", "PodLauncher"]]), far_w=0, optional_keys=FIGHTERS)
place_spread(DO("추진기 갑판"), interleave([rep_("CMC_EMcannon", 2), rep_("Milira_SunLightDefenceTowerII", 2)]), rect=(-9, 30, 9, 80), far_w=0)
BAT = {
    "북서 포대 갑판": [["CMCML"], rep_("CMC_Svcannon", 2), ["PLAMilira_Field_Tower_Player"], ["CMCcannon_BF"], ["Milira_SunLightDefenceTowerII"]],
    "북측 포대 갑판": [["CMC_SAML"], ["CMC_CICAESA_Radar_Small", "PLAMilira_Field_Tower_Player", "CMC_FCradar"], ["CMC_Svcannon"], ["Milira_SunLightDefenceTowerII"]],
    "북동 포대 갑판": [["CMCML"], ["CMC_ReinforcedBunker_R", "PLAMilira_Field_Tower_Player", "CMC_ReinforcedBunker_R"], ["Milira_SunLightDefenceTowerII"]],
    "남서 포대 갑판": [["CMCML"], ["CMC_EMcannon"], ["PLAMilira_Field_Tower_Player"], ["CMCcannon_BF"], ["Milira_SunLightDefenceTowerII"]],
    "남측 포대 갑판": [["CMC_SAML"], ["CMC_FCradar", "PLAMilira_Field_Tower_Player"], rep_("NCL_LaserDefenceTurret", 2), ["Milira_SunLightDefenceTowerII"]],
    "남동 포대 갑판": [["CMCcannon_BF"], ["CMC_Svcannon", "PLAMilira_Field_Tower_Player", "CMC_Svcannon"], ["Milira_SunLightDefenceTowerII"]],
}
for dn, groups in BAT.items():
    place_spread(DO(dn), interleave(groups), far_w=0.15)
SMALL_SH = ("ASG_SmallWallShieldGenerator", "ShieldPylon_GT")
# GravTech pylons (radius 20) along the thruster deck, inner edge
for y0 in (38, 70, 102):
    for dy in range(0, 8):
        if any(try_place(spec("ShieldPylon_GT"), DO("추진기 갑판"), x, y0 + sgn * dy, 0) for sgn in (1, -1) for x in (-1, -2, -3)): break
    else: errors.append(f"no pylon spot on thruster deck near y{y0}")
# reflection small shield (radius 5) beside every deck turret; exempt from blast spacing
small_n = 0
GUARD_POSTS = (RO("북측 경비실"), RO("남측 경비실"))
for b in list(blds):
    dn = b["sp"]["defName"]
    if (b["o"][0] != "d" and b["o"] not in GUARD_POSTS) or dn not in COMBAT or COMBAT[dn]["종류"] != "포탑": continue
    cb = fp_centre(b["cells"])
    for c in sorted(set(b["adj"]), key=lambda c: math.dist(c, cb)):
        if try_place(spec("ASG_SmallWallShieldGenerator"), b["o"], c[0], c[1], 0):
            small_n += 1; break
    else: errors.append(f"no small shield spot beside {b['sp']['name']} ({oname(b['o'])})")
turrets = sum(1 for b in blds if b["sp"]["defName"] in COMBAT and COMBAT[b["sp"]["defName"]]["종류"] == "포탑")


# ---------------------------------------------------------------- climate: wall units, pylons, oxygen
wallunits = []
used_wall = set()
for (px, py) in DEF_PORTALS:   # no temperature units / pumps next to walls the defence grid runs under
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            used_wall.add((px + dx, py + dy))
            if K(px + dx, py + dy) == INT: reserved.add((px + dx, py + dy))
def side_cells(r):
    # (wall cell, room-side cell, outer cell, dir from room to wall)
    out = []
    for x in range(r["x"], r["x"] + r["w"]):
        out.append(((x, r["y"] - 1), (x, r["y"]), (x, r["y"] - 2), "N"))
        out.append(((x, r["y"] + r["h"]), (x, r["y"] + r["h"] - 1), (x, r["y"] + r["h"] + 1), "S"))
    for y in range(r["y"], r["y"] + r["h"]):
        out.append(((r["x"] - 1, y), (r["x"], y), (r["x"] - 2, y), "W"))
        out.append(((r["x"] + r["w"], y), (r["x"] + r["w"] - 1, y), (r["x"] + r["w"] + 1, y), "E"))
    return out
def outer_type(c):
    k = K(*c)
    if k in (EMPTY, None, DECK): return "ext"
    o = O(*c)
    if k == INT and o and o[0] == "r" and iscorr(o[1]): return "corr"
    return None
RELAX = False
def room_side_free(c, o):
    gx, gy = G(*c)
    if O(*c) != o or K(*c) != INT or c in reserved: return False
    return RELAX or occ[gy][gx] is None
def wall_ok(c): return K(*c) == WALL and c not in used_wall
def place_wall_unit(r, want, key, room_check=True):
    o = ("r", r["id"])
    sc = side_cells(r)
    idx = {(w, d): (w, rc, oc, d) for (w, rc, oc, d) in sc}
    sp = spec(key)
    for (w, rc, oc, d) in sc:
        if outer_type(oc) != want or not wall_ok(w): continue
        if room_check and not room_side_free(rc, o): continue
        cells = [(w, rc, oc)]
        if sp["w"] * sp["h"] == 2:
            nxt = (w[0] + 1, w[1]) if d in ("N", "S") else (w[0], w[1] + 1)
            t = idx.get((nxt, d))
            if not t: continue
            w2, rc2, oc2, _ = t
            if outer_type(oc2) != want or not wall_ok(w2): continue
            if room_check and not room_side_free(rc2, o): continue
            cells.append((w2, rc2, oc2))
        for (a, b, c) in cells:
            used_wall.add(a); reserved.add(b)
        wallunits.append(dict(n=sp["name"], d=sp["defName"], p=sp["power"], room=r["name"], exhaust=want, dir=d,
                              c=[a for (a, b, c) in cells], rs=[b for (a, b, c) in cells], ex=[c for (a, b, c) in cells]))
        return True
    return False

climate_rooms = ["개인 침실", "공용 침실", "조각·예술실", "연구실 A", "연구실 B", "실체 연구실", "의식실", "생체강 가공실", "실체보관실",
                 "오락·도서실", "대식당", "간부실", "조종실", "중력구동기실", "반응로실", "주방", "치료실", "성장 배양실",
                 "유전자 연구소", "시체·부산물 가공실", "의류 제작실", "화학 제작실", "금속·부품 작업실", "밀리라 작업실",
                 "초월공학 작업실", "메카 제작실", "단순작업실", "충전 격납고", "수경 농장", "약품 가공실", "수족관", "경비실", "킬존 회랑", "북서 반응로실", "북동 반응로실"]
no_unit = []
relaxed = []
for r in rooms:
    if not any(r["name"].startswith(t) for t in climate_rooms): continue
    need = 2 if r["area"] > 250 else 1
    for _ in range(need):
        if not (place_wall_unit(r, "ext", "MUR_TCU_Wide") or place_wall_unit(r, "corr", "MUR_TCU_Wide")
                or place_wall_unit(r, "ext", "MUR_TCU") or place_wall_unit(r, "corr", "MUR_TCU")):
            RELAX = True
            ok = place_wall_unit(r, "ext", "MUR_TCU_Wide") or place_wall_unit(r, "corr", "MUR_TCU_Wide")
            RELAX = False
            if ok: relaxed.append(r["name"])
            else: no_unit.append(r["name"])
for n in no_unit: errors.append(f"no wall for temperature unit: {n}")
# corridors dump heat outside at hull ends
for r in rooms:
    if r["cat"] != "corridor": continue
    k = 0
    while k < 4 and (place_wall_unit(r, "ext", "MUR_TCU_Wide", room_check=False) or place_wall_unit(r, "ext", "MUR_TCU", room_check=False)):
        k += 1
autofill(RO("수감 홀"), [("HeaterPylon_GT", 1), ("CoolerPylon_GT", 1)])
for (x, y) in ((45 + 1, 30), (45 + 1, 110), (101, 30), (99, 112), (30, 46), (120, 46), (30, 91), (120, 91)):
    o = O(x, y)
    if not try_place(spec("HeaterPylon_GT"), o, x, y, 0, check_reach=False): errors.append(f"pylon fail {x},{y}")
for (x, y) in ((46, 3), (48, 115), (101, 7), (99, 115), (2, 48), (145, 46), (2, 91), (145, 89)):
    o = O(x, y)
    if not try_place(spec("OxygenPump"), o, x, y, 0, check_reach=False): errors.append(f"pump fail {x},{y}")
pump_rooms = [r for r in rooms if r["cat"] not in ("corridor",)]
for r in pump_rooms:
    n = 1 + r["area"] // 200
    o = ("r", r["id"])
    # prefer cells next to this room's temperature unit
    near = [c for u in wallunits if u["room"] == r["name"] for c in u["rs"]]
    placed = 0
    for (x, y) in near:
        for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if placed >= n: break
            if try_place(spec("OxygenPump"), o, c[0], c[1], 0): placed += 1
    if placed < n:
        autofill(o, [("OxygenPump", n - placed)])

# ---------------------------------------------------------------- airtightness: bulkheads, door types, wall types
bulkheads = []
def cross_ok(cells, sides):
    for c in cells:
        o = O(*c)
        gx, gy = G(*c)
        if not (o and o[0] == "r" and iscorr(o[1]) and K(*c) == INT and occ[gy][gx] is None and c not in reserved): return False
    return all(K(*c) == WALL for c in sides)
def add_bulkhead(label, seq):
    for cells, sides in seq:
        if cross_ok(cells, sides):
            bulkheads.append(dict(n="격벽 (3x1)", label=label, c=cells, p=-300)); return
    errors.append(f"no bulkhead spot: {label}")
vrow = lambda x0, y: ([(x0, y), (x0 + 1, y), (x0 + 2, y)], [(x0 - 1, y), (x0 + 3, y)])
hcol = lambda x, y0: ([(x, y0), (x, y0 + 1), (x, y0 + 2)], [(x, y0 - 1), (x, y0 + 3)])
add_bulkhead("세로 통로 1 북쪽 에어록", [vrow(46, y) for y in range(3, 20)])
add_bulkhead("세로 통로 1 남쪽 에어록", [vrow(46, y) for y in range(115, 100, -1)])
add_bulkhead("세로 통로 2 북쪽 에어록", [vrow(99, y) for y in range(3, 20)])
add_bulkhead("세로 통로 2 남쪽 에어록", [vrow(99, y) for y in range(115, 100, -1)])
add_bulkhead("가로 통로 1 서쪽 에어록", [hcol(x, 46) for x in range(3, 20)])
add_bulkhead("가로 통로 1 동쪽 에어록", [hcol(x, 46) for x in range(144, 125, -1)])
add_bulkhead("가로 통로 2 서쪽 에어록", [hcol(x, 89) for x in range(3, 20)])
add_bulkhead("가로 통로 2 동쪽 진입로 격벽", [hcol(x, 89) for x in range(144, 125, -1)])
add_bulkhead("가로 통로 1 중앙 구획", [hcol(x, 46) for x in range(64, 90)])
add_bulkhead("가로 통로 2 중앙 구획", [hcol(x, 89) for x in range(64, 90)])
add_bulkhead("세로 통로 1 중앙 구획", [vrow(46, y) for y in range(60, 80)])
add_bulkhead("세로 통로 2 중앙 구획", [vrow(99, y) for y in range(60, 80)])

door_types = []
for (x, y) in doors:
    sides = door_side.get((x, y), [])
    ext = any(o[0] == "d" or (o[0] == "r" and rooms[o[1]]["cat"] == "airlock") for (o, c) in sides) or (x, y) in OUTER_DOORS
    if (x, y) in VAC_DOORS: door_types.append(("vac", "진공 장벽", -50))
    elif (x, y) in OUTER_DOORS: door_types.append(("adoor", "초월공학 문 (무전력)", 0))
    elif ext: door_types.append(("bulk", "격벽", -100))
    else: door_types.append(("door", "일반 문", 0))

deck_wall_set = set(DECK_WALLS)
deck_ring_set = set(DECK_RING)
port_set = set(PORT_WALLS)
def wall_type(x, y):
    if (x, y) in deck_wall_set: return "emb"
    if (x, y) in port_set: return "port"
    if (x, y) in deck_ring_set: return "hull"
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            k = K(x + dx, y + dy)
            if k in (EMPTY, None, DECK): return "hull"
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        o = O(x + dx, y + dy)
        if o and o[0] == "r" and iscorr(o[1]) and K(x + dx, y + dy) == INT: return "corr"
    return "inner"

# ---------------------------------------------------------------- wiring (reference): hidden conduits only
# three kinds of network: main (always on), def (all powered deck turrets, one master switch),
# aa:<deck> (anti-air / interception islands on dark-matter batteries, always on)
import heapq
CONNECT_R = 6
kz_o = RO("킬존 회랑")
def nb4(c): return ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1))
def nb8(c): return [(c[0] + dx, c[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def cond_ok(c):
    k = K(*c)
    if k not in (INT, WALL, DOOR, PILL, DECK): return False
    if k == INT and O(*c) == kz_o: return False
    return True
def deck_name(c):
    o = O(*c)
    return decks[o[1]]["name"] if o and o[0] == "d" and K(*c) == DECK else None
net, GRID = {}, {}
FORB = defaultdict(set)          # grid -> cells it may not use (other grids and a one-cell gap around them)
GRIDS = ("main", "def", "aa:북측 포대 갑판", "aa:남측 포대 갑판")
def put(c, t, g):
    if c in net:
        if GRID[c] != g: errors.append(f"grids touch at {c}: {GRID[c]} / {g}")
        return
    net[c] = t; GRID[c] = g
    for g2 in GRIDS:
        if g2 != g:
            FORB[g2].add(c); FORB[g2].update(nb8(c))
def step_cost(c):
    k = K(*c)
    if k == WALL and wall_type(*c) == "hull": return 5
    if k == DECK: return 2
    return 1
def route(starts, goal_fn, ok_fn):
    dist, prev, h = {}, {}, []
    for s0 in starts:
        if ok_fn(s0): dist[s0] = 0; prev[s0] = None; heapq.heappush(h, (0, s0))
    while h:
        d_, c = heapq.heappop(h)
        if d_ > dist[c]: continue
        if goal_fn(c):
            path = []
            while c is not None: path.append(c); c = prev[c]
            return path
        for n in nb4(c):
            if not ok_fn(n): continue
            nd = d_ + step_cost(n)
            if nd < dist.get(n, 1e18): dist[n] = nd; prev[n] = c; heapq.heappush(h, (nd, n))
    return None
# --- main trunk: one centre line per corridor, joined at every junction, plus 8 junction bypass cells
for r in rooms:
    if r["cat"] != "corridor": continue
    if r["w"] == 3:
        for y in range(r["y"], r["y"] + r["h"]): put((r["x"] + 1, y), "trunk", "main")
    else:
        for x in range(r["x"], r["x"] + r["w"]): put((x, r["y"] + 1), "trunk", "main")
iscorr_cell = lambda c: K(*c) == INT and O(*c) is not None and O(*c)[0] == "r" and iscorr(O(*c)[1])
for r in rooms:
    if r["cat"] != "corridor": continue
    if r["w"] == 3: ends = [((r["x"] + 1, r["y"]), (0, -1)), ((r["x"] + 1, r["y"] + r["h"] - 1), (0, 1))]
    else: ends = [((r["x"], r["y"] + 1), (-1, 0)), ((r["x"] + r["w"] - 1, r["y"] + 1), (1, 0))]
    for (c, (dx, dy)) in ends:
        run = []; q = (c[0] + dx, c[1] + dy)
        while iscorr_cell(q) and q not in net and len(run) < 4: run.append(q); q = (q[0] + dx, q[1] + dy)
        if q in net:
            for z in run: put(z, "trunk", "main")
for c in [(48, 46), (46, 48), (99, 46), (101, 48), (46, 89), (48, 91), (101, 89), (99, 91)]: put(c, "trunk", "main")
feedA = [(146, 89)] + [(147, y) for y in range(89, 79, -1)] + [(x, 80) for x in range(148, 167)]
ring = [(167, y) for y in range(80, 101)] + [(x, 100) for x in range(148, 167)] + [(148, y) for y in range(101, 107)]
feedB = [(x, 106) for x in range(148, 167)] + [(147, 106), (146, 106)]
for c in feedA + ring + feedB: put(c, "mod", "main")
PBUS = [(x, 82) for x in range(70, 87)]
PDROP = {"반응로실": [(70, y) for y in range(83, 90)], "기계실": [(86, y) for y in range(83, 90)],
         "중력구동기실": [(73, y) for y in range(62, 82)]}
for c in PBUS + [c for cs in PDROP.values() for c in cs]: put(c, "bus", "main")
for c in PORT_WALLS: put(c, "under", "main")
# --- consumers and which grid each belongs to; "pos" is the cell the game measures connection distance from
AA_DEF = {"CMC_SAML", "CMC_CICAESA_Radar_Small", "NCL_LaserDefenceTurret"}
SRC_DEF = ("AdvShip_GravReactor", "Milira_DarkMatterBattery")
AA_FP = [set(b["cells"]) for b in blds if b["sp"]["defName"] in AA_DEF]
def bld_grid(b):
    dn = deck_name((b["cx"], b["cy"])) if b["o"][0] == "d" else None
    if dn in DEF_DECKS:
        isl = "aa:" + dn if ("aa:" + dn) in GRIDS else "main"
        if b["sp"]["defName"] in AA_DEF or b["sp"]["defName"] == "Milira_DarkMatterBattery": return isl
        if b["sp"]["defName"] == "ASG_SmallWallShieldGenerator" and any(
                max(abs(c[0] - q[0]), abs(c[1] - q[1])) <= 1 for fp in AA_FP for q in fp for c in b["cells"]): return isl
        return "def"
    return "main"
# anchors: powered doors, bulkheads and wall units keep a gap from def / aa grids
for (x, y), t in zip(doors, door_types):
    if t[2]:
        for g2 in GRIDS[1:]: FORB[g2].add((x, y)); FORB[g2].update(nb8((x, y)))
for u in wallunits:
    for c in u["c"]:
        for g2 in GRIDS[1:]: FORB[g2].add(tuple(c)); FORB[g2].update(nb8(tuple(c)))
def ok_for(g):
    if g == "main":
        return lambda c: cond_ok(c) and c not in FORB["main"] and deck_name(c) not in DEF_DECKS
    if g == "def":
        allowed = set(DEF_PORTALS) | set(DECK_WALLS)
        return lambda c: c not in FORB["def"] and (c in allowed or deck_name(c) in DEF_DECKS)
    dn = g[3:]
    return lambda c: c not in FORB[g] and deck_name(c) == dn
def grow(g, t, tree, terminals):
    ok = ok_for(g); tree = set(tree)
    for term in sorted(terminals, key=lambda p: min((math.dist(p, q) for q in tree), default=0)):
        if term in tree: continue
        if not tree:
            put(term, t, g); tree.add(term); continue
        path = route([term], lambda c: c in tree, ok)
        if not path: errors.append(f"{g}: no route to terminal {term}"); continue
        for c in path: put(c, t, g); tree.add(c)
    return tree
def term_cell(b, g):
    ok = ok_for(g); p = (b["cx"], b["cy"])
    if ok(p): return p
    alt = sorted((c for c in b["cells"] if ok(c)), key=lambda c: math.dist(c, p))
    if alt: return alt[0]
    errors.append(f"{g}: no cell under {b['sp']['name']} ({oname(b['o'])})"); return None
# --- anti-air islands: SAML, phased-array radar, laser point defence on their own dark-matter batteries
aa_info = {}
for g in GRIDS[2:]:
    dn = g[3:]; do = DO(dn)
    aa_b = [b for b in blds if b["o"] == do and b["sp"]["power"] < 0 and bld_grid(b) == g]
    load = -sum(b["sp"]["power"] for b in aa_b)
    need = math.ceil(load * 1.15 / 5000)
    core = [b for b in aa_b if b["sp"]["defName"] in AA_DEF]
    cen = (sum(b["cx"] for b in core) / len(core), sum(b["cy"] for b in core) / len(core))
    sp_dm = spec("Milira_DarkMatterBattery"); got = []
    for (cx, cy) in sorted(room_cells(do), key=lambda c: math.dist(c, cen)):
        if len(got) >= need: break
        fc, _, _ = footprint(sp_dm, cx, cy, 0)
        if blast_conflict(fc, 0, do) or (cx, cy) in FORB[g]: continue
        if any(math.dist((cx, cy), q) < 3 for q in got): continue
        bb = try_place(sp_dm, do, cx, cy, 0, tag="aa")
        if bb: got.append((cx, cy))
    if len(got) < need: errors.append(f"{dn}: only {len(got)}/{need} dark-matter batteries for anti-air")
    terms = [term_cell(b, g) for b in aa_b] + got
    grow(g, "aa", set(), [t_ for t_ in terms if t_])
    aa_info[dn] = dict(load=load, gen=5000 * len(got), n=len(got))
# --- defence grid: master switch in the defence equipment room, then every powered deck turret
do_room = RO("방어 설비실")
xs = next(x for x in range(130, 146) if free((x, 117), do_room) and (x, 117) not in reserved and free((x, 116), do_room))
MASTER = (xs, 117)
for c in DEF_PORTALS + [(xs, 118)]: put(c, "def", "def")
for c in DECK_WALLS: put(c, "under", "def")
def_b = [b for b in blds if b["sp"]["power"] < 0 and bld_grid(b) == "def"]
def_terms = [t_ for t_ in (term_cell(b, "def") for b in def_b) if t_]
grow("def", "def", set(DEF_PORTALS) | {(xs, 118)} | set(DECK_WALLS), def_terms)
# --- main branches
put((xs, 116), "branch", "main")
main_items = []   # (name, where, pos, cells)
for b in blds:
    if (b["sp"]["power"] != 0) and bld_grid(b) == "main" and b["sp"]["defName"] != "Milira_SunLightDefenceTowerII":
        main_items.append((b["sp"]["name"], oname(b["o"]), (b["cx"], b["cy"]), list(b["cells"])))
for u in wallunits:
    if u["p"]: main_items.append((u["n"], u["room"], tuple(u["c"][0]), [tuple(c) for c in u["c"]]))
for bk in bulkheads: main_items.append((bk["n"], bk["label"], tuple(bk["c"][1]), [tuple(c) for c in bk["c"]]))
for (x, y), t in zip(doors, door_types):
    if t[2]: main_items.append((t[1], "문", (x, y), [(x, y)]))
okm = ok_for("main")
def near_main(pos, R=CONNECT_R - 1):
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            q = (pos[0] + dx, pos[1] + dy)
            if dx * dx + dy * dy <= R * R and GRID.get(q) == "main": return True
    return False
for (nm, where, pos, cells) in main_items:
    if near_main(pos): continue
    st = [pos] if okm(pos) else [c for c in cells if okm(c)] or [n for c in cells for n in nb4(c) if okm(n)]
    path = route(st, lambda c: GRID.get(c) == "main", okm)
    if not path: errors.append(f"main: no route to {nm} ({where})"); continue
    for c in path[1:]:
        put(c, "branch", "main")
        if math.dist(c, pos) <= CONNECT_R - 1: break
def comps_of(g):
    cells = [c for c in net if GRID[c] == g]; seen, out = set(), []
    for c in cells:
        if c in seen: continue
        comp = {c}; dq = deque([c]); seen.add(c)
        while dq:
            for n in nb4(dq.popleft()):
                if GRID.get(n) == g and n not in seen: seen.add(n); comp.add(n); dq.append(n)
        out.append(comp)
    return out
for g in GRIDS:
    for _ in range(300):
        cs = sorted(comps_of(g), key=len, reverse=True)
        if len(cs) <= 1: break
        path = route(list(cs[1]), lambda c: c in cs[0], ok_for(g))
        if not path: errors.append(f"{g}: isolated conduit group near {next(iter(cs[1]))}"); break
        for c in path: put(c, "branch" if g == "main" else ("def" if g == "def" else "aa"), g)
net[MASTER] = "switch"; GRID[MASTER] = "switch"
switches = [dict(c=MASTER, label="방어 포탑 전원 (주 스위치)")]
# --- nearest-conduit check: the game connects each building to the closest conduit within 6 cells
def nearest(pos):
    best, bd = [], 99
    for dy in range(-CONNECT_R, CONNECT_R + 1):
        for dx in range(-CONNECT_R, CONNECT_R + 1):
            q = (pos[0] + dx, pos[1] + dy); d2 = dx * dx + dy * dy
            if q in net and d2 <= CONNECT_R * CONNECT_R:
                if d2 < bd: bd, best = d2, [q]
                elif d2 == bd: best.append(q)
    return best
def check_all():
    bad = []
    items = [(b["sp"]["name"], oname(b["o"]), (b["cx"], b["cy"]), bld_grid(b)) for b in blds
             if b["sp"]["power"] != 0 and b["sp"]["defName"] != "Milira_SunLightDefenceTowerII"]
    items += [(u["n"], u["room"], tuple(u["c"][0]), "main") for u in wallunits if u["p"]]
    items += [(bk["n"], bk["label"], tuple(bk["c"][1]), "main") for bk in bulkheads]
    items += [(t[1], "문", (x, y), "main") for (x, y), t in zip(doors, door_types) if t[2]]
    for (nm, where, pos, g) in items:
        nb_ = nearest(pos)
        gs = {GRID[q] for q in nb_} - {"switch"}
        if not nb_: bad.append((nm, where, pos, g, "없음"))
        elif gs != {g}: bad.append((nm, where, pos, g, "/".join(sorted(gs)) or "switch"))
    return bad
for _ in range(3):
    bad = check_all()
    if not bad: break
    for (nm, where, pos, g, got) in bad:
        if g != "main" or not okm(pos): continue
        path = route([pos], lambda c: GRID.get(c) == "main", okm)
        if path:
            for c in path: put(c, "branch", "main")
bad = check_all()
for (nm, where, pos, g, got) in bad[:25]: errors.append(f"wrong grid: {nm} ({where}) @{pos} should be {g}, nearest {got}")
# --- separation: with the master switch off the def grid has no generator
def_cells = {c for c in net if GRID[c] == "def"}
gens_all = [b for b in blds if b["sp"]["power"] > 0]
def_leak = []
for b in gens_all:
    nb_ = nearest((b["cx"], b["cy"]))
    if nb_ and all(GRID[q] == "def" for q in nb_): def_leak.append((b["sp"]["name"], b["sp"]["power"]))
if any(n != "태양 에너지 수집/레이저 포탑" for n, _ in def_leak): errors.append(f"generator on def grid: {def_leak}")
def_load = -sum(b["sp"]["power"] for b in def_b) + 50 * len(DECK_WALLS)
for dn, inf in aa_info.items():
    if inf["gen"] < inf["load"]: errors.append(f"anti-air island {dn} short: {inf}")
# redundancy of the defence module (main side): either feed cut
mod_rooms = {RO(n) for n in ("북측 경비실", "남측 경비실", "경비 통로", "킬존 회랑")}
gens = [b for b in blds if b["sp"]["defName"] in SRC_DEF and bld_grid(b) == "main"]
def near_cells(pos, pool):
    return any((pos[0] + dx, pos[1] + dy) in pool for dy in range(-CONNECT_R, CONNECT_R + 1) for dx in range(-CONNECT_R, CONNECT_R + 1)
               if dx * dx + dy * dy <= CONNECT_R * CONNECT_R)
redund = {}
mod_items = [(b["cx"], b["cy"]) for b in blds if b["o"] in mod_rooms and b["sp"]["power"] < 0]
for cut_name, cut in (("A", set(feedA)), ("B", {(147, 106), (146, 106)})):
    pool = {c for c in net if GRID[c] == "main" and c not in cut}
    comps2, seen = [], set()
    for c in pool:
        if c in seen: continue
        comp = {c}; dq = deque([c]); seen.add(c)
        while dq:
            for n in nb4(dq.popleft()):
                if n in pool and n not in seen: seen.add(n); comp.add(n); dq.append(n)
        comps2.append(comp)
    ok = True
    for pos in mod_items:
        comp = next((cp for cp in comps2 if near_cells(pos, cp)), None)
        if comp is None or not any(near_cells((g_["cx"], g_["cy"]), comp) for g_ in gens): ok = False
    redund[cut_name] = ok
    if not ok: errors.append(f"defence module loses power when feed {cut_name} is cut")
wire_cnt = {}
for t in net.values(): wire_cnt[t] = wire_cnt.get(t, 0) + 1

# ---------------------------------------------------------------- validation
# roof support
sup = set()
for gy in range(GH):
    for gx in range(GW):
        if kind[gy][gx] in (WALL, DOOR, PILL): sup.add((gx, gy))
for gy in range(GH):
    for gx in range(GW):
        if kind[gy][gx] == INT:
            if not any((gx + dx, gy + dy) in sup and dx * dx + dy * dy <= 36 for dy in range(-6, 7) for dx in range(-6, 7)):
                errors.append(f"roof unsupported {oname(owner[gy][gx])} @{gx - OX},{gy - OY}")
                break
# connectivity of rooms via doors
adj = {}
for d1 in decks:          # decks that share an edge are walkable without a door
    for d2 in decks:
        if d1["id"] >= d2["id"]: continue
        if any(O(x + 1, y) == ("d", d2["id"]) or O(x, y + 1) == ("d", d2["id"]) or O(x - 1, y) == ("d", d2["id"]) or O(x, y - 1) == ("d", d2["id"])
               for (x, y) in cells_of(d1) if K(x, y) == DECK):
            adj.setdefault(("d", d1["id"]), set()).add(("d", d2["id"])); adj.setdefault(("d", d2["id"]), set()).add(("d", d1["id"]))
node = lambda o: ("C",) if o[0] == "r" and iscorr(o[1]) else o
for dp, sides in door_side.items():
    if len(sides) == 2:
        a, b = node(sides[0][0]), node(sides[1][0])
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
seen = {("C",)}; dq = deque(seen)
while dq:
    n = dq.popleft()
    for m in adj.get(n, ()):
        if m not in seen: seen.add(m); dq.append(m)
for r in rooms:
    if not iscorr(r["id"]) and ("r", r["id"]) not in seen: errors.append(f"unreachable room {r['name']}")
for d in decks:
    if ("d", d["id"]) not in seen: errors.append(f"unreachable deck {d['name']}")
# per-room reachability of all buildings
for o in set(b["o"] for b in blds):
    if not reach_ok(o, [], None, None): errors.append(f"blocked access in {oname(o)}")
# no-roof / invalid
for b in blds:
    if b["sp"]["invalid"]: errors.append(f"invalid over substructure: {b['sp']['name']}")
    if b["sp"]["noroof"] and b["o"][0] != "d": errors.append(f"noroof under roof: {b['sp']['name']}")

# gravship distance limits
def centre(b):
    xs = [c[0] for c in b["cells"]]; ys = [c[1] for c in b["cells"]]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
E = centre(ENG)
limits = {"중력 단조대": 3.9, "고급 중력부양선 컴퓨터 코어": 26.9, "특이점 반응로": 29.9, "조종석 콘솔": 200,
          "고급 보호막 생성기": 300, "중력 화학연료 탱크": 300, "대형 화학연료 탱크": 500, "중력장 확장기": 100}
dist_checks = []
for b in blds:
    n = b["sp"]["name"]
    if n in limits:
        d = math.dist(E, centre(b))
        dist_checks.append(dict(name=n, dist=round(d, 1), limit=limits[n], ok=d <= limits[n]))
        if d > limits[n]: errors.append(f"too far from engine: {n} {d:.1f}>{limits[n]}")

# substructure tiles & field coverage
sub = [(gx - OX, gy - OY) for gy in range(GH) for gx in range(GW) if kind[gy][gx] != EMPTY]
field = [E] + [centre(b) for b in blds if b["sp"]["name"] in ("중력장 확장기", "특이점 반응로")]
uncovered = [c for c in sub if min(math.dist(c, f) for f in field) > 100]
if uncovered: errors.append(f"{len(uncovered)} substructure tiles outside grav field radius 100")
shields = [centre(b) for b in blds if b["sp"]["name"] == "고급 보호막 생성기"]
ship_tiles = [c for c in sub if K(*c) != DECK]
sh_cov = sum(1 for c in ship_tiles if min(math.dist(c, s) for s in shields) <= 80) / len(ship_tiles)
deck_tiles = [c for c in sub if K(*c) == DECK]
sh_cov_deck = sum(1 for c in deck_tiles if min(math.dist(c, s) for s in shields) <= 80) / len(deck_tiles)

room_int = [(gx - OX, gy - OY) for gy in range(GH) for gx in range(GW) if kind[gy][gx] in (INT, PILL) and owner[gy][gx] and owner[gy][gx][0] == "r"]
expl_checks = []
for b in blds:
    R_ = expl_r(b["sp"]["defName"])
    if not R_: continue
    cx, cy = centre(b)
    dmin = min(math.dist((cx, cy), c) for c in room_int if abs(c[0] - cx) < 25 and abs(c[1] - cy) < 25) if any(abs(c[0] - cx) < 25 and abs(c[1] - cy) < 25 for c in room_int) else 99
    expl_checks.append(dict(name=b["sp"]["name"], o=oname(b["o"]), r=R_, d=round(dmin, 1), ok=dmin > R_))
    if dmin <= R_: errors.append(f"explosion radius reaches rooms: {b['sp']['name']} {dmin:.1f}<={R_}")
blast_pairs = 0
for b in blds:
    Rb = expl_r(b["sp"]["defName"])
    if not Rb: continue
    cb = centre(b)
    for b2 in blds:
        if b2 is b or abs(centre(b2)[0] - cb[0]) > 30 or abs(centre(b2)[1] - cb[1]) > 30: continue
        if b2["sp"]["defName"] in SMALL_SH: continue
        blast_pairs += 1
        if min(math.dist(cb, c) for c in b2["cells"]) <= Rb:
            errors.append(f"blast of {b['sp']['name']} ({oname(b['o'])}) reaches {b2['sp']['name']}")
ADV_R = 80
SH_R = {"AdvShip_ShieldGenerator": ADV_R, "PLAMilira_Field_Tower_Player": 25, "ShieldPylon_GT": 20, "ASG_SmallWallShieldGenerator": 5}
sh_units = [(b["sp"]["defName"], centre(b)) for b in blds if b["sp"]["defName"] in SH_R]
adv_c = [c for (dn, c) in sh_units if dn == "AdvShip_ShieldGenerator"]
layer = []
for b in blds:
    dn = b["sp"]["defName"]
    if dn not in COMBAT or COMBAT[dn]["종류"] not in ("포탑", "전투기"): continue
    c = centre(b)
    inside = sorted(set(k for (k, s_) in sh_units if math.dist(c, s_) <= SH_R[k] and s_ != c))
    if not any(math.dist(c, s_) <= ADV_R for s_ in adv_c):
        errors.append(f"turret outside advanced shields: {b['sp']['name']} ({oname(b['o'])})")
    layer.append(dict(n=b["sp"]["name"], o=oname(b["o"]), k=len(inside), sh=inside))
eo2 = DO("방어 진입 갑판")
lane_start = [(x, y) for x in (201,) for y in range(87, 94)]
seen2 = set(c for c in lane_start if free(c, eo2)); dq2 = deque(seen2); lane_ok = False
while dq2:
    x, y = dq2.popleft()
    if (x, y) == (168, 90): lane_ok = True; break
    for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if nb not in seen2 and free(nb, eo2): seen2.add(nb); dq2.append(nb)
if not lane_ok: errors.append("entry lane blocked")
ko = RO("킬존 회랑")
kz_len = None; dist_k = {(166, 90): 0}; dq3 = deque([(166, 90)])
while dq3:
    c = dq3.popleft()
    if c == (148, 90): kz_len = dist_k[c]; break
    for nb in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)):
        if nb not in dist_k and free(nb, ko): dist_k[nb] = dist_k[c] + 1; dq3.append(nb)
if kz_len is None: errors.append("kill corridor blocked")
if errors:
    print("\n".join(errors[:80])); print(len(errors), "errors"); sys.exit(1)

# ---------------------------------------------------------------- output
cnt = {k: 0 for k in ("int", "wall", "door", "pill", "deck")}
for gy in range(GH):
    for gx in range(GW):
        k = kind[gy][gx]
        if k == INT: cnt["int"] += 1
        elif k == WALL: cnt["wall"] += 1
        elif k == DOOR: cnt["door"] += 1
        elif k == PILL: cnt["pill"] += 1
        elif k == DECK: cnt["deck"] += 1
total = sum(cnt.values())
corr = sum(1 for gy in range(GH) for gx in range(GW) if kind[gy][gx] == INT and owner[gy][gx][0] == "r" and iscorr(owner[gy][gx][1]))
walls = []
wcount = {}
for gy in range(GH):
    gx = 0
    while gx < GW:
        if kind[gy][gx] == WALL:
            t = wall_type(gx - OX, gy - OY); st = gx
            while gx < GW and kind[gy][gx] == WALL and wall_type(gx - OX, gy - OY) == t: gx += 1
            walls.append([st - OX, gy - OY, gx - st, t]); wcount[t] = wcount.get(t, 0) + gx - st
        else: gx += 1

gen = sum(b["sp"]["power"] for b in blds if b["sp"]["power"] > 0 and b["sp"]["defName"] != "CMC_ZPReactor_Large")
reserve = sum(b["sp"]["power"] for b in blds if b["sp"]["defName"] == "CMC_ZPReactor_Large")
use = -sum(b["sp"]["power"] for b in blds if b["sp"]["power"] < 0) - sum(u["p"] for u in wallunits) - sum(b["p"] for b in bulkheads) - sum(t[2] for t in door_types) + 50 * (wcount.get("emb", 0) + wcount.get("port", 0))
for r in rooms:
    r["area"] = r["w"] * r["h"] - len(r["pillars"])
out_b = []
for b in blds:
    sp = b["sp"]
    out_b.append(dict(n=sp["name"], d=sp["defName"], m=sp["mod"], c=b["cells"], i=b["inter"], e=b["excl"],
                      p=sp["power"], o=oname(b["o"]), w=sp["w"], h=sp["h"]))
counts = {}
for b in blds: counts[b["sp"]["name"]] = counts.get(b["sp"]["name"], 0) + 1
summary = dict(def_load=def_load, def_leak=def_leak, aa_info=aa_info, master=MASTER, n_def_b=len(def_b), wire_cnt=wire_cnt, redund=redund, stored_wd=stored_wd, fuse_need=fuse_need, n_switch=len(switches), kz_len=kz_len, layer=layer, small_sh=small_n, blast_pairs=blast_pairs, expl=expl_checks, lane_ok=lane_ok, ring=len(DECK_RING), turrets=turrets, wcount=wcount, bulk=len(bulkheads), doors_ext=sum(1 for t in door_types if t[0]!='door'), relaxed=relaxed, tcu=len(wallunits), tcu_ext=sum(1 for u in wallunits if u['exhaust']=='ext'), total=total, cnt=cnt, corridor=corr, gen=gen, reserve=reserve, use=use, thrusters=thr, platforms=plat,
               basins=basins, aquariums=aqn, dist=dist_checks, shield_cov=round(sh_cov * 100, 1),
               shield_cov_deck=round(sh_cov_deck * 100, 1), engine=E, field=field,
               support=5000 * (1 + sum(1 for b in blds if b["sp"]["name"] in ("중력장 확장기", "특이점 반응로"))),
               beds=sum(v for k, v in counts.items() if "침대" in k and k != "수술대"), counts=counts)
json.dump(dict(wires=[[c[0], c[1], t, GRID[c]] for c, t in net.items()], switches=[[w["c"][0], w["c"][1], w["label"]] for w in switches], bulkheads=bulkheads, door_types=door_types, wallunits=wallunits, rooms=rooms, decks=decks, doors=doors, pillars=pillars, walls=walls, blds=out_b, summary=summary),
          open(sys.argv[1], "w"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps({k: v for k, v in summary.items() if k not in ("counts", "field")}, ensure_ascii=False, indent=1))
