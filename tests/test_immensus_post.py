from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops

from src.agents import a2_writer, a5_qc
from src.branding import apply_logo
from src.config import ROOT, load_config
from src.scheduler import generate_times
from src.main import weighted_rubric_sequence
from src.research import require_sources, verified_sources


class ImmensusConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = load_config()

    def test_channel_schedule_and_image(self) -> None:
        self.assertEqual(self.cfg["channel"]["id"], "@immensuspost")
        self.assertEqual(
            self.cfg["schedule"]["publish_times"],
            ["07:00"],
        )
        self.assertEqual(self.cfg["image"]["aspect_ratio"], "4:5")
        self.assertTrue((ROOT / "assets" / "logo.png").exists())

    def test_generate_times_honours_lead_hours(self) -> None:
        cfg = {
            "schedule": {
                "publish_times": ["07:00"],
                "generate_lead_hours": 13,
            }
        }
        self.assertEqual(generate_times(cfg), ["18:00"])

    def test_rubric_distribution_is_exact(self) -> None:
        self.assertEqual(
            [rubric["weight"] for rubric in self.cfg["rubrics"]],
            [80, 11, 3, 3, 3],
        )
        sequence = weighted_rubric_sequence(self.cfg["rubrics"])
        self.assertEqual(len(sequence), 100)
        self.assertEqual(Counter(sequence), Counter({0: 80, 1: 11, 2: 3, 3: 3, 4: 3}))

    def test_brand_rules_reject_old_values(self) -> None:
        bad = (
            "Immensus Cargo uchun maslahat. Avto kargo $6/kg. "
            "Avia kargo $9.9/kg. #ImmensusPost"
        )
        problems = " ".join(a5_qc._mechanical(self.cfg, bad))
        self.assertIn("noto'g'ri brend", problems)
        self.assertIn("kargo narxi", problems)

    def test_writer_receives_verified_source_links(self) -> None:
        topic = {
            "title": "1688 sotuvchi tekshiruvi",
            "research": "Rasmiy yordam sahifasidagi tavsiyalar.",
            "sources": [{"title": "Rasmiy manba", "url": "https://example.com/help"}],
        }
        prompt = a2_writer._prompt(self.cfg, self.cfg["rubrics"][0], topic, None)
        self.assertIn("https://example.com/help", prompt)
        self.assertIn("Immensus Post", prompt)

    def test_research_requires_two_trustworthy_sources(self) -> None:
        sources = [
            {"title": "Official help", "url": "https://example.com/help"},
            {"title": "Second guide", "url": "https://docs.example.org/guide#part"},
            {"title": "Social post", "url": "https://t.me/not-a-source"},
        ]
        self.assertEqual(len(verified_sources(sources)), 2)
        self.assertEqual(len(require_sources(sources, 2)), 2)
        with self.assertRaises(RuntimeError):
            require_sources(sources[:1], 2)

    def test_real_logo_is_applied(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "post.png"
            before = Image.new("RGB", (600, 750), "white")
            before.save(image_path)
            apply_logo(image_path, self.cfg, ROOT)
            after = Image.open(image_path).convert("RGB")
            self.assertEqual(after.size, (600, 750))
            self.assertIsNotNone(ImageChops.difference(before, after).getbbox())


if __name__ == "__main__":
    unittest.main()

