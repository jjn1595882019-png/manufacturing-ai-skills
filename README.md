# 制造业 AI Skills：让业务资料变成可检查的工作结果

面向制造业 ERP 常见场景的三个可复用 Agent Skills。技能由 `SKILL.md` 描述何时使用、输入要求和工作步骤；其中需要精确计算的环节交给 Python 标准库脚本。示例数据均为虚构，不依赖模型 API、数据库或客户资料。

另有独立的[电商商品上新 AI 工作流](ecommerce-ai-workflow/README.md)：展示商品资料校验、提示词、可选模型调用、输出核对和人工审核。默认离线演示使用模拟结果，不代表真实模型评测。

| Skill | 解决的问题 | 交付结果 |
| --- | --- | --- |
| `bom-material-planning` | 多层 BOM 在指定生产数量下需要多少基础物料 | 明细路径及按物料汇总的理论用量 |
| `inventory-shortage-check` | 按现存、已分配和在途量粗算物料缺口 | 可用量、缺口和需核实项 |
| `production-exception-handover` | 生产异常信息分散，交接容易遗漏 | 基于已有证据的异常交接单及待确认问题 |

## 运行示例

需要 Python 3.10 或更高版本，无需安装第三方依赖。在项目根目录执行：

```bash
python skills/bom-material-planning/scripts/explode_bom.py examples/bom.json --output /tmp/bom-result.json
python skills/inventory-shortage-check/scripts/check_shortage.py /tmp/bom-result.json examples/inventory.json
python -m unittest discover -s tests -v
```

Windows PowerShell 可把 `/tmp/bom-result.json` 换成 `$env:TEMP/bom-result.json`，两个命令使用同一个路径。

示例包括两条不同的产品结构路径，公共物料会合并；输出保留每条路径以便核查。缺料计算把在途量单独列出，并给出不依赖在途量的缺口，方便识别延期风险。

## 如何作为 Skill 使用

在支持 Agent Skills 的工具中，将 `skills/` 下需要的文件夹复制到该工具约定的技能目录；重新加载工具后，按其使用方式调用。也可以直接让支持读取项目文件的 AI 助手阅读相应 `SKILL.md` 并根据示例运行脚本。不同产品的 Skill 安装位置与调用方式可能不同，请查看对应产品文档。

示例：

> 根据 examples/bom.json 展开 10 台产品的物料需求，列出每种基础物料的需求来源，再结合 examples/inventory.json 分析缺料和在途依赖。

> 按 production-exception-handover Skill 整理 examples/production-exception.md，所有缺失信息单独列出，不要猜测原因。

## 边界和设计选择

- BOM 脚本仅计算给定结构中的叶子物料，不做库存抵扣、工单排程或多单位换算；单位由输入显式提供。
- 损耗使用每层 `用量 × (1 + loss_rate)`，这是示例计算口径，不等同于所有企业的工艺损耗规则。
- 缺料脚本只计算总量，不识别批次、锁库归属、替代料、到货日期或安全库存；缺少库存记录不会默认为零。
- 异常交接内容用于辅助协作，不替代质量判定、设备安全处置或企业正式审批流程。
- `SKILL.md` 是交给模型执行的操作规范，不是独立部署的 AI 服务；脚本输出是确定性的计算结果。该仓库不宣称真实企业落地或量化收益。

## 目录

```text
skills/                 三个独立的 Skill
examples/               虚构 BOM、库存及生产异常样例
tests/                  计算规则与异常输入测试
docs/                   项目介绍、面试讲解和简历素材
```
