import html, json, hashlib, collections, csv
from pathlib import Path

ROOT = Path('/home/user/Doubao/chats/38455508308244482')
OUT = ROOT / 'exhibition-shelves'
DATA = json.load(open(OUT / 'data/books.json', encoding='utf-8'))
BOOKS = DATA['books']

# 项目来源与人员信息统一保存在 data/sources.csv(唯一一处)。
# books.json 只留页面展示内容;生成时按 id 把来源字段合并回卡片。
with open(OUT / 'data/sources.csv', encoding='utf-8-sig') as _fh:
    SOURCES = {row['id']: row for row in csv.DictReader(_fh)}
for _b in BOOKS:
    _s = SOURCES.get(_b['id'], {})
    _b['repo'] = _s.get('repo', '')
    _b['repo_owner'] = _s.get('owner', '') or None  # 与旧数据一致:缺省按 bear20252026 处理
    _b['url'] = _s.get('url', '')
    _b['kind'] = _s.get('kind', '') or 'shelf'
    _b['note'] = _s.get('note', '')

CAT_ORDER = ['看 / Visual', '玩 / Play', '做 / Tool', '查 / Data']
CAT_META = {
    '看 / Visual': ('看', 'Visual', '观看、漫游、欣赏', 'scene'),
    '玩 / Play': ('玩', 'Play', '有操作循环、目标与反馈', 'play'),
    '做 / Tool': ('做', 'Tool', '完成一件事、做一件工具', 'interface'),
    '查 / Data': ('查', 'Data', '查阅、核对、获取信息', 'data'),
}
# Pairs come from the old Paper gallery plates: warm-to-cool gradients with
# one deep/light text colour per pair. They are assigned deterministically,
# so the page does not shuffle every time it is rebuilt.
PALETTES = {
    '看 / Visual': [
        ('#dce7f1', '#f6efdf', 'rgba(20,20,22,.38)'),
        ('#9fd8e8', '#f4d9b0', 'rgba(20,20,22,.38)'),
        ('#d9b26a', '#6b2a1e', 'rgba(255,255,255,.55)'),
        ('#181420', '#e79ab5', 'rgba(255,255,255,.55)'),
        ('#dfe9f5', '#e0654f', 'rgba(20,20,22,.38)'),
        ('#ffe9d2', '#d9543d', 'rgba(20,20,22,.38)'),
    ],
    '玩 / Play': [
        ('#eaeae6', '#ff5b14', 'rgba(20,20,22,.38)'),
        ('#ede7dd', '#6c50f6', 'rgba(20,20,22,.38)'),
        ('#dff0d8', '#4e7d5f', 'rgba(20,20,22,.38)'),
        ('#ffe9d2', '#d9543d', 'rgba(20,20,22,.38)'),
        ('#d9f0c4', '#4d9f63', 'rgba(20,20,22,.38)'),
    ],
    '做 / Tool': [
        ('#e8eef7', '#2b36ff', 'rgba(20,20,22,.38)'),
        ('#f0e7d8', '#b26a3c', 'rgba(20,20,22,.38)'),
        ('#dde8e3', '#3d5a55', 'rgba(20,20,22,.38)'),
        ('#e5e9ff', '#6c50f6', 'rgba(20,20,22,.38)'),
        ('#f4e6e4', '#b04b45', 'rgba(20,20,22,.38)'),
    ],
    '查 / Data': [
        ('#f5e8d8', '#ff5b14', 'rgba(20,20,22,.38)'),
        ('#e8e2ff', '#6c50f6', 'rgba(20,20,22,.38)'),
        ('#e4f0d8', '#7a9a3a', 'rgba(20,20,22,.38)'),
    ],
}

def esc(x):
    return html.escape(str(x or ''), quote=True)

def stable_index(s, n):
    h = hashlib.sha1(s.encode('utf-8')).hexdigest()
    return int(h[:8], 16) % n

def split_tags(raw):
    raw = (raw or '').replace('；', ';')
    return [t.strip() for t in raw.split(';') if t.strip()][:4]

def search_text(b):
    return ' '.join([
        b.get('title', ''), b.get('desc', ''), b.get('tags', ''),
        b.get('repo', ''), b.get('category', ''), b.get('lang', ''),
        b.get('note', ''),
    ]).lower()

def card(b, no):
    cat = b['category']
    en = CAT_META[cat][1]
    motif = 'plate--' + CAT_META[cat][3]
    palettes = PALETTES.get(cat, PALETTES['看 / Visual'])
    a, c, m = palettes[stable_index(b.get('id', b.get('title', '')), len(palettes))]
    tags = ''.join(f'<li>{esc(t)}</li>' for t in split_tags(b.get('tags', '')))
    owner = b.get('repo_owner', 'bear20252026')
    repo = b.get('repo', '')
    source = f'{repo} · {owner}' if owner != 'bear20252026' else repo
    target = esc(b.get('url', ''))
    return f'''        <a class="piece" href="{target}" target="_blank" rel="noopener" data-text="{esc(search_text(b))}" data-kind="{esc(b.get('kind', 'shelf'))}" data-category="{esc(en.lower())}">
          <div class="plate {motif}" style="--a:{a};--b:{c};--m:{m}">
            <span class="no">{no:02d}</span>
            <span class="motif" aria-hidden="true"></span>
          </div>
          <div class="copy">
            <div class="line"><h3>{esc(b.get('title', ''))}</h3><span class="arrow" aria-hidden="true">↗</span></div>
            <p>{esc(b.get('desc', ''))}</p>
            <ul class="tags">{tags}</ul>
            <div class="source"><b>{esc(source)}</b></div>
          </div>
        </a>'''

