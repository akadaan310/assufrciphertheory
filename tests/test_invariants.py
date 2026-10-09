# -*- coding: utf-8 -*-
"""الثوابت اللي ما لازم تنكسر بأي تعديل: النص، المواقع، التصنيف، وسجلّ اللآلئ.

    python3 -m unittest discover -s tests
"""
import hashlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lab"))
import build  # noqa: E402
import experiments  # noqa: E402
import quran  # noqa: E402
import sites  # noqa: E402

TANZIL_SHA256 = {
    "tanzil-uthmani.txt": "6933e133dd56db778c801bf738848454e43648105a151e8d84d86a7cae39ec5f",
    "tanzil-simple-clean.txt": "054b3d9f79c0c2e44df7f9ddf42561797b3b5cb4fbdafbf2e99c805ccf1a6b49",
}


class TestText(unittest.TestCase):
    def test_tanzil_files_unchanged(self):
        # شروط تنزيل: ممنوع تغيير النص. أي تغيير على الملف بيفشّل الاختبار.
        for name, digest in TANZIL_SHA256.items():
            with open(os.path.join(quran.QDIR, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)

    def test_counts(self):
        q = quran.load()
        self.assertEqual(len(q.uthmani), 6236)
        self.assertEqual(len(q.simple), 6236)
        self.assertEqual(sum(v["basmala_prefix_removed"] for v in q.uthmani.values()), 112)

    def test_key_verses(self):
        q = quran.load()
        self.assertEqual(q.verse(30, 1), "الٓمٓ")
        # ترتيب علامات الضبط (شدّة/ضمّة) بيختلف بين لوحات المفاتيح، فبنقارن بلا تشكيل لما نكتب النص باليد.
        self.assertEqual(quran.strip_marks(q.verse(30, 2)), "غلبت ٱلروم")
        self.assertTrue(q.verse(13, 1).startswith("الٓمٓر ۚ"))
        self.assertEqual(q.verse(42, 1), "حمٓ")
        self.assertEqual(q.verse(42, 2), "عٓسٓقٓ")
        self.assertEqual(quran.strip_marks(q.verse(77, 33)), "كأنه جملت صفر")
        self.assertIn("فى أدنى ٱلأرض", quran.strip_marks(q.verse(30, 3)))


class TestSites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = sites.build()["sites"]

    def test_twenty_nine(self):
        self.assertEqual(len(self.data), 29)
        self.assertEqual(sum(len(s["units"]) for s in self.data), 30)

    def test_shura_not_flattened(self):
        shura = next(s for s in self.data if s["sura"] == 42)
        self.assertEqual([(u["ayah"], u["letters"]) for u in shura["units"]], [(1, "حم"), (2, "عسق")])

    def test_mim_dives_in_raad_not_rum(self):
        # الثابت التحريري الأساسي: غوص الميم = المر في الرعد (١٣)، مش الم في الروم (٣٠).
        raad = next(s for s in self.data if s["sura"] == 13)
        rum = next(s for s in self.data if s["sura"] == 30)
        self.assertEqual(raad["opening"], "المر")
        self.assertEqual(raad["author_class"], "مغوصة")
        self.assertEqual(rum["opening"], "الم")
        self.assertNotEqual(rum["author_class"], "مغوصة")
        self.assertIn("الرعد", rum["notes"])

    def test_author_classification_not_extended(self):
        # ما بنخترع تصنيف للمواقع اللي ما صنّفها المؤلف.
        unresolved = {s["opening"] for s in self.data if s["author_class"] == "غير محسوم"}
        self.assertEqual(unresolved, {"طسم", "يس", "حم", "حم عسق"})
        diving = {s["opening"] for s in self.data if s["author_class"] == "مغوصة"}
        self.assertEqual(diving, {"الر", "طس", "المر", "ص"})


class TestExperiments(unittest.TestCase):
    def test_exp01_counterexamples(self):
        r = experiments.exp01()["rules"]
        self.assertEqual((r["R1"]["agree"], r["R1"]["of"]), (17, 19))
        self.assertEqual(r["R4"]["agree"], 18)

    def test_exp02_scs(self):
        r = experiments.exp02()
        self.assertEqual([x["scs"] for x in r["scs_of_alm_and_alr"]], ["الرم", "المر"])

    def test_exp03_lillah_alamr(self):
        r = experiments.exp03()
        self.assertEqual([(o["sura"], o["ayah"]) for o in r["occurrences"]], [(13, 31), (30, 4)])
        self.assertIn("يريكم البرق", r["baseline"]["pair_13_30_bigrams"])

    def test_exp04_sarh(self):
        r = experiments.exp04()
        self.assertEqual([(v["sura"], v["ayah"]) for v in r["sarh_verses"]], [(27, 44), (28, 38), (40, 36)])
        self.assertTrue(r["all_sarh_suras_are_sites"])
        self.assertEqual(r["seven_heavens_phrases"]["سبع سماوات"], [(2, 29), (41, 12), (65, 12), (67, 3), (71, 15)])


class TestPearlSkeleton(unittest.TestCase):
    def test_exp08_same_word_all_eight(self):
        # كلها نفس الكلمة على مستوى الرسم: ولا موضع منها «نتيجة كاذبة».
        r = experiments.exp08()
        self.assertEqual(len(r["occurrences"]), 8)
        self.assertTrue(r["same_skeleton_in_both_editions"])
        self.assertEqual(r["readings"]["لَوَلَّوْا"], ["9:57", "48:22"])
        self.assertEqual(len(r["readings"]["لُؤْلُؤ"]), 6)


class TestQiraat(unittest.TestCase):
    QIRAAT_SHA256 = {
        "hafsData_v18.json": "5d8bb91726e482839d0057633cb1973031e4d706fa9604eea5e08892f20ba140",
        "ShoubaData08.json": "f105da3949e0b8092e3abcd23a539c9bef4c9b7474f15d29848471f150ade667",
        "warshData_v10.json": "f05d0dc652fd46b38563cacb13242f76f80db4cc64d25873da0bce157253872f",
        "QaloonData_v10.json": "18465c40ebeec40a92eb98745c9b89796ac6e31f6e93988883dfb6602faaea95",
        "DooriData_v09.json": "169b949d6cedd93ddb21728c16057d5ac7faf673ac10e0f213bb5dec1dc90d7d",
        "SoosiData09.json": "81af638398efa88308803c06a961d7019daf2e87e822b8acae24df05a82aa81b",
        "BazziData_v07.json": "2ff11a126e0f15f161b88f83528c0b11d24f69f474baabf02d8864cd93ed15ce",
        "QumbulData_v07.json": "3a0377bd943def12711b15cc71a65214fb902a5df70240b87df13c7b516a7888",
    }

    def test_narration_files_unchanged(self):
        for name, digest in self.QIRAAT_SHA256.items():
            with open(os.path.join(ROOT, "data", "qiraat", name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)

    def test_rawm_mark_unique_in_yusuf(self):
        r = experiments.exp09()
        self.assertEqual([(v["sura"], v["ayah"]) for v in r["verses_with_mark"]], [(12, 11)])
        self.assertEqual(r["sura_opening"], "الر")
        self.assertTrue(r["rasm_is_morph_minus_one_nun"])
        self.assertTrue(r["skeleton_alrum_eq_alrawm"])

    def test_standalone_is_kufan(self):
        r = experiments.exp10()
        self.assertEqual(r["standalone_openings_per_narration"]["حفص"], 19)
        self.assertEqual(r["standalone_openings_per_narration"]["ورش"], 0)
        self.assertEqual(quran.rasm(r["rum_1_in_basri_count"]), "الم غلبت الروم")

    def test_imala_only_on_hayy_tahir(self):
        r = experiments.exp12()
        self.assertTrue(r["all_inclined_letters_in_hayy_tahir"])
        self.assertIn("\u0651", r["noon_68_1"]["ورش"])
        self.assertNotIn("\u0651", r["noon_68_1"]["حفص"])


class TestBrand(unittest.TestCase):
    def test_title_and_brand(self):
        b = json.load(open(os.path.join(ROOT, "data", "brand.json"), encoding="utf-8"))
        self.assertEqual(b["full_title"], "لؤلؤ العربية: الأَولى في اللغات العالمي، الكوني، والحسابي")
        self.assertEqual(b["brand"], "لغة اللؤلؤ واللؤلؤة")
        with open(os.path.join(ROOT, "web", "index.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn(b["title"], page)
        self.assertIn(b["brand"], page)


class TestPearls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build.build()

    def test_ids_unique_and_linked(self):
        ids = [p["id"] for p in self.data["pearls"]]
        self.assertEqual(len(ids), len(set(ids)))
        for p in self.data["pearls"]:
            for link in p["links"]:
                self.assertIn(link, ids, f"{p['id']} → {link}")

    def test_required_fields_and_status(self):
        required = ["id", "title", "refs", "author_note", "question", "rule", "operation", "expected",
                    "actual", "supporting", "counterexamples", "layers", "sources", "status"]
        for p in self.data["pearls"]:
            for k in required:
                self.assertIn(k, p, f"{p['id']} ناقصها {k}")
            self.assertIn(p["status"], self.data["statuses"], p["id"])
            self.assertEqual(set(p["layers"]), {"text", "reading", "tafsir", "model"}, p["id"])

    def test_every_ref_resolves(self):
        q = quran.load()
        for p in self.data["pearls"]:
            for s, a in p["refs"]:
                self.assertIn((s, a), q.uthmani, f"{p['id']} {s}:{a}")

    def test_no_seven_storey_tower_claim(self):
        # النص ما بيقول إن الصرح سبع طبقات؛ ما لازم أي لؤلؤة تنسبه للنص.
        for p in self.data["pearls"]:
            blob = json.dumps(p, ensure_ascii=False)
            self.assertNotIn("برج من سبع طبقات", blob.replace("أي رسم بسبع طبقات", ""))

    def test_web_data_matches_registry(self):
        with open(build.WEB_DATA, encoding="utf-8") as f:
            raw = f.read()
        payload = json.loads(raw[raw.index("= ") + 2: raw.rstrip().rindex(";")])
        self.assertEqual([p["id"] for p in payload["pearls"]], [p["id"] for p in self.data["pearls"]])


if __name__ == "__main__":
    unittest.main()
