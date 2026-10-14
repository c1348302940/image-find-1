# character-image-collection

为**一个角色**（如孙权、诸葛亮、关羽）跨多部作品系统采集「角色形象素材」的 Claude Code skill。

找源 → 下载 → 身份核验 → 按媒介/作品归类去重 → 生成推荐形象预览页。
记录了各图源的实测可用性、反爬绕过手法，以及 Windows 中文环境 / 公司网络 / 浏览器自动化下的具体坑。

## 安装

```bash
git clone https://github.com/c1348302940/image-find-1.git \
  ~/.claude/skills/character-image-collection
```

或把本目录整个拷进 `~/.claude/skills/character-image-collection/`。

## 交付物（四件套）

跑完一轮，应该产出这四样：

| # | 交付物 | 说明 |
|---|---|---|
| 1 | `素材树/` | 按媒介/作品归类、跨库 MD5 去重后的图片目录 |
| 2 | `推荐形象预览.html` | **每个模块至少一张**代表作的可视化预览页 |
| 3 | `素材清单`（md/json） | 每张图的 **原始 URL + 出处页面 + 分辨率 + 角色确认度** |
| 4 | `未取得说明` | 逐条写清「试过哪些源、为什么没拿到」 |

## 内容

```
SKILL.md                       全流程 + 图源可用性总表 + 踩坑记录 + 交付自检清单
scripts/
  sn_dl.sh                     单张下载 + >5KB/PIL 校验
  sn_baike.py                  Playwright 打开百度百科词条页，取图册链接与图片
  sn_walk.py                   进图册逐张翻页收图
  sn_img.py                    Sogou 图片搜索（走浏览器）
  merge_material.py            多来源素材树 -> 统一分类 + MD5 跨库去重 + 并集校验
  build_preview.py             【交付物 2】素材树 -> 按模块的推荐形象预览 HTML（内置路径自检）
```

## 生成预览页

```bash
# 自动模式：每个一级目录取第一张图当封面，天然满足「每个模块都有一张」
python scripts/build_preview.py <素材树根目录> <输出.html>

# 指定封面与推荐理由
python scripts/build_preview.py <素材树根目录> <输出.html> config.json
```

生成后会打印 `missing=N`（图片路径未命中的数量）——**交付前必须是 0**。

## 三条铁律

1. **严禁编造**作品、演员、图片 URL、出处 —— 拿不到就写「未取得」。
2. **不拿「同名的其他作品」冒充** —— 同名/易混必须先做辨析表。
3. **角色确认度必须诚实标注** —— 只有「作品对 + 造型符合」的图是低确认度，不能当定妆图用。
