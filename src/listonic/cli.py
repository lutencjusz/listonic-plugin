import argparse
import getpass
import json
import sys

from .client import ListonicClient, ListonicError, normalize_item
from . import history


def _print(obj, as_json):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    elif isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_login(args):
    email = args.email or input("Email Listonic: ")
    password = getpass.getpass("Hasło: ")
    ListonicClient().login(email, password)
    print("Zalogowano. Tokeny zapisane w ~/.listonic/config.json")


def cmd_lists(args):
    client = ListonicClient()
    out = []
    for lst in client.get_lists():
        items = []
        for raw in (lst.get("Items") or lst.get("items") or []):
            it = normalize_item(raw)
            if args.checked and not it["checked"]:
                continue
            if args.unchecked and it["checked"]:
                continue
            items.append(it)
        out.append({"name": lst.get("Name", ""), "items": items})
    _print(out, args.json)


def _resolve(client, list_name, item_name):
    lst = client.find_list(list_name)
    item = client.find_item(lst, item_name)
    return str(lst.get("Id", lst.get("IdAsNumber"))), item["id"]


def cmd_add(args):
    client = ListonicClient()
    lst = client.find_list(args.list)
    client.add_item(str(lst.get("Id", lst.get("IdAsNumber"))), args.item)
    print(f"Dodano '{args.item}' do listy '{args.list}'.")


def cmd_check(args):
    client = ListonicClient()
    lid, iid = _resolve(client, args.list, args.item)
    client.set_checked(lid, iid, not args.uncheck)
    print(("Odhaczono " if not args.uncheck else "Cofnięto ") + f"'{args.item}'.")


def cmd_remove(args):
    client = ListonicClient()
    lid, iid = _resolve(client, args.list, args.item)
    client.remove_item(lid, iid)
    print(f"Usunięto '{args.item}' z listy '{args.list}'.")


def cmd_sync_history(args):
    new = history.sync_history(ListonicClient())
    history.write_popular_note()
    print(f"Zalogowano {len(new)} nowych odhaczonych: {', '.join(new) if new else '—'}")


def cmd_popular(args):
    _print([{"produkt": n, "razy": c} for n, c in history.popular(top=args.top)], args.json)


def cmd_stats(args):
    _print(history.stats(), args.json)


def build_parser():
    p = argparse.ArgumentParser(prog="listonic")
    p.add_argument("--json", action="store_true", help="wyjście JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("login"); sp.add_argument("--email"); sp.set_defaults(func=cmd_login)

    sp = sub.add_parser("lists")
    sp.add_argument("--checked", action="store_true")
    sp.add_argument("--unchecked", action="store_true")
    sp.set_defaults(func=cmd_lists)

    sp = sub.add_parser("add"); sp.add_argument("list"); sp.add_argument("item"); sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("check")
    sp.add_argument("list"); sp.add_argument("item")
    sp.add_argument("--uncheck", action="store_true")
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("uncheck")
    sp.add_argument("list"); sp.add_argument("item")
    sp.set_defaults(func=cmd_check, uncheck=True)

    sp = sub.add_parser("remove"); sp.add_argument("list"); sp.add_argument("item"); sp.set_defaults(func=cmd_remove)
    sp = sub.add_parser("sync-history"); sp.set_defaults(func=cmd_sync_history)
    sp = sub.add_parser("popular"); sp.add_argument("--top", type=int, default=20); sp.set_defaults(func=cmd_popular)
    sp = sub.add_parser("stats"); sp.set_defaults(func=cmd_stats)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except ListonicError as e:
        print(f"Błąd: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
