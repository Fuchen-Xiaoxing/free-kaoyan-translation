#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_kb_manager.py - Unit test suite for kb_manager.py
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
KB_MANAGER = PROJECT_ROOT / "scripts" / "kb_manager.py"


class TestKBManager(unittest.TestCase):

    def run_cmd(self, *args):
        cmd = [sys.executable, str(KB_MANAGER)] + list(args)
        res = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return res

    def test_01_doctor(self):
        res = self.run_cmd("doctor")
        self.assertEqual(res.returncode, 0, f"doctor command failed: {res.stderr}")
        self.assertIn("真题标尺库: 正常", res.stdout)
        self.assertIn("种子规则库: 正常", res.stdout)
        self.assertIn("学员个人外脑: 正常", res.stdout)

    def test_02_status(self):
        res = self.run_cmd("status")
        self.assertEqual(res.returncode, 0, f"status command failed: {res.stderr}")
        self.assertIn("学员外脑资产统计看板", res.stdout)

    def test_03_prompt(self):
        # Test 2023 prompt
        res = self.run_cmd("prompt", "--year", "2023", "--json")
        self.assertEqual(res.returncode, 0, f"prompt 2023 failed: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["year"], "2023")
        self.assertIn("Wordsworth", data["source_text"])
        self.assertGreaterEqual(len(data["sentences"]), 5)
        # Verify physical isolation: reference_translation must NOT be present
        self.assertNotIn("reference_translation", data)

    def test_04_anchor_requires_full(self):
        # Anchor without --full should be rejected with code 2
        res = self.run_cmd("anchor", "--year", "2023")
        self.assertEqual(res.returncode, 2)

        # Anchor with --full should succeed
        res_full = self.run_cmd("anchor", "--year", "2023", "--full", "--json")
        self.assertEqual(res_full.returncode, 0)
        data = json.loads(res_full.stdout)
        self.assertIn("reference_translation", data)
        self.assertIn("华兹华斯", data["reference_translation"])

    def test_05_check_draft(self):
        tmp_draft = PROJECT_ROOT / "tmp_draft_test.txt"
        try:
            # Case 1: Valid draft for 2023
            valid_text = (
                "18世纪末，威廉·华兹华斯因其关于大自然的诗歌而闻名于世。“他是浪漫主义运动的创始人之一，”"
                "该运动歌颂了大自然的美妙与奇观。诗歌富有感染力。它的能量与韵律可以打动读者，"
                "带他们进入另一个世界，让他们以不同的视角看待事物。通过精心挑选的词句，诗歌可以极具戏剧性、"
                "幽默、优美、动人并富有启发性。没有人确切知道诗歌何时起源，但它已经流传了数千年。"
            )
            with open(tmp_draft, "w", encoding="utf-8") as f:
                f.write(valid_text)

            res = self.run_cmd("check", "--file", str(tmp_draft), "--year", "2023")
            self.assertEqual(res.returncode, 0)
            self.assertIn("通过项", res.stdout)
            self.assertIn("约定俗成专名命中", res.stdout)

            # Case 2: Short draft with missing proper noun
            short_text = "写了一首诗。“引号未闭合"
            with open(tmp_draft, "w", encoding="utf-8") as f:
                f.write(short_text)

            res_short = self.run_cmd("check", "--file", str(tmp_draft), "--year", "2023")
            self.assertEqual(res_short.returncode, 0)
            self.assertIn("字数偏少", res_short.stdout)
            self.assertIn("不闭合", res_short.stdout)
        finally:
            if tmp_draft.exists():
                tmp_draft.unlink()

    def test_06_query(self):
        # Query pattern
        res_p = self.run_cmd("query", "--category", "pattern", "--keyword", "定从", "--json")
        self.assertEqual(res_p.returncode, 0)
        items_p = json.loads(res_p.stdout)
        self.assertGreaterEqual(len(items_p), 1)

        # Query vocab
        res_v = self.run_cmd("query", "--category", "vocab", "--keyword", "celebrate", "--json")
        self.assertEqual(res_v.returncode, 0)
        items_v = json.loads(res_v.stdout)
        self.assertGreaterEqual(len(items_v), 1)
        self.assertIn("歌颂", items_v[0]["data"]["translation_meaning"])

    def test_07_settle_atomic(self):
        tmp_settle = PROJECT_ROOT / "tmp_settle_test.json"
        payload = {
            "task_id": "TEST_T9999_TRANS",
            "year": "9999",
            "exam_type": "English II",
            "title": "测试翻译归档",
            "basic_translation": "这是测试基础译文。",
            "advanced_translation": "这是测试高分地道润色译文。",
            "score_estimate": {
                "total_score": 13.0,
                "max_score": 15.0,
                "deductions": [{"item": "无明显硬伤", "penalty": 0}]
            },
            "batch": {
                "new_patterns": [
                    {
                        "id": "PAT_TEST_01",
                        "pattern_name": "测试句型",
                        "structure": "A -> B",
                        "principle": "测试原理",
                        "example_en": "Test EN",
                        "example_cn": "测试中文",
                        "category": "测试"
                    }
                ],
                "new_vocab": [
                    {
                        "word": "testword",
                        "translation_meaning": "测试释义",
                        "general_meaning": "测试常用",
                        "tone": "中性",
                        "exam_trap": "测试避坑"
                    }
                ]
            }
        }
        try:
            with open(tmp_settle, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)

            res = self.run_cmd("settle", "--file", str(tmp_settle))
            self.assertEqual(res.returncode, 0, f"settle failed: {res.stderr}")
            self.assertIn("原子结算成功", res.stdout)

            # Verify files written
            archive_file = PROJECT_ROOT / "knowledge_base" / "user_brain" / "archives" / "TEST_T9999_TRANS.md"
            self.assertTrue(archive_file.exists())
            with open(archive_file, "r", encoding="utf-8") as af:
                c = af.read()
                self.assertIn("TEST_T9999_TRANS", c)
                self.assertIn("测试高分地道润色译文", c)

            # Cleanup test artifacts
            archive_file.unlink()
        finally:
            if tmp_settle.exists():
                tmp_settle.unlink()

    def test_08_init_atomic(self):
        # 1. Init without draft
        res = self.run_cmd("init", "--year", "2010", "--json")
        self.assertEqual(res.returncode, 0, f"init 2010 failed: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["year"], "2010")
        self.assertIn("Sustainability", data["source_text"])
        self.assertEqual(len(data["sentences"]), 10)
        self.assertIsNone(data["draft_lint"])
        self.assertNotIn("reference_translation", data)

        # 2. Init with draft text
        draft_text = "如今，“可持续性”已经成为一个热门词语，但对泰德·宁来说，这个概念始终具有个人意义。"
        res_lint = self.run_cmd("init", "--year", "2010", "--text", draft_text, "--json")
        self.assertEqual(res_lint.returncode, 0)
        data_lint = json.loads(res_lint.stdout)
        self.assertIsNotNone(data_lint["draft_lint"])
        self.assertIn("ted ning", str(data_lint["draft_lint"]["passes"]).lower())

    def test_09_check_with_text(self):
        # Check draft with --text
        draft_text = (
            "18世纪末，威廉·华兹华斯因其关于大自然的诗歌而闻名于世。“他是浪漫主义运动的创始人之一，”"
            "该运动歌颂了大自然的美妙与奇观。诗歌富有感染力。它的能量与韵律可以打动读者，"
            "带他们进入另一个世界，让他们以不同的视角看待事物。通过精心挑选的词句，诗歌可以极具戏剧性、"
            "幽默、优美、动人并富有启发性。没有人确切知道诗歌何时起源，但它已经流传了数千年。"
        )
        res = self.run_cmd("check", "--text", draft_text, "--year", "2023", "--json")
        self.assertEqual(res.returncode, 0, f"check --text failed: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertGreaterEqual(data["char_count"], 150)
        self.assertTrue(any("约定俗成专名命中" in p for p in data["passes"]))
        self.assertTrue(any("字数达标" in p for p in data["passes"]))


if __name__ == "__main__":
    unittest.main()
