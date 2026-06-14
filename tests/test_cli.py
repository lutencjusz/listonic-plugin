import pytest
from listonic.cli import build_parser


def test_json_flag_after_subcommand_stats():
    args = build_parser().parse_args(["stats", "--json"])
    assert args.json is True and args.func.__name__ == "cmd_stats"


def test_json_flag_after_subcommand_popular():
    args = build_parser().parse_args(["popular", "--top", "5", "--json"])
    assert args.json is True and args.top == 5


def test_json_flag_after_subcommand_lists():
    args = build_parser().parse_args(["lists", "--unchecked", "--json"])
    assert args.json is True and args.unchecked is True


def test_lists_checked_and_unchecked_mutually_exclusive():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["lists", "--checked", "--unchecked"])


def test_sync_history_prune_flag():
    args = build_parser().parse_args(["sync-history", "--prune"])
    assert args.prune is True and args.func.__name__ == "cmd_sync_history"


def test_sync_history_default_no_prune():
    args = build_parser().parse_args(["sync-history"])
    assert args.prune is False
