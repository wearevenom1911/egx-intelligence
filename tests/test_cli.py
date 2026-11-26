from egx_intelligence.cli import main


def test_daily_cli_returns_no_trade_when_unconfigured(capsys):
    assert main([]) == 0
    output = capsys.readouterr().out
    assert '"status": "NO_TRADE"' in output
    assert "not configured" in output
