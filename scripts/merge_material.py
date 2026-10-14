#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「孙权形象_清单11项」与「孙权影视衍生形象」合并为一棵按媒介归类、按年代排序的素材树。
原始两个文件夹保持不动（本脚本只复制）。"""
import os, shutil, json, hashlib, collections

ROOT = r'C:\Users\chenmingwang\Desktop\孙权影视图片'
A = os.path.join(ROOT, '孙权影视衍生形象')          # 主库（按媒介）
B = os.path.join(ROOT, '孙权形象_清单11项')         # 按作品清单
OUT = os.path.join(ROOT, '孙权形象素材_合并')

# (源目录, 目标子目录)  目标子目录相对 OUT
MAP = [
    # ---- 主库 ----
    (os.path.join(A, '07_历史形象_古画'),            '01_历史形象_古画'),
    (os.path.join(A, '01_电视剧_中国大陆'),          '02_电视剧_中国大陆/1994-2010'),
    (os.path.join(A, '02_电视剧_港台'),              '03_电视剧_港台/终极三国_修杰楷'),
    (os.path.join(A, '03_电影'),                     '04_电影/赤壁_张震_2008-2009'),
    (os.path.join(A, '05_日本ACG'),                  '07_游戏/真三国无双8'),
    (os.path.join(A, '06_国产游戏动画'),             '07_游戏/国产游戏宣传图'),
    (os.path.join(A, '_废弃_有浮层或片源错'),        '_已排除/废弃_有浮层或片源错'),
    (os.path.join(A, '_wide_raw'),                   '_原始截帧_未整理/_wide_raw'),
    (os.path.join(A, '_宽景'),                       '_原始截帧_未整理/_宽景'),
    (os.path.join(A, '_宽景_自举'),                  '_原始截帧_未整理/_宽景_自举'),
    (os.path.join(A, '_视频截帧_待挑选'),            '_原始截帧_未整理/_视频截帧_待挑选'),
    # ---- 清单库（去重：08/09/10 与主库 01/03 完全重复，跳过）----
    (os.path.join(B, '02_SD高达世界三国创杰传_2019'), '09_模型手办_SD高达_2019'),
    (os.path.join(B, '03_新解释三国志_2020'),        '04_电影/新解释三国志_2020'),
    (os.path.join(B, '06_军师联盟_丁海峰_2017'),     '02_电视剧_中国大陆/军师联盟_丁海峰_2017'),
    (os.path.join(B, '11_钓_王者荣耀孙权CG_2025'),   '07_游戏/王者荣耀_钓CG_2025'),
    (os.path.join(B, '12_Cos作品_2025-2026'),        '08_Cos作品'),
    (os.path.join(B, '13_游戏_官方立绘'),            '07_游戏/官方立绘'),
    (os.path.join(B, '14_动画_角色图'),              '05_动画_角色图'),
    (os.path.join(B, '15_漫画_角色图'),              '06_漫画_角色图'),
]
SKIP_DIRS = {'_已排除_不可用'}   # 在 Cos 目录内单独处理

DOCS = [
    (os.path.join(A, '00_孙权影视衍生形象总表.md'), '00_索引与说明/孙权影视衍生形象总表.md'),
    (os.path.join(A, '_README_采集说明.md'),        '00_索引与说明/_README_采集说明.md'),
    (os.path.join(B, '_README_清单对照.md'),        '00_索引与说明/_README_清单对照.md'),
    (os.path.join(B, '12_Cos作品_2025-2026', '_README_本目录说明.md'),
     '00_索引与说明/Cos作品_说明.md'),
]

# 主库 01 目录需要拆成两个作品子目录
SPLIT_01 = {
    '1994三国演义': '1994三国演义_吴晓东',
    '2010三国': '2010三国_张博',
    '廉石传奇': '廉石传奇_罗嘉良',
}
SPLIT_BASE = '02_电视剧_中国大陆/1994-2010'


def md5(p):
    d = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            d.update(b)
    return d.hexdigest()


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    log = []
    seen = {}          # md5 -> 首次落盘相对路径（用于跨库去重报告）
    copied = 0
    for src, dstrel in MAP:
        if not os.path.isdir(src):
            log.append(f'[MISS] {src}')
            continue
        for dp, dn, fn in os.walk(src):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fn:
                sp = os.path.join(dp, f)
                sub = os.path.relpath(dp, src)
                target = dstrel
                if sub != '.':
                    target = os.path.join(dstrel, sub)
                # 02 目录按作品再分一层
                if dstrel == SPLIT_BASE:
                    for k, v in SPLIT_01.items():
                        if f.startswith(k):
                            target = os.path.join(SPLIT_BASE, v)
                            break
                    else:
                        target = os.path.join(SPLIT_BASE, '其他')
                op = os.path.join(OUT, target, f)
                os.makedirs(os.path.dirname(op), exist_ok=True)
                shutil.copy2(sp, op)
                copied += 1
                hh = md5(sp)
                seen.setdefault(hh, []).append(os.path.relpath(op, OUT))
    # Cos 的 _已排除
    ex = os.path.join(B, '12_Cos作品_2025-2026', '_已排除_不可用')
    if os.path.isdir(ex):
        for f in os.listdir(ex):
            sp = os.path.join(ex, f)
            if os.path.isfile(sp):
                op = os.path.join(OUT, '_已排除', 'Cos_已排除_不可用', f)
                os.makedirs(os.path.dirname(op), exist_ok=True)
                shutil.copy2(sp, op); copied += 1
    # 文档
    for sp, dstrel in DOCS:
        if os.path.isfile(sp):
            op = os.path.join(OUT, dstrel)
            os.makedirs(os.path.dirname(op), exist_ok=True)
            shutil.copy2(sp, op); copied += 1
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    print('copied files:', copied)
    print('unique contents:', len(seen), '| residual dup groups:', len(dups))
    for k, v in list(dups.items())[:10]:
        print('  dup', v)
    with open(os.path.join(ROOT, '_tools', '_merge_log.json'), 'w', encoding='utf-8') as f:
        json.dump({'copied': copied, 'dups': dups, 'missing': log}, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
