import json

from gen_tasks import generate


def test_generator_keeps_expected_out_of_workspace(tmp_path):
    csv_path = tmp_path / "bank.csv"
    csv_path.write_text(
        '"id","service_line","category","subcategory","bi_band","complexity","tool","agent_prompt","workspace","expected_behavior","expected_tool_calls","output_format","expert_time_mins","time_budget_s","gradability","verification","grading_signals","rubric","side_effect_checks","skills","reference_answer","maps_to"\n'
        '"T1","CFO","Cat","Sub","Junior","Easy","OneDrive","Prompt","inputs/, docs.csv","Behavior","1+ tool calls","Out","1","10","Deterministic","Rule","rule_based","[{""operator"": ""exact"", ""criteria"": ""Name"", ""value"": ""Acme""}]","Posted; logged","skill","","map"\n',
        encoding="utf-8",
    )
    generate(csv_path, tmp_path / "tasks")
    task_dir = tmp_path / "tasks" / "T1"
    assert (task_dir / "expected.json").exists()
    assert not list((task_dir / "workspace").rglob("expected.json"))
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    assert task["rubric"][0]["operator"] == "exact"
