---
name: inventory-shortage-check
description: 对比已给定的物料需求、现存、已分配与在途数量，计算简单缺料及对在途的依赖；适用于制造业备料分析，不替代正式 MRP 或采购审批。
---

# 库存缺料分析

先确认需求与库存数据的时间点、单位、库存范围以及在途是否包含可靠到货信息。需要用户提供完整数值，不要把未知库存当作零。

1. 需求 JSON 格式为 `{"demand":[{"code":"...","name":"...","unit":"...","quantity":"..."}]}`，也可使用 `bom-material-planning` 脚本结果。库存格式参照 `examples/inventory.json`，每条包括 code、unit、on_hand、allocated、on_order。
2. 执行 `python <本技能目录>/scripts/check_shortage.py DEMAND.json INVENTORY.json`，可用 `--output` 保存 JSON。按 `现存 - 已分配 + 在途` 得到账面净可用量，缺口不小于零；同时列出不考虑在途时的缺口。
3. 汇报短缺项、依赖在途项、数据缺失项、单位不一致项。缺失记录与单位不一致必须标为“待核实”，不能给出数字结论。已分配大于现存时显示预警；不要擅自调整数据。
4. 说明本结果不考虑到货日期、替代料、批次、锁库归属、安全库存、最小采购量和采购周期。建议用户核查后再执行采购，不创建采购单。
