"""Unit tests for CLI commands."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from ai_audit.cli import build_parser, main


def test_cli_parser():
    parser = build_parser()
    assert parser.prog == "ai-audit"

    # Test score command parsing
    args = parser.parse_args(["score", "--file", "data/sample_project.json"])
    assert args.command == "score"
    assert args.file == "data/sample_project.json"

    # Test financial scenario parsing
    args_fin = parser.parse_args(["financial", "--scenario", "conservative"])
    assert args_fin.command == "financial"
    assert args_fin.scenario == "conservative"


def test_cli_info_and_score_execution(capsys):
    with patch("sys.argv", ["ai-audit", "info", "--file", "data/sample_project.json"]):
        main()
    captured = capsys.readouterr()
    assert "APEX GROWTH PARTNERS" in captured.out
    assert "HubSpot CRM" in captured.out

    with patch("sys.argv", ["ai-audit", "score", "--file", "data/sample_project.json"]):
        main()
    captured = capsys.readouterr()
    assert "TRANSPARENT PRIORITISATION ENGINE" in captured.out
    assert "OPP-01" in captured.out
    assert "BLOCKED" in captured.out


def test_cli_report_generation(tmp_path: Path, capsys):
    out_dir = str(tmp_path / "cli_outputs")
    with patch("sys.argv", ["ai-audit", "report", "--file", "data/sample_project.json", "--output-dir", out_dir]):
        main()
    captured = capsys.readouterr()
    assert "REPORT GENERATION COMPLETE" in captured.out
    assert (tmp_path / "cli_outputs" / "executive_report.md").exists()
    assert (tmp_path / "cli_outputs" / "opportunity_register.csv").exists()


def test_cli_init_command(tmp_path: Path, capsys):
    init_file = str(tmp_path / "my_audit.json")
    with patch("sys.argv", ["ai-audit", "init", "Acme Advisory", "--file", init_file]):
        main()
    captured = capsys.readouterr()
    assert "Initialized new audit project" in captured.out
    assert Path(init_file).exists()
