from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path


OUT_DIR = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_fallback_9_20260702"
    r"\workbook_skill_rules_audit_20260702"
)


SECTIONS = [
    (
        "总原则",
        [
            "做 Temu/Xuanxshop 表格工作前，先查 GitHub/本地记忆。",
            "所有技术、workflow、skill 更新必须同步 GitHub。",
            "不直接改唯一源表，必须复制后处理。",
            "过程表、复检前表、候选表、失败表不入库。",
            "只有最终确认表才允许进入 D 查询/指纹库。",
            "用户反馈优先级最高，高于历史通过记录和 approved registry。",
        ],
    ),
    (
        "表格分组",
        [
            "按精确 产品货号(D) 分组，不按 L0xx 前缀粗分。",
            "同一个 D 的标题、T、U、T1 必须一致。",
            "J 是行级别，按每一行的 G + SKU货号 匹配。",
            "空 D 行视为分隔行，不处理。",
            "标题指纹/追踪码按文件、按 D 保留，不能串用。",
        ],
    ),
    (
        "T 首图",
        [
            "新批次全部 D 先走 image2/APIMart。",
            "image2 失败或复检不合格，才走 Seedream/Jimeng fallback。",
            "image2 redo 项不能写回最终表。",
            "后续图像生成、重构、fallback、redo 需要 Claude/NVIDIA 过审。",
            "T 首图按 D 共享，不默认按行生成。",
            "同一 L0xx 要做 PNG 差异化和场景差异化，不能同质化复用。",
            "用户说素材太统一时，下一轮必须换/扩展源 PNG 池。",
        ],
    ),
    (
        "T 列",
        [
            "T 最多 10 张。",
            "U 必须等于 T1。",
            "同 D 的 T 列必须完全一致。",
            "插入新 T1 后要去重、应用删除锁、修复 T4，再截断到 10。",
            "删除/不要/死刑/错误配色/多次删除过的 URL 不得回流。",
            "approved registry 不能覆盖后来的用户反馈。",
        ],
    ),
    (
        "T4 尺寸图",
        [
            "T4 是硬规则，必须是尺寸图。",
            "不能只信“原第 4 张”。",
            "必须通过 URL/文件名/标题线索识别：尺寸、size、尺码 等。",
            "如果原 T4 被删除或不是尺寸图，必须找另一个合法尺寸图放回第 4 位。",
            "找不到合法尺寸图时，不得交付最终表。",
            "最终校验必须检查每行 T4。",
        ],
    ),
    (
        "J 图",
        [
            "J 必须按行 SKU/属性匹配，不能按 D 盲用。",
            "匹配依据优先 G + SKU货号，标题只能做最后辅助。",
            "生成前要打印/复核：row、D、G、SKU、wanted tokens、matched tokens、source、match mode、warning。",
            "如果用户说 J 全部可疑，要全量重做 J，不只补几行。",
            "写回前必须先给 J 复核页并等用户确认。",
            "如果用户指出颜色/变体错配，必须检查实际渲染图片，不能只看文件夹名或路径。",
        ],
    ),
    (
        "五宫格",
        [
            "默认 800x800。",
            "五宫格定义：画布等分 3x3 九宫格。",
            "取五个格子：左上、右上、正中、左下、右下。",
            "每张图居中，并尽量铺满自己的格子。",
            "均等排布，不重叠。",
            "背景可以是浅纹理商业背景，不默认纯白。",
            "除非用户明确说白底，否则不要改成纯白。",
        ],
    ),
    (
        "L042 特规",
        [
            "L042 J 使用整张 SKU 尺寸信息图。",
            "必须保留 Black/Green size 文字、尺寸标注、30PCS 钉子排、产品主体。",
            "不得误抠成仅产品主体，除非用户明确要求 cutout。",
            r"只使用 E:\jit制图\L042\sku\黑色 和 E:\jit制图\L042\sku\绿色 的一级文件。",
            "禁止使用二级目录、九宫格、out、output。",
            "按行属性匹配黑/绿。",
            "不能只信文件夹名，必须做视觉颜色校验。",
            "黑色源图不得呈现绿色标题/绿色主体。",
            "绿色源图必须呈现绿色标题/绿色主体。",
            "混放源图写入 rejected 清单并剔除。",
            "remove.bg 只有用户明确要求且有额度时才试。",
            "remove.bg 返回 insufficient_credits 时立即停止，回到黑/绿一级文件夹五宫格方案。",
        ],
    ),
    (
        "反馈/删除",
        [
            "复核页导出必须读取实时 DOM/input/textarea。",
            "中文反馈不能丢。",
            "localStorage 或 POST 保存失败时，必须从页面 DOM 恢复反馈 JSON。",
            "删除锁必须按精确 URL 应用。",
            "T 删除：同 D 全行删除该 URL。",
            "J 删除：只影响对应行，重做或清空该行 J。",
            "删除后必须重新校验 T≤10、U=T1、T4、删除 URL 不回流。",
        ],
    ),
    (
        "最终校验",
        [
            "effective row count。",
            "unique exact D count。",
            "same-D title mismatch。",
            "empty J。",
            "empty T。",
            "T over 10。",
            "U != T1。",
            "same-D T mismatch。",
            "T4 missing/not-size/not-at-position-4。",
            "deleted/rejected URL returned。",
            "L042 visual color/source mismatch。",
            "SKU source forbidden path。",
            "missing source assets。",
            "generated image existence/dimensions。",
            "OSS/CDN URL prefix check。",
            "任一关键项非 0，不得说最终表完成。",
        ],
    ),
    (
        "当前落地文件",
        [
            r"本地 Codex skill: C:\Users\Administrator\.codex\skills\temu-xuanxshop-image-workbook\SKILL.md",
            r"仓库 skill: C:\Users\Administrator\Documents\temu自动化\skills\temu-xuanxshop-image-workbook\SKILL.md",
            r"仓库 references: C:\Users\Administrator\Documents\temu自动化\skills\temu-xuanxshop-image-workbook\references",
            r"仓库 scripts: C:\Users\Administrator\Documents\temu自动化\skills\temu-xuanxshop-image-workbook\scripts",
            "本地提交: 0eea1ca Update workbook skill rules and references。",
            "GitHub push 状态: 最近两次因 github.com:443 reset/超时失败，待网络恢复后推送。",
        ],
    ),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cards = []
    idx = 1
    for title, items in SECTIONS:
        lis = []
        for item in items:
            lis.append(
                f"<li><span class='num'>{idx}</span><span>{html.escape(item)}</span></li>"
            )
            idx += 1
        cards.append(
            f"<section><h2>{html.escape(title)} <small>{len(items)} 条</small></h2>"
            f"<ol>{''.join(lis)}</ol></section>"
        )

    html_text = f"""<!doctype html>
<meta charset="utf-8">
<title>表格 Skill 规则审核清单</title>
<style>
:root {{ --green:#1f883d; --line:#d8dee4; --bg:#f6f3ec; --ink:#1f2328; --muted:#59636e; }}
body {{ margin:0; font-family:Arial,"Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); }}
header {{ position:sticky; top:0; z-index:5; background:#fff; border-bottom:1px solid var(--line); padding:16px 22px; }}
h1 {{ margin:0 0 6px; font-size:22px; }}
.meta {{ color:var(--muted); font-size:13px; line-height:1.55; }}
main {{ max-width:1180px; margin:0 auto; padding:18px; display:grid; gap:14px; }}
section {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:14px 16px; }}
h2 {{ margin:0 0 10px; font-size:18px; }}
h2 small {{ color:var(--muted); font-weight:400; font-size:12px; }}
ol {{ list-style:none; padding:0; margin:0; display:grid; gap:7px; }}
li {{ display:grid; grid-template-columns:44px 1fr; gap:10px; align-items:start; padding:8px 10px; border:1px solid #eef1f4; border-radius:6px; background:#fbfcfd; line-height:1.5; }}
.num {{ display:inline-flex; align-items:center; justify-content:center; min-width:30px; height:24px; border-radius:999px; background:#e7f3eb; color:var(--green); font-weight:700; font-size:12px; }}
.badge {{ display:inline-block; padding:3px 8px; border-radius:999px; background:#e7f3eb; color:var(--green); font-weight:700; margin-left:8px; }}
footer {{ max-width:1180px; margin:0 auto; padding:0 18px 24px; color:var(--muted); font-size:12px; }}
</style>
<header>
  <h1>表格 Skill 规则审核清单 <span class="badge">{idx - 1} 条</span></h1>
  <div class="meta">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>用途：审核今天校准后写入 temu-xuanxshop-image-workbook skill 的表格规则。</div>
</header>
<main>{''.join(cards)}</main>
<footer>本页只是规则审核，不改 Excel、不跑图、不写回表。</footer>
"""
    (OUT_DIR / "index.html").write_text(html_text, encoding="utf-8")
    print(
        "http://127.0.0.1:8765/outputs/store_newskill_seedream_fallback_9_20260702/"
        "workbook_skill_rules_audit_20260702/index.html"
    )


if __name__ == "__main__":
    main()
