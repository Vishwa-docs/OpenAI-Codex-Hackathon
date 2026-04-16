from services.worker.app.cli import main


def test_cli_scan_json_smoke(capsys) -> None:
    code = main(["scan", "demo-systems/legacycart", "--json"])
    captured = capsys.readouterr()
    assert code == 0
    assert '"scan_id"' in captured.out
    assert '"LegacyCart"' in captured.out

