#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""From a baike item page, pick an album (by keyword) and step through its viewer,
collecting every image URL.  Usage: sn_walk.py <item_url> <keyword> [session]"""
import sys, os, json, re, time, subprocess

TOOLS = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.expandvars(r'%APPDATA%\npm\playwright-cli.cmd')
if not os.path.exists(EXE):
    EXE = 'playwright-cli'


def run_pl(args):
    p = subprocess.run([EXE] + args, capture_output=True, cwd=TOOLS)
    return (p.stdout.decode('utf-8', 'ignore') + '\n' + p.stderr.decode('utf-8', 'ignore'))


def parse(out):
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('"') and line.endswith('"'):
            try:
                return json.loads(json.loads(line))
            except Exception:
                pass
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except Exception:
                pass
    return None


CLICK_JS = r'''
async page => {
  const grab = () => page.evaluate(() => {
    const out = { imgs: [], counter: '' };
    for (const im of document.querySelectorAll('img')) {
      const s = (im.currentSrc || im.src || '');
      if (!s.includes('bkimg.cdn.bcebos.com')) continue;
      if (im.naturalWidth >= 250) out.imgs.push(s.split('?')[0]);
    }
    const m = (document.body.innerText.match(/(\d+)\s*\/\s*(\d+)/) || []);
    out.counter = m[0] || ''; return out;
  });
  const res = [];
  for (let i = 0; i < 60; i++) {
    const g = await grab();
    const main = g.imgs[0] || '';
    if (main && !res.find(r => r.u === main)) res.push({ u: main, c: g.counter });
    const ok = await page.evaluate(() => {
      const b = document.querySelector('[class*=nextPicBtn]');
      if (b) { b.click(); return true; } return false;
    });
    if (!ok) break;
    await page.waitForTimeout(1000);
  }
  return JSON.stringify({ n: res.length, res });
}
'''


def walk(item_url, keyword, session='sq'):
    jsf = os.path.join(TOOLS, '_walk_click.js')
    with open(jsf, 'w', encoding='utf-8') as f:
        f.write(CLICK_JS)
    run_pl([f'-s={session}', 'open'])
    g = run_pl([f'-s={session}', 'goto', item_url])
    if 'is not open' in g:
        run_pl([f'-s={session}', 'open'])
        run_pl([f'-s={session}', 'goto', item_url])
    time.sleep(3)
    # find album links
    js_link = os.path.join(TOOLS, '_walk_links.js')
    with open(js_link, 'w', encoding='utf-8') as f:
        f.write("async page => { await page.waitForTimeout(500); return JSON.stringify(await page.evaluate(() => "
                "[...document.querySelectorAll('a')].filter(a=>/baike\\.baidu\\.com\\/pic\\//.test(a.href))"
                ".map(a=>({t:(a.innerText||'').trim().slice(0,40), h:a.href})))); }")
    links = parse(run_pl([f'-s={session}', '--raw', 'run-code', f'--filename={js_link}'])) or []
    cand = None
    for l in links:
        if keyword and keyword in l['t'] and re.search(r'/\d+/\d+/', l['h']):
            cand = l
            break
    if not cand:
        for l in links:
            if re.search(r'/\d+/\d+/', l['h']):
                cand = l
                break
    if not cand:
        return {'err': 'no album', 'links': links}
    run_pl([f'-s={session}', 'goto', cand['h']])
    time.sleep(4)
    r = parse(run_pl([f'-s={session}', '--raw', 'run-code', f'--filename={jsf}']))
    if r:
        r['album'] = cand
        r['item'] = item_url
    return r


if __name__ == '__main__':
    item = sys.argv[1]
    kw = sys.argv[2] if len(sys.argv) > 2 else ''
    sess = sys.argv[3] if len(sys.argv) > 3 else 'sq'
    out = walk(item, kw, sess)
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    with open(os.path.join(TOOLS, '_walk_out.json'), 'w', encoding='utf-8') as f:
        f.write(txt)
    try:
        print(txt)
    except Exception:
        print(txt.encode('utf-8', 'replace').decode('ascii', 'replace'))