books = sorted(BOOKS, key=lambda b: (CAT_ORDER.index(b['category']) if b['category'] in CAT_ORDER else 99, b.get('title', '').lower()))
counts = collections.Counter(b['category'] for b in books)
total = len(books)

sections = []
for cat in CAT_ORDER:
    key = CAT_META[cat][1].lower()
    items = [b for b in books if b['category'] == cat]
    # numbers are global, so build from the full ordered list below
    sections.append((cat, key, items))

# Global numbering follows the rendered order (category sections, title sort).
all_ordered = []
for cat, key, items in sections:
    all_ordered.extend(items)
numbers = {id(b): n for n, b in enumerate(all_ordered, 1)}

section_html = []
for cat, key, items in sections:
    zh, en, note, _ = CAT_META[cat]
    cards = '\n'.join(card(b, numbers[id(b)]) for b in items)
    section_html.append(f'''        <section class="section" id="{key}" data-category="{key}">
          <div class="sec-head">
            <h2>{zh} / {en}</h2>
            <span class="sec-note">{len(items)} 件 · {note}</span>
          </div>
          <div class="grid">
{cards}
          </div>
        </section>''')

chip_items = ''.join(
    f'<button class="chip" type="button" data-filter="{CAT_META[cat][1].lower()}" aria-pressed="false">{CAT_META[cat][0]} {counts[cat]}</button>'
    for cat in CAT_ORDER
)
CSS = (OUT / 'gradient.css').read_text(encoding='utf-8')
JS = (OUT / 'gradient.js').read_text(encoding='utf-8')

page = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="color-scheme" content="light" />
<title>六架 · 作品公开页</title>
<meta name="description" content="{total} 件正在展出的作品，按看 / 玩 / 做 / 查四类整理；工具架另收 RicoUI Blocks。" />
<link rel="icon" href="data:," />
<style>
{CSS}
</style>
</head>
<body data-total="{total}">
<div class="page">
  <header class="mast">
    <div class="brand"><i></i>六架 · 公开页</div>
    <nav aria-label="分类导航">
      <a href="#visual" data-sec>看</a>
      <a href="#play" data-sec>玩</a>
      <a href="#tool" data-sec>做</a>
      <a href="#data" data-sec>查</a>
      <a href="https://github.com/bear20252026/exhibition-shelves" target="_blank" rel="noopener">GitHub ↗</a>
    </nav>
  </header>

  <main>
    <section class="intro">
      <p class="eyebrow">PUBLIC INDEX · {total} WORKS · BEAR20252026</p>
      <h1>作品，按动作放在一起。</h1>
      <p class="lead">
        {total} 件正在展出的作品，按你实际要做什么分成 <b>看</b>、<b>玩</b>、<b>做</b>、<b>查</b>。
        工具架另收 <b>RicoUI Blocks</b>；仓库只是容器，不单独计数。
      </p>
      <div class="tools">
        <label class="search"><span>Filter</span><input id="q" type="search" placeholder="搜索作品、简介、标签……" autocomplete="off" /></label>
        <span class="count" id="count">{total} pieces</span>
      </div>
      <div class="filters" data-filter-field="category" aria-label="按分类筛选">
        <button class="chip is-active" type="button" data-filter="all" aria-pressed="true">全部 {total}</button>
        {chip_items}
      </div>
    </section>
{''.join(section_html)}
    <p class="empty" id="empty">没有匹配的作品。换个短词，或清除筛选。</p>
  </main>

  <footer>
    <p class="eyebrow">One shelf, four actions</p>
    <p class="fine">
      作品来自 <a href="https://github.com/bear20252026/paper-widgets" target="_blank" rel="noopener">paper-widgets</a>、
      <a href="https://github.com/bear20252026/games" target="_blank" rel="noopener">games</a> 和
      <a href="https://github.com/bear20252026/frontier-shelf-07" target="_blank" rel="noopener">frontier-shelf-07</a>。
    </p>
    <p class="fine">
      <b>RicoUI Blocks</b> 是外部参考作品：<a href="https://github.com/ricocc/ricoui-blocks" target="_blank" rel="noopener">ricocc/ricoui-blocks</a>，
      MIT；只作工具架来源，不在本仓库复制源码。
    </p>
  </footer>
</div>
<script>
{JS}
</script>
</body>
</html>'''

(OUT / 'index.html').write_text(page, encoding='utf-8')
print(f'wrote {OUT / "index.html"} ({len(page)} bytes), {total} cards')
