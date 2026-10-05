"""命令行入口。"""

import argparse
import json

from . import core


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)


def _bands(pairs):
    out = []
    for pair in pairs or []:
        price, sep, cap = pair.partition(":")
        if not sep:
            raise SystemExit("--band 需要 price:capacity 形式：" + pair)
        out.append((int(price), int(cap)))
    return out


def _fills(pairs):
    out = []
    for pair in pairs or []:
        price, sep, qty = pair.partition(":")
        if not sep:
            raise SystemExit("--fill 需要 price:qty 形式：" + pair)
        out.append((int(price), int(qty)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="marketx")
    ap.add_argument("--sample", choices=["bands", "cap", "replay", "settle", "work"])
    sub = ap.add_subparsers(dest="cmd")

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--state", required=True)
    init_parser.add_argument("--order-id", required=True)
    init_parser.add_argument("--side", choices=["buy", "sell"], default="buy")
    init_parser.add_argument("--qty", type=int, required=True)
    init_parser.add_argument("--max-child", type=int, required=True)
    init_parser.add_argument("--band", action="append", default=[])

    split_parser = sub.add_parser("split")
    split_parser.add_argument("--state", required=True)
    split_parser.add_argument("--req-id", required=True)

    settle_parser = sub.add_parser("settle")
    settle_parser.add_argument("--state", required=True)
    settle_parser.add_argument("--req-id", required=True)
    settle_parser.add_argument("--fill", action="append", default=[])

    args = ap.parse_args(argv)
    if args.sample:
        from . import samples
        return samples.run(args.sample)
    if args.cmd is None:
        ap.print_help()
        return 2

    if args.cmd == "init":
        state = core.new_state(args.order_id, args.side, args.qty, args.max_child, _bands(args.band))
        _save(args.state, state)
        print(json.dumps({"order_id": args.order_id, "qty": args.qty}, ensure_ascii=False))
        return 0

    state = _load(args.state)
    counter = core.Counter()
    if args.cmd == "split":
        out = core.split(state, args.req_id, counter)
    else:
        out = core.settle(state, args.req_id, _fills(args.fill), counter)
    _save(args.state, state)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
