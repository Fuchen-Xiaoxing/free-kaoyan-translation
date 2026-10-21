# 脚本接口与调用契约（按需加载）

> **加载时机**：仅当进入**阶段 3**（外脑归档 / 墨墨导入）调用脚本前，按需读取本文件。日常讲题（阶段 0-2）无需加载，保持上下文精简。
>
> ⚠️ **【强约束】AI 严禁调用 view_file / grep 查看 `scripts/` 目录下的 Python 源码文件。所有脚本调用方式、参数和 JSON Schema 完全以本契约规范为准，直接构造 JSON 与执行命令行。**

---

## 一、核心词汇墨墨一键推送：`scripts/memo_import.py`

- **命令格式**：`python3 scripts/memo_import.py --json <JSON字符串或临时文件路径> [--validate-only] [--dry-run] [--keep-json]`
- **Token 机制**：自动从环境变量 `MAIMEMO_TOKEN` 读取，无需显式传 `--token`。
- **功能特性**：
  - 批量解析 `voc_id`，未直接收录的词组自动提取核心关键词与原型二次查询，自动过滤英语虚词；
  - 比对已有学习记录，新词自动添加至待背队列（`advance=false`），已有词提升为今日提前复习；
  - 截断保护（去重后强制 ≤30 词）；
  - **自动清理**：通过临时文件路径调用成功后，默认自动删除临时文件及其变空的临时目录（`--keep-json` 可保留）。
- **输入 JSON Schema**（词汇对象数组）：
  ```json
  [
    {
      "word": "celebrate",
      "keyword": "celebrate",
      "meaning": "歌颂，赞美",
      "tone": "正向褒义",
      "source": "2023 翻译第 2 句"
    }
  ]
  ```
- **输出**：stdout 打印结构化分类报告（新加待背、提前复习、核心词提取明细、跳过虚词、无法识别）。

---

## 二、知识库与外脑管理：`scripts/kb_manager.py`

脚本统一通过 `python3 scripts/kb_manager.py <子命令>` 执行：

| 子命令 | 阶段 | 核心职责 | 命令示例 |
| :--- | :---: | :--- | :--- |
| `init` | S0 | **开场原子初始化**：一键提取真题英文原文、分句列表、题材背景；附带 `--text` 或 `--file` 时同时完成初译质检，消除多重调用 | `python3 scripts/kb_manager.py init --year 2010 [--text "<初译草稿>"]` |
| `prompt` | S0 | 提取指定年份真题英文原文、分句列表与篇章背景（物理隔离参考译文） | `python3 scripts/kb_manager.py prompt --year 2023` |
| `anchor` | S4 | 调取指定年份完整官方参考译文与三维度标尺精析（S4 解锁专用） | `python3 scripts/kb_manager.py anchor --year 2023 --full` |
| `check` | S0/S1 | 质检学员初译稿件（支持 `--text` 直接传文本或 `--file` 文件路径；字数、分句匹配、专名核对、标点闭合） | `python3 scripts/kb_manager.py check --text "<初译草稿>" [--year 2023]` |
| `query` | S0/S1 | 检索学员外脑或种子库中的翻译句型与熟词生义 | `python3 scripts/kb_manager.py query --category pattern [--keyword 定从]` |
| `settle` | S3 | 阶段 3 唯一结算入口：外脑双仓入库、整篇译文归档、元数据校验与日志记录 | `python3 scripts/kb_manager.py settle --file <settle.json>` |
| `doctor` | 排错 | 检查外脑目录、真题底座完整性、环境变量连通性 | `python3 scripts/kb_manager.py doctor` |
| `status` | 状态 | 查看外脑资产条目统计与归档历史 | `python3 scripts/kb_manager.py status` |

---

## 三、阶段 3 载荷契约 (`settle.json`)

`settle` 命令专用于本地外脑双仓入库与整篇译文归档。推荐写入临时目录或当前目录，再以 `--file settle.json` 传参：

> **说明**：字段键名保持 `basic_translation`（基于学员初译纠错的基础合规版）与 `advanced_translation`（兼顾原文风格与流畅汉语的高分润色版），底层接口与历史资产完全兼容。

```json
{
  "task_id": "T2023-E2-TRANS",
  "year": "2023",
  "exam_type": "English II",
  "title": "华兹华斯与自然诗歌",
  "basic_translation": "18世纪晚期，威廉·华兹华斯因其有关大自然的诗歌而闻名于世……",
  "advanced_translation": "18世纪末，威廉·华兹华斯凭借其歌咏大自然的诗篇而享誉文坛……",
  "score_estimate": {
    "total_score": 12.5,
    "max_score": 15.0,
    "deductions": [
      {"item": "第2句 celebrated 误译为庆祝", "penalty": -0.5},
      {"item": "第4句 时间状语未提前导致语序生硬", "penalty": -0.5}
    ]
  },
  "batch": {
    "new_patterns": [
      {
        "id": "PAT_ATTRIB_POST_01",
        "pattern_name": "长定语从句后置之代词承接式",
        "structure": "...先行词, which + 谓语... ➔ ...先行词。该/这一先行词...",
        "example_en": "a movement called Romanticism, which celebrated the wonders...",
        "example_cn": "一项名为浪漫主义的运动；该运动极力歌颂了……",
        "category": "定语从句"
      }
    ],
    "new_vocab": [
      {
        "word": "celebrate",
        "translation_meaning": "歌颂，赞美",
        "general_meaning": "庆祝",
        "tone": "正向褒义",
        "trap_warning": "切忌在文学/思想语境直译为庆祝"
      }
    ]
  }
}
```

- **退出码语义**：
  - `0`：结算成功，本地外脑已落盘；
  - `1`：运行时异常（自动回滚，零脏写入）；
  - `2`：参数或 JSON Schema 校验失败（未写入）。
