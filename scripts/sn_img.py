#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sogou image search via playwright; returns title/oriPicUrl/source page per hit."""
import sys, os, json, time, subprocess, urllib.parse

TOOLS = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.expandvars(r'%APPDATA%\npm\playwright-cli.cmd')
if not os.path.exists(EXE):
    EXE = 'playwright-cli'

JS = r'''
async page => {
  await page.waitForTimeout(2500);
  const d = await page.evaluate(() => {
    const st = window.__INITIAL_STATE__ || {};
    const sl = (st.searchList && st.searchList.searchList) || [];
    return sl.map(x => ({
      t: (x.title || x.name || '').slice(0, 70),
      img: x.oriPicUrl || x.picUrl || '',
      page: x.page_url || x.pageUrl || x.link || '',
      site: x.ch_site_name || x.author || '',
      w: x.width, h: x.height,
    }));
  });
  return JSON.stringify({ n: d.length, d });
}
'''


def run_pl(a):
    p = subprocess.run([EXE] + a, capture_output=True, cwd=TOOLS)
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


def search(q, session='sq2'):
    jsf = os.path.join(TOOLS, '_img_js.js')
    with open(jsf, 'w', encoding='utf-8') as f:
        f.write(JS)
    url = 'https://pic.sogou.com/pics?query=' + urllib.parse.quote(q)
    run_pl([f'-s={session}', 'open'])
    g = run_pl([f'-s={session}', 'goto', url])
    if 'is not open' in g:
        run_pl([f'-s={session}', 'open'])
        run_pl([f'-s={session}', 'goto', url])
    time.sleep(3)
    return parse(run_pl([f'-s={session}', '--raw', 'run-code', f'--filename={jsf}']))


if __name__ == '__main__':
    q = sys.argv[1]
    sess = sys.argv[2] if len(sys.argv) > 2 else 'sq2'
    r = search(q, sess)
    if not r:
        print('FAIL')
        sys.exit(1)
    print('n=', r['n'])
    json.dump(r, open(os.path.join(TOOLS, '_img_out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for i, x in enumerate(r['d'][:25]):
        print(f"{i:2d} {x['w']}x{x['h']} [{x['site']}] {x['t'][:50]}")
        print(f"     img : {x['img'][:130]}")
        print(f"     page: {x['page'][:130]}")
