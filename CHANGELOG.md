# Changelog - free-kaoyan-translation

All notable changes to the `free-kaoyan-translation` skill will be documented in this file.

## [1.0.0] - 2026-10-06

### Initial Release (考研英语二翻译一对一私教初始化发布)

- **核心定位与十大铁律**：
  - 角色确立：考研英语二翻译（Section Ⅲ Translation，满分 15 分，约 150 词微语篇）一对一私教。
  - 唐静“拆分与组合”第一性原理：抓主干、锁动词、标生词，把“大树砍成竹节”。
  - 双版递进隔离原则：基础合规版（字字落实，踩实采分点，消除死线，保底 10 分）与高分地道润色版（说人话，意合竹节，融汇八大技巧，冲刺 13~15 分）。
  - 单步推进铁律、绝对零 Emoji 原则、零音标原则、教学纯粹性绝对红线。
- **15 年真题标尺底座 (2010~2024)**：
  - 完整解析并结构化 15 年英二翻译真题至 `knowledge_base/anchors/translation_past_papers.jsonl`，包含逐句英汉对照、采分点与词汇考点。
- **外脑双仓与种子库**：
  - 预置经典长难句转化骨架种子 (`translation_patterns.seed.jsonl`) 与高频熟词生义种子 (`translation_vocab.seed.jsonl`)。
  - 初始化本地个人外脑目录结构 (`patterns.jsonl`, `vocab.jsonl`, `archives/`, `.kb_meta.json`, `history.log`)。
- **参考规范系统 (`references/`)**：
  - `methodology.md`: 考研英二翻译核心方法论、三大评卷原则、四大死线与 15 分钟考场节奏。
  - `grammar_patterns.md`: 定从后置三式、形式主宾、同位语、状语颠倒律、被动四破法。
  - `eight_techniques.md`: 专名四律、代词还原、熟词生义、名转动、增减词、调序、被动转主动、读出声法则。
  - `style_and_rubrics.md`: 私教教学风格规范、15 分制采分阶梯与 6 项译后死线自查清单。
  - `script_contracts.md`: CLI 命令调用契约与 JSON Schema 规范。
  - `maimemo_api.md`: 墨墨背单词 Open API 纯单词推送机制规范。
- **核心工具与测试套件 (`scripts/`)**：
  - `kb_manager.py`: 支持 `prompt`, `anchor`, `check`, `query`, `settle`, `doctor`, `status` 命令。
  - `memo_import.py`: 对齐阅读理解 Skill，自动比对学习记录进行新词待背/旧词复习分流推送与临时文件自愈清理。
  - `test_kb_manager.py`: 7 项自动化单元测试，100% 通过。
  - `test_memo_import.py`: 6 项自动化单元测试，100% 通过。
