#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load a Baike (or any) page in a playwright-cli session and extract images + album links."""
import subprocess, sys, os, json, time

TOOLS = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.expandvars(r'%APPDATA%\npm\playwright-cli.cmd')
if not os.path.exists(EXE):
    EXE = 'playwright-cli'

JS = r'''
async page => {
  await page.waitForTimeout(1000);
  try { await page.evaluate(async () => {
      for (let y=0; y<document.body.scrollHeight; y+=700){ window.scrollTo(0,y); await new Promise(r=>setTimeout(r,220)); }
      window.scrollTo(0,0);
  }); } catch(e){}
  await page.waitForTimeout(1200);
  const data = await page.evaluate(() => {
    const seen=new Set(), imgs=[];
    for (const im of document.querySelectorAll('img')) {
      const s=(im.currentSrc||im.src||'');
      if(!s.includes('bkimg.cdn.bcebos.com')) continue;
      const base=s.split('?')[0];
      if(seen.has(base)) continue; seen.add(base);
      let cap=(im.alt||'').trim();
      if(!cap){ let p=im.parentElement;
        for(let i=0;i<5&&p&&!cap;i++){ const t=(p.innerText||'').replace(/\s+/g,' ').trim(); if(t&&t.length<90)cap=t; p=p.parentElement; } }
      imgs.push({url:base, cap:cap.slice(0,90), w:im.naturalWidth, h:im.naturalHeight});
    }
    const albums=[], sa=new Set();
    for (const a of document.querySelectorAll('a')) {
      const h=a.href||''; if(!/baike\.baidu\.com\/pic\//.test(h)) continue;
      if(sa.has(h)) continue; sa.add(h);
      albums.push({t:(a.innerText||'').replace(/\s+/g,' ').trim().slice(0,40), href:h});
    }
    const body=(document.body.innerText||'').replace(/\s+/g,' ').slice(0,5000);
    return {title:document.title, imgs, albums:albums.slice(0,20), body};
  });
  return JSON.stringify(data);
}
'''


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


def scrape(url, session='sq'):
    jsf = os.path.join(TOOLS, '_bpage.js')
    with open(jsf, 'w', encoding='utf-8') as f:
        f.write(JS)
    run_pl([f'-s={session}', 'open'])          # no-op if already open
    g = run_pl([f'-s={session}', 'goto', url])
    if 'is not open' in g:
        run_pl([f'-s={session}', 'open'])
        run_pl([f'-s={session}', 'goto', url])
    time.sleep(3)
    out = run_pl([f'-s={session}', '--raw', 'run-code', f'--filename={jsf}'])
    return parse(out)


if __name__ == '__main__':
    url = sys.argv[1]
    sess = sys.argv[2] if len(sys.argv) > 2 else 'sq'
    d = scrape(url, sess)
    if d is None:
        print('PARSE FAIL')
        sys.exit(1)
    # print compactly to a file + stdout
    lines = [d['title']]
    for a in d['albums']:
        lines.append(f"ALBUM\t{a['t']}\t{a['href']}")
    for im in d['imgs']:
        lines.append(f"IMG\t{im['w']}x{im['h']}\t{im['cap']}\t{im['url']}")
    txt = '\n'.join(lines)
    with open(os.path.join(TOOLS, '_bout.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n===BODY===\n' + d['body'])
    try:
        print(txt)
    except Exception:
        print(txt.encode('utf-8', 'replace').decode('ascii', 'replace'))
