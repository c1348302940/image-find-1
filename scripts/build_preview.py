#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「推荐形象预览」HTML —— 保证每个模块至少一张代表作。

用法：
    python build_preview.py <素材树根目录> <输出.html> [config.json]

不传 config 时：自动扫根目录下一级目录，每个目录取第一张图当封面，标题用目录名
—— 天然满足「每个模块都有一张」。

config.json（可选，用来自定义封面与推荐理由）：
{
  "title": "孙权 · 推荐形象预览（每个模块一张）",
  "sub": "按素材树模块分组，每个模块至少一张代表作",
  "modules": [
    {"dir": "01_历史形象_古画",
     "label": "01 历史画像",                 // 卡片角标，缺省用 dir
     "img": "阎立本_历代帝王图_孙权.jpg",     // 目录内文件名；缺省自动取第一张
     "title": "阎立本《历代帝王图》孙权像",
     "sub": "唐·阎立本（公有领域）",
     "why": "所有现代改编的形象源头对照。",    // 推荐理由：这张图能证明什么
     "extra": "同模块备选：xxx.jpg、yyy.jpg",  // 可选
     "note": "角色确认度低，需人工复核",        // 可选，标红
     "pair": "07_游戏/xxx/yyy.jpg"}            // 可选：相对素材树根，给卡片配第二张
  ]
}

所有 <img src> 都按「相对 HTML 所在目录」计算，HTML 放哪都能用。
生成后自动校验路径是否命中本地文件并打印 missing=N —— 交付前必须是 0。
"""
import os
import re
import sys
import json
import html

IMG_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

CSS = """
  :root { --bg:#0f1115; --fg:#e8e6e3; --dim:#9aa0a6; --line:#2a2f38; --accent:#e0b44a; --ok:#7ee787; }
  * { box-sizing:border-box; }
  body { margin:0; padding:32px; background:var(--bg); color:var(--fg);
         font:15px/1.6 "Microsoft YaHei","PingFang SC",system-ui,sans-serif; }
  header { max-width:1100px; margin:0 auto 28px; }
  h1 { margin:0 0 6px; font-size:26px; }
  header p { margin:0; color:var(--dim); font-size:14px; }
  .grid { max-width:1100px; margin:0 auto; }
  .card { position:relative; display:grid; grid-template-columns:minmax(0,340px) 1fr;
           gap:22px; margin:0 0 22px; padding:18px; border:1px solid var(--line);
           border-radius:12px; background:#151922; }
  .rank { position:absolute; top:-11px; left:16px; background:var(--accent); color:#1a1a1a;
           font-weight:700; font-size:13px; padding:2px 11px; border-radius:20px; }
  .imgbox { background:#0b0d11; border-radius:8px; overflow:hidden;
             display:flex; align-items:center; justify-content:center; min-height:180px; }
  .imgbox img { width:100%; height:auto; display:block; }
  .imgbox.two { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
  .imgbox.two img { width:100%; height:100%; object-fit:cover; }
  h3 { margin:0 0 4px; font-size:17px; }
  .sub { margin:0 0 10px; color:var(--dim); font-size:13px; }
  .why { margin:0 0 12px; }
  code { font-size:12px; color:#7d8590; word-break:break-all; }
  .miss { color:#ff8a80; }
  .mod { color:var(--ok); }
  @media (max-width:760px) { .card { grid-template-columns:1fr; } }
"""


def first_image(folder):
    for f in sorted(os.listdir(folder)):
        if os.path.splitext(f)[1].lower() in IMG_EXT:
            return f
    return None


def count_images(folder):
    n = 0
    for _, _, fn in os.walk(folder):
        n += sum(1 for f in fn if os.path.splitext(f)[1].lower() in IMG_EXT)
    return n


def rel_to_html(abs_img, html_dir):
    """相对 HTML 所在目录算路径（正斜杠），HTML 放哪都能引用。"""
    return os.path.relpath(abs_img, html_dir).replace('\\', '/')


def build(root, out_html, config):
    root = os.path.abspath(root)
    html_dir = os.path.dirname(os.path.abspath(out_html)) or os.getcwd()

    modules = list(config.get('modules') or [])
    if not modules:                                     # 自动模式
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if os.path.isdir(p) and not d.startswith('_'):
                modules.append({'dir': d})

    cards = []
    for m in modules:
        d = m['dir']
        folder = os.path.join(root, d)
        if not os.path.isdir(folder):
            print('[SKIP] 目录不存在:', d)
            continue
        img = m.get('img') or first_image(folder)
        if not img:
            print('[SKIP] 目录内无图片:', d)
            continue

        rel = rel_to_html(os.path.join(folder, img), html_dir)
        label = m.get('label', d)
        title = m.get('title', d)
        sub = m.get('sub', '')
        n = count_images(folder)
        tag = f'<span class="mod">本模块 {n} 张</span>'
        subline = f'{html.escape(sub)}　｜　{tag}' if sub else tag

        body = ''
        if m.get('why'):
            body += f'<p class="why">{html.escape(m["why"])}</p>'
        if m.get('extra'):
            body += f'<p class="why">{html.escape(m["extra"])}</p>'
        if m.get('note'):
            body += f'<p class="why"><span class="miss">注：{html.escape(m["note"])}</span></p>'

        if m.get('pair'):
            pair_rel = rel_to_html(os.path.join(root, m['pair']), html_dir)
            imgbox = (f'<div class="imgbox two">'
                      f'<img src="{rel}" alt="{html.escape(title)}">'
                      f'<img src="{pair_rel}" alt="">'
                      f'</div>')
        else:
            imgbox = f'<div class="imgbox"><img src="{rel}" alt="{html.escape(title)}"></div>'

        cards.append(f'''  <figure class="card">
    <div class="rank">{html.escape(label)}</div>
    {imgbox}
    <figcaption>
      <h3>{html.escape(title)}</h3>
      <p class="sub">{subline}</p>
      {body}
      <code>{rel.replace('/', '\\')}</code>
    </figcaption>
  </figure>''')

    doc = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(config.get('title', '推荐形象预览'))}</title>
<style>{CSS}</style></head><body>
<header>
  <h1>{html.escape(config.get('title', '推荐形象预览'))}</h1>
  <p>{config.get('sub', '')}</p>
</header>
<div class="grid">
{chr(10).join(cards)}
</div>
</body></html>
'''
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(doc)

    missing = 0
    for s in re.findall(r'<img src="([^"]+)"', doc):
        if not os.path.isfile(os.path.join(html_dir, s.replace('/', os.sep))):
            print('MISSING', s)
            missing += 1
    print(f'模块 {len(cards)} 个，图片路径 missing={missing}')
    return missing


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cfg = {}
    if len(sys.argv) > 3:
        with open(sys.argv[3], encoding='utf-8') as f:
            cfg = json.load(f)
    cfg.setdefault('title', '推荐形象预览')
    sys.exit(1 if build(sys.argv[1], sys.argv[2], cfg) else 0)
