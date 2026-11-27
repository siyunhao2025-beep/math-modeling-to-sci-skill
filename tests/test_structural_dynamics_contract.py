from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StructuralDynamicsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = (ROOT / "references" / "model-validation-matrix.md").read_text(encoding="utf-8")
        cls.provenance = (ROOT / "references" / "provenance.md").read_text(encoding="utf-8")

    def test_claim_classes_are_kept_separate(self):
        for token in (
            "dynamic_event",
            "equilibrium_instability",
            "fold_or_branch_bifurcation",
            "post_event_landing",
        ):
            self.assertIn(token, self.matrix)

    def test_explicit_solver_evidence_is_bounded(self):
        for token in (
            "meaningful_nonzero_energy_window",
            "loading_rate_sensitivity",
            "mesh_sensitivity",
            "solver_exit_code_only_is_insufficient",
        ):
            self.assertIn(token, self.matrix)
        self.assertIn("力降或开口只能标记事件候选，不能单独证明分岔", self.matrix)

    def test_equilibrium_and_landing_claims_have_distinct_evidence(self):
        self.assertIn("约束或接触可行方向上的切线模态", self.matrix)
        self.assertIn("分支延拓", self.matrix)
        self.assertIn("接触、阻尼和加载协议", self.matrix)

    def test_source_and_independent_implementation_are_recorded(self):
        self.assertIn("DJDeborah/research-mechanics-skills", self.provenance)
        self.assertIn("b3ad6a18c40199ff49ea9f33522d9c670eb4fb05", self.provenance)
        self.assertIn("未复制其代码、提示词、模板或求解器资产", self.provenance)


if __name__ == "__main__":
    unittest.main()
