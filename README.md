# market-order-split

母单拆分执行：先建单，再拆成子单，最后用成交回报结算。只用 Python 标准库。

```
python3 -m unittest discover -s tests
python3 -m marketx init   --state s.json --order-id o1 --side buy --qty 10 --max-child 4 --band 101:10 --band 100:10
python3 -m marketx split  --state s.json --req-id r1
python3 -m marketx settle --state s.json --req-id r2 --fill 100:3
python3 -m marketx --sample=bands|cap|replay|settle|work
```

## 口径

- **价格优劣**：买单从低价档往高价档分配，卖单从高价档往低价档分配。
- **粒度与档位**：单个子单不超过 `max_child`；每档分配量不超过该档的 `capacity`。
- **总量守恒**：子单总量 + `remaining` 始终等于母单数量；装不下的部分留在 `remaining`。
- **成交回填**：结算按价格找到还没填满的子单依次填，填不完的数量退回 `remaining`。
- **幂等**：同一个 `req_id` 的拆单或结算只生效一次。

## 不变量

- 子单数量之和不超过母单数量。
- 每档的子单数量之和不超过该档 `capacity`。
- `scanned` 不随子单数放大：两千个子单、两千笔成交回报时不超过 9000。

## 输出契约

`split` 打印 `req_id`、`status`（`ok` / `replay`）、`children`（`[price, qty]` 列表）、`remaining`、`scanned`。
`settle` 打印 `req_id`、`status`、`filled`、`remaining`、`scanned`。
`--sample=work` 只打印 `{"children": N, "fills": N, "scanned": N}`。
