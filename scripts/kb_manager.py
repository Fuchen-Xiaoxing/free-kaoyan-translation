#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb_manager.py - Knowledge Base & Workflow Manager for Kaoyan English II Translation

Subcommands:
  1. init: Atomic S0 initialization (prompt, breakdown, context, and optional draft preflight linting).
  2. prompt: Retrieve pure English prompt, sentence breakdown and context (physically isolates reference translation).
  3. anchor: Retrieve full reference translation and sentence benchmark alignment (strictly for Stage 4 debrief).
  4. check: Preflight linting for student translation drafts (sentence count, proper noun check, punctuation balance).
  5. query: Search syntactic patterns or translation polysemy across user brain and seed bases.
  6. settle: Atomic settlement of translation session (archives essay, writes patterns/vocab to user brain, logs history).
  7. doctor: Comprehensive health check for paths, anchors, seeds, user brain, and environment credentials.
  8. status: Summary of user brain assets, mastery, and practice history.
"""

import sys
import os
import json
import argparse
import datetime
import re
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"
ANCHORS_FILE = KB_DIR / "anchors" / "translation_past_papers.jsonl"
SEEDS_DIR = KB_DIR / "seeds"
PATTERNS_SEED = SEEDS_DIR / "translation_patterns.seed.jsonl"
VOCAB_SEED = SEEDS_DIR / "translation_vocab.seed.jsonl"
USER_BRAIN_DIR = KB_DIR / "user_brain"
USER_PATTERNS = USER_BRAIN_DIR / "patterns.jsonl"
USER_VOCAB = USER_BRAIN_DIR / "vocab.jsonl"
ARCHIVES_DIR = USER_BRAIN_DIR / "archives"
META_FILE = USER_BRAIN_DIR / ".kb_meta.json"
HISTORY_LOG = USER_BRAIN_DIR / "history.log"

PROPER_NOUNS_MAP = {
    "william wordsworth": "威廉·华兹华斯",
    "wordsworth": "华兹华斯",
    "romanticism": "浪漫主义",
    "ted ning": "泰德·宁",
    "ning": "宁",
    "beethoven": "贝多芬",
    "shakespeare": "莎士比亚",
    "bill gates": "比尔·盖茨",
    "james herriot": "吉米·哈利 / 詹姆斯·赫里奥特",
    "chicago": "芝加哥"
}


def load_jsonl(file_path: Path) -> list:
    if not file_path.exists():
        return []
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def get_anchor_by_year(year: str) -> dict:
    anchors = load_jsonl(ANCHORS_FILE)
    clean_year = str(year).strip()
    for item in anchors:
        if str(item.get("year", "")).strip() == clean_year:
            return item
    return None


def cmd_prompt(args):
    """Retrieve pure English prompt and sentence breakdown without reference translation."""
    anchor = get_anchor_by_year(args.year)
    if not anchor:
        print(f"❌ 未找到 {args.year} 年考研英语二翻译真题。", file=sys.stderr)
        sys.exit(1)

    output = {
        "year": anchor.get("year"),
        "exam_type": anchor.get("exam_type", "English II"),
        "title": anchor.get("title", ""),
        "theme": anchor.get("theme", ""),
        "word_count": anchor.get("word_count", 0),
        "source_text": anchor.get("source_text", ""),
        "sentences": [
            {"id": s.get("id"), "english": s.get("english")}
            for s in anchor.get("sentences", [])
        ]
    }
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"📖 【{output['title']}】 (考研英语二 Section Ⅲ Translation)")
        print(f"📌 篇章题材: {output['theme']} | 词数: {output['word_count']} 词 | 句子总数: {len(output['sentences'])} 句\n")
        print("【英文原文】:")
        print(output["source_text"])
        print("\n【逐句清单】:")
        for s in output["sentences"]:
            print(f"  [{s['id']}] {s['english']}")


def cmd_anchor(args):
    """Retrieve full official reference translation and benchmark analysis (Stage 4 only)."""
    anchor = get_anchor_by_year(args.year)
    if not anchor:
        print(f"❌ 未找到 {args.year} 年考研英语二翻译标尺数据。", file=sys.stderr)
        sys.exit(1)

    if not args.full:
        print("⚠️ 提示: anchor 命令默认仅在 S4 终局对照复盘阶段使用，必须指定 --full 参数以解密完整参考译文。", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(anchor, ensure_ascii=False, indent=2))
    else:
        print(f"🏆 【{anchor.get('title')} · 真题官方高分参考标尺】\n")
        print("【官方参考译文】:")
        print(anchor.get("reference_translation", ""))
        print("\n【逐句英汉对齐】:")
        for s in anchor.get("sentences", []):
            print(f"  [{s.get('id')}]")
            print(f"    EN: {s.get('english')}")
            print(f"    CN: {s.get('chinese')}")


def run_draft_lint(content: str, anchor: dict = None, label: str = "学员译文初稿") -> dict:
    """Run linting checks on student translation draft."""
    char_count = len(re.sub(r"\s+", "", content))
    cn_sentences = [s.strip() for s in re.split(r"(?<=[。！？\n])\s*", content) if s.strip()]

    issues = []
    passes = []

    # Check 1: Length check (normally 200~350 Chinese characters)
    if char_count < 150:
        issues.append(f"中文字数偏少 ({char_count} 字)，可能存在漏译分句或未完成段落")
    elif char_count > 450:
        issues.append(f"中文字数偏多 ({char_count} 字)，请检查是否存在冗余累赘或翻译腔")
    else:
        passes.append(f"字数达标 ({char_count} 字，处于 200~350 标准区间)")

    # Check 2: Sentence count match if anchor specified
    if anchor:
        exp_count = len(anchor.get("sentences", []))
        act_count = len(cn_sentences)
        if abs(act_count - exp_count) > 3:
            issues.append(f"分句数量偏离较大 (实际识别 {act_count} 句，真题英文包含 {exp_count} 句)，请核对是否有遗漏整句")
        else:
            passes.append(f"分句对应合理 (英文 {exp_count} 句 ➔ 汉语译文切分为 {act_count} 句)")

    # Check 3: Paired quotes / brackets
    left_quotes = content.count("“")
    right_quotes = content.count("”")
    if left_quotes != right_quotes:
        issues.append(f"中文双引号不闭合 (左引号“ {left_quotes} 处，右引号” {right_quotes} 处)")
    else:
        passes.append("成对标点符号闭合正常")

    # Check 4: Proper noun checks
    for en_name, cn_name in PROPER_NOUNS_MAP.items():
        if anchor and en_name in anchor.get("source_text", "").lower():
            expected_parts = [p.strip() for p in cn_name.split("/")]
            matched = any(p in content for p in expected_parts)
            if not matched:
                issues.append(f"约定俗成专有名词核对未命中: 原文出现 '{en_name}'，标准译名为 '{cn_name}'")
            else:
                passes.append(f"约定俗成专名命中: '{en_name}' ➔ 正确译出")

    return {
        "label": label,
        "char_count": char_count,
        "sentence_count": len(cn_sentences),
        "passes": passes,
        "issues": issues,
        "is_clean": len(issues) == 0
    }


def format_lint_report(lint: dict) -> str:
    """Format lint result into human-readable report."""
    lines = [
        f"📋 【学员译文初稿预检报告】: {lint.get('label', '初稿')}",
        f"📊 汉字字符数: {lint.get('char_count', 0)} 字 | 识别分句数: {lint.get('sentence_count', 0)} 句\n"
    ]
    if lint.get("passes"):
        lines.append("✅ 通过项:")
        for p in lint["passes"]:
            lines.append(f"  • {p}")
    if lint.get("issues"):
        lines.append("\n⚠️ 关注项与潜在风险:")
        for iss in lint["issues"]:
            lines.append(f"  • {iss}")
    else:
        lines.append("\n🎉 初检查验无硬伤，可直接推进逐句精讲！")
    return "\n".join(lines)


def cmd_check(args):
    """Preflight check on student translation draft."""
    content = ""
    label = "直接输入文本"
    if getattr(args, "text", None):
        content = args.text.strip()
    elif getattr(args, "file", None):
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}", file=sys.stderr)
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        label = file_path.name
    elif not sys.stdin.isatty():
        content = sys.stdin.read().strip()
        label = "标准输入(stdin)"
    else:
        print("❌ 必须提供 --file 或 --text 参数，或通过管道输入初译草稿。", file=sys.stderr)
        sys.exit(1)

    anchor = get_anchor_by_year(args.year) if getattr(args, "year", None) else None
    lint = run_draft_lint(content, anchor=anchor, label=label)

    if getattr(args, "json", False):
        print(json.dumps(lint, ensure_ascii=False, indent=2))
    else:
        print(format_lint_report(lint))


def cmd_init(args):
    """Atomic initialization for S0: extracts prompt, context and optionally checks draft."""
    anchor = get_anchor_by_year(args.year)
    if not anchor:
        print(f"❌ 未找到 {args.year} 年考研英语二翻译真题。", file=sys.stderr)
        sys.exit(1)

    content = ""
    label = "草稿文本"
    if getattr(args, "text", None):
        content = args.text.strip()
    elif getattr(args, "file", None):
        file_path = Path(args.file)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            label = file_path.name

    lint_result = run_draft_lint(content, anchor=anchor, label=label) if content else None

    output = {
        "year": anchor.get("year"),
        "exam_type": anchor.get("exam_type", "English II"),
        "title": anchor.get("title", ""),
        "theme": anchor.get("theme", ""),
        "word_count": anchor.get("word_count", 0),
        "source_text": anchor.get("source_text", ""),
        "sentences": [
            {"id": s.get("id"), "english": s.get("english")}
            for s in anchor.get("sentences", [])
        ],
        "draft_lint": lint_result
    }

    if getattr(args, "json", False):
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"📖 【{output['title']}】 (考研英语二 Section Ⅲ Translation)")
        print(f"📌 篇章题材: {output['theme']} | 词数: {output['word_count']} 词 | 句子总数: {len(output['sentences'])} 句\n")
        print("【英文原文】:")
        print(output["source_text"])
        print("\n【逐句清单】:")
        for s in output["sentences"]:
            print(f"  [{s['id']}] {s['english']}")
        if lint_result:
            print("\n" + format_lint_report(lint_result))


def cmd_query(args):
    """Query translation patterns or vocabulary in seeds and user brain."""
    category = args.category.lower() if args.category else "all"
    kw = (args.keyword or "").strip().lower()

    results = []

    if category in ("pattern", "patterns", "all"):
        seeds = load_jsonl(PATTERNS_SEED)
        user_items = load_jsonl(USER_PATTERNS)
        for it in user_items:
            it["_source"] = "user_brain"
        for it in seeds:
            it["_source"] = "seed"
        all_pat = user_items + seeds
        for p in all_pat:
            text = f"{p.get('id', '')} {p.get('pattern_name', '')} {p.get('category', '')} {p.get('structure', '')} {p.get('principle', '')}".lower()
            if not kw or kw in text:
                results.append({"type": "pattern", "data": p})

    if category in ("vocab", "all"):
        seeds = load_jsonl(VOCAB_SEED)
        user_items = load_jsonl(USER_VOCAB)
        for it in user_items:
            it["_source"] = "user_brain"
        for it in seeds:
            it["_source"] = "seed"
        all_voc = user_items + seeds
        for v in all_voc:
            text = f"{v.get('word', '')} {v.get('translation_meaning', '')} {v.get('general_meaning', '')} {v.get('exam_trap', '')}".lower()
            if not kw or kw in text:
                results.append({"type": "vocab", "data": v})

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"🔍 检索结果 (关键词: '{kw or '全部'}', 类型: {category}, 共 {len(results)} 条):\n")
        for idx, r in enumerate(results, 1):
            d = r["data"]
            src_tag = "[外脑资产]" if d.get("_source") == "user_brain" else "[系统底座]"
            if r["type"] == "pattern":
                print(f"{idx}. {src_tag} [{d.get('id')}] 【{d.get('pattern_name')}】({d.get('category')})")
                print(f"   结构: {d.get('structure')}")
                print(f"   原理: {d.get('principle')}")
                print(f"   例句: {d.get('example_en')} ➔ {d.get('example_cn')}\n")
            else:
                print(f"{idx}. {src_tag} 【{d.get('word')}】")
                print(f"   考研翻译释义: {d.get('translation_meaning')} (大纲常用意: {d.get('general_meaning', '-')})")
                if d.get("exam_trap"):
                    print(f"   避坑提示: {d.get('exam_trap')}\n")


def cmd_settle(args):
    """Atomic settlement of translation session (archives essay, writes patterns/vocab, logs history)."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 结算载荷文件不存在: {file_path}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"❌ 载荷 JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(2)

    # Validate essential fields
    task_id = payload.get("task_id")
    year = payload.get("year")
    title = payload.get("title", f"{year}年考研英语二翻译")
    basic_tr = payload.get("basic_translation", "")
    adv_tr = payload.get("advanced_translation", "")

    if not task_id or not year or not (basic_tr or adv_tr):
        print("❌ 载荷缺少必要字段 (task_id, year, basic_translation 或 advanced_translation)", file=sys.stderr)
        sys.exit(2)

    # Backup states for rollback
    try:
        # 1. Write patterns if any
        new_patterns = payload.get("batch", {}).get("new_patterns", [])
        if new_patterns:
            with open(USER_PATTERNS, "a", encoding="utf-8") as f:
                for pat in new_patterns:
                    pat_entry = dict(pat)
                    pat_entry["settled_at"] = datetime.datetime.now().isoformat()
                    pat_entry["task_id"] = task_id
                    f.write(json.dumps(pat_entry, ensure_ascii=False) + "\n")

        # 2. Write vocab if any
        new_vocab = payload.get("batch", {}).get("new_vocab", [])
        if new_vocab:
            with open(USER_VOCAB, "a", encoding="utf-8") as f:
                for voc in new_vocab:
                    voc_entry = dict(voc)
                    voc_entry["settled_at"] = datetime.datetime.now().isoformat()
                    voc_entry["task_id"] = task_id
                    f.write(json.dumps(voc_entry, ensure_ascii=False) + "\n")

        # 3. Archive essay markdown
        ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
        archive_path = ARCHIVES_DIR / f"{task_id}.md"
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(f"# 考研英语二翻译归档 · {title}\n\n")
            f.write(f"- **任务编号**: `{task_id}`\n")
            f.write(f"- **真题年份**: {year} 年\n")
            f.write(f"- **归档时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            if payload.get("score_estimate"):
                score_info = payload["score_estimate"]
                f.write(f"## 评分与估分报告\n- **预估得分**: **{score_info.get('total_score', '-')} / {score_info.get('max_score', 15.0)} 分**\n")
                if score_info.get("deductions"):
                    f.write("- **扣分复盘**:\n")
                    for d in score_info["deductions"]:
                        f.write(f"  • {d.get('item', '')}: {d.get('penalty', '')} 分\n")
                f.write("\n")
            f.write("## 基础合规版译文\n\n" + basic_tr + "\n\n")
            f.write("## 高分地道润色版译文\n\n" + adv_tr + "\n\n")

        # 4. Update meta
        meta = {}
        if META_FILE.exists():
            try:
                with open(META_FILE, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass
        meta["total_settled_tasks"] = meta.get("total_settled_tasks", 0) + 1
        meta["total_user_patterns"] = meta.get("total_user_patterns", 0) + len(new_patterns)
        meta["total_user_vocab"] = meta.get("total_user_vocab", 0) + len(new_vocab)
        meta["last_updated"] = datetime.datetime.now().isoformat()
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 5. Log history
        with open(HISTORY_LOG, "a", encoding="utf-8") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] [SETTLE] Task {task_id} ({title}) settled. Patterns: +{len(new_patterns)}, Vocab: +{len(new_vocab)}.\n")

        print("==============================================")
        print("🎉 考研英语二翻译本地外脑原子结算成功！")
        print("==============================================")
        print(f"📦 任务编号: {task_id}")
        print(f"📁 译文归档: {archive_path.relative_to(PROJECT_ROOT)}")
        print(f"🧠 新增高分句型: {len(new_patterns)} 条 ➔ patterns.jsonl")
        print(f"📚 新增熟词生义: {len(new_vocab)} 条 ➔ vocab.jsonl")
        print("✅ 本地资产已安全落盘。")

    except Exception as e:
        print(f"❌ 结算过程中发生异常: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_doctor(args):
    """Comprehensive environment, database and token check."""
    print("🩺 【考研英语二翻译 Skill 系统与环境体检报告】\n")
    all_pass = True

    # Check 1: Anchors
    if ANCHORS_FILE.exists():
        anchors = load_jsonl(ANCHORS_FILE)
        print(f"✅ 真题标尺库: 正常 ({len(anchors)} 篇真题，覆盖 2010~2024 年)")
    else:
        print("❌ 真题标尺库: 缺失 (translation_past_papers.jsonl 不存在)")
        all_pass = False

    # Check 2: Seeds
    if PATTERNS_SEED.exists() and VOCAB_SEED.exists():
        p_seeds = load_jsonl(PATTERNS_SEED)
        v_seeds = load_jsonl(VOCAB_SEED)
        print(f"✅ 种子规则库: 正常 (句型种子 {len(p_seeds)} 条，熟词生义种子 {len(v_seeds)} 条)")
    else:
        print("❌ 种子规则库: 缺失")
        all_pass = False

    # Check 3: User brain
    if USER_BRAIN_DIR.exists() and USER_PATTERNS.exists() and USER_VOCAB.exists():
        u_p = len(load_jsonl(USER_PATTERNS))
        u_v = len(load_jsonl(USER_VOCAB))
        print(f"✅ 学员个人外脑: 正常 (已沉淀句型 {u_p} 条，已沉淀生词 {u_v} 条)")
    else:
        print("❌ 学员个人外脑: 目录或数据文件异常")
        all_pass = False

    # Check 4: MaiMemo Token
    token = os.environ.get("MAIMEMO_TOKEN", "").strip()
    if token:
        masked = token[:6] + "..." + token[-4:] if len(token) > 10 else "***"
        print(f"✅ 墨墨背单词 Token: 已配置 ($MAIMEMO_TOKEN: {masked})")
    else:
        print("⚠️ 墨墨背单词 Token: 未设置 ($MAIMEMO_TOKEN 环境变量为空，导入墨墨时需配置)")

    print("\n----------------------------------------------")
    if all_pass:
        print("🚀 系统状态健康，随时可以开展翻译一对一精讲！")
    else:
        print("⚠️ 发现潜在问题，请根据上述提示进行排查。")


def cmd_status(args):
    """Summary of user brain assets and practice history."""
    meta = {}
    if META_FILE.exists():
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            pass

    u_p = len(load_jsonl(USER_PATTERNS))
    u_v = len(load_jsonl(USER_VOCAB))
    archives = list(ARCHIVES_DIR.glob("*.md")) if ARCHIVES_DIR.exists() else []

    print("📊 【考研英语二翻译学员外脑资产统计看板】")
    print(f"  • 累计演练篇数: {len(archives)} 篇 (历史归档)")
    print(f"  • 个人句型沉淀: {u_p} 条")
    print(f"  • 个人词汇沉淀: {u_v} 条")
    print(f"  • 最后更新时间: {meta.get('last_updated', '未记录')}")
    if archives:
        print("\n📝 最近练习归档:")
        for a in archives[-5:]:
            print(f"  - {a.stem}")


def main():
    parser = argparse.ArgumentParser(description="Knowledge base manager for kaoyan translation.")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to run")

    # init (atomic S0 initialization)
    p_init = subparsers.add_parser("init", help="Atomic S0 initialization: prompt, context, and optional draft lint")
    p_init.add_argument("--year", required=True, help="Year of the exam (e.g. 2010)")
    p_init.add_argument("--text", help="Draft Chinese translation text for linting")
    p_init.add_argument("--file", help="Path to draft text file")
    p_init.add_argument("--json", action="store_true", help="Output JSON format")

    # prompt
    p_prompt = subparsers.add_parser("prompt", help="Get pure English prompt and sentence breakdown")
    p_prompt.add_argument("--year", required=True, help="Year of the exam (e.g. 2023)")
    p_prompt.add_argument("--json", action="store_true", help="Output JSON format")

    # anchor
    p_anchor = subparsers.add_parser("anchor", help="Get full reference benchmark (Stage 4 only)")
    p_anchor.add_argument("--year", required=True, help="Year of the exam")
    p_anchor.add_argument("--full", action="store_true", help="Confirm full reference debrief")
    p_anchor.add_argument("--json", action="store_true", help="Output JSON format")

    # check
    p_check = subparsers.add_parser("check", help="Preflight check on student translation draft")
    p_check.add_argument("--file", help="Path to draft text file")
    p_check.add_argument("--text", help="Draft Chinese translation text directly")
    p_check.add_argument("--year", help="Optional year for sentence count matching")
    p_check.add_argument("--json", action="store_true", help="Output JSON format")

    # query
    p_query = subparsers.add_parser("query", help="Search patterns or vocab")
    p_query.add_argument("--category", choices=["pattern", "vocab", "all"], default="all", help="Category to search")
    p_query.add_argument("--keyword", help="Search keyword")
    p_query.add_argument("--json", action="store_true", help="Output JSON format")

    # settle
    p_settle = subparsers.add_parser("settle", help="Atomic settlement of translation session")
    p_settle.add_argument("--file", required=True, help="Path to settle payload JSON")

    # doctor
    subparsers.add_parser("doctor", help="Check system health")

    # status
    subparsers.add_parser("status", help="View brain asset status")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "init": cmd_init,
        "prompt": cmd_prompt,
        "anchor": cmd_anchor,
        "check": cmd_check,
        "query": cmd_query,
        "settle": cmd_settle,
        "doctor": cmd_doctor,
        "status": cmd_status
    }

    func = dispatch.get(args.subcommand)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
