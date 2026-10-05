"""固定场景，用来复现题面里的锚点。"""

import json

from . import core


def _line(obj):
    print(json.dumps(obj, ensure_ascii=False))


def run(name):
    if name == "bands":
        state = core.new_state("o1", "buy", 10, 4, [(101, 10), (100, 10)])
        out = core.split(state, "b-1", core.Counter())
        _line({"children": out["children"], "remaining": out["remaining"]})
        return 0
    if name == "cap":
        state = core.new_state("o2", "buy", 10, 10, [(100, 3), (101, 3)])
        out = core.split(state, "c-1", core.Counter())
        _line({"children": out["children"], "remaining": out["remaining"]})
        return 0
    if name == "replay":
        state = core.new_state("o3", "buy", 10, 4, [(100, 10)])
        core.split(state, "r-1", core.Counter())
        second = core.split(state, "r-1", core.Counter())
        _line({"status": second["status"], "remaining": second["remaining"],
               "children": len(state["children"])})
        return 0
    if name == "settle":
        state = core.new_state("o4", "buy", 10, 4, [(100, 4), (101, 6)])
        state["children"] = [{"child_id": "c1", "price": 100, "qty": 4},
                             {"child_id": "c2", "price": 101, "qty": 4}]
        state["remaining"] = 2
        out = core.settle(state, "s-1", [(100, 10)], core.Counter())
        _line({"filled": out["filled"], "remaining": out["remaining"]})
        return 0
    if name == "work":
        state = core.new_state("o5", "buy", 2000, 1, [(100, 2000)])
        state["children"] = [{"child_id": "c%d" % i, "price": 100, "qty": 1}
                             for i in range(2000)]
        state["remaining"] = 0
        counter = core.Counter()
        for i in range(2000):
            core.settle(state, "w-%d" % i, [(100, 1)], counter)
        _line({"children": 2000, "fills": 2000, "scanned": counter.scanned})
        return 0
    raise SystemExit("未知场景：" + name)
