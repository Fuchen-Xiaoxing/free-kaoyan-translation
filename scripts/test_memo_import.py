#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_memo_import.py - Unit test suite for memo_import.py
"""

import unittest
import json
import subprocess
import sys
import os
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMO_IMPORT = PROJECT_ROOT / "scripts" / "memo_import.py"

# Add scripts to sys.path to test internal functions
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import memo_import


class TestMemoImport(unittest.TestCase):

    def test_01_normalize_vocab_entries(self):
        raw = [
            {"word": "celebrate", "meaning": "歌颂"},
            {"word": "celebrate", "meaning": "重复项"},
            {"word": "  wonder  ", "meaning": "奇观"},
            {"word": "", "meaning": "无效项"},
            "rest upon"
        ]
        deduped, terms, dups, trunc, inval = memo_import.normalize_vocab_entries(raw)
        self.assertEqual(len(deduped), 3)
        self.assertIn("celebrate", dups)
        self.assertEqual(len(inval), 1)
        self.assertEqual(terms, ["celebrate", "wonder", "rest upon"])

    def test_02_truncation_limit(self):
        # Generate 35 items
        raw = [{"word": f"word{i}", "meaning": f"释义{i}"} for i in range(35)]
        deduped, terms, dups, trunc, inval = memo_import.normalize_vocab_entries(raw)
        self.assertEqual(len(deduped), 30)
        self.assertEqual(len(trunc), 5)

    def test_03_split_phrase_stopwords(self):
        phrase = "in the late eighteenth century"
        words, skipped = memo_import.split_phrase_into_words(phrase)
        # in, the are in PHRASE_STOPWORDS
        self.assertIn("in", [s.lower() for s in skipped])
        self.assertIn("the", [s.lower() for s in skipped])
        self.assertIn("eighteenth", words)
        self.assertIn("century", words)

    def test_04_extract_core_keyword(self):
        # regular people -> regular is core keyword, people is skipped companion
        kw, companions, stopwords = memo_import.extract_core_keyword("regular people")
        self.assertEqual(kw.lower(), "regular")
        self.assertIn("people", companions)

    def test_05_cli_validate_only(self):
        tmp_file = PROJECT_ROOT / "tmp_test_val.json"
        try:
            sample = [
                {"word": "celebrate", "meaning": "歌颂，赞美", "tone": "正向褒义", "source": "2023 翻译第 2 句"},
                {"word": "wonder", "meaning": "奇观，美妙之处", "tone": "正向褒义", "source": "2023 翻译第 2 句"}
            ]
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(sample, f, ensure_ascii=False)

            cmd = [sys.executable, str(MEMO_IMPORT), "--validate-only", "--json", str(tmp_file), "--format", "markdown"]
            res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(res.returncode, 0)
            self.assertIn("本篇核心单词与词组清单", res.stdout)
            self.assertIn("celebrate", res.stdout)
        finally:
            if tmp_file.exists():
                tmp_file.unlink()

    def test_06_cli_dry_run_auto_cleanup(self):
        tmp_file = PROJECT_ROOT / "tmp_test_dryrun.json"
        sample = [{"word": "celebrate", "meaning": "歌颂"}]
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False)

        cmd = [sys.executable, str(MEMO_IMPORT), "--dry-run", "--json", str(tmp_file)]
        res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0)
        self.assertIn("预览模式", res.stdout)
        # Note: --dry-run does not delete the json file
        self.assertTrue(tmp_file.exists())
        tmp_file.unlink()


if __name__ == "__main__":
    unittest.main()
