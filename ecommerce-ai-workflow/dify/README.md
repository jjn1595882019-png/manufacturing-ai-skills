# Dify 可视化商品上新工作流

这是与仓库 Python 示例对应的 Dify DSL 草稿：`product-listing-workflow.yml`。文件使用 JSON 格式书写（JSON 是 YAML 的子集），扩展名为 `.yml`，便于在 Dify 的 DSL 导入入口选择。

```text
开始：商品资料 JSON
  → 代码：校验输入及事实 ID
  → LLM：基于资料生成结构化标题、卖点、详情
  → 代码：校验 JSON / 事实 ID / 风险词，输出审核提示
  → 结束：draft + review
```

## 当前验证状态

2026-11-21，在 Dify Cloud 工作空间通过 URL 导入成功，五个节点与连线正常显示；使用工作空间提供的 `gpt-4o-mini` 和虚构收纳盒资料完成两次测试运行，均返回草稿与“待人工审核”状态。导入和运行结果只对这次使用的 Cloud 环境及测试样例有效；其他版本、模型和资料仍需重新验证。

两次测试均暴露了事实约束不足：第一次模型由“塑料”推断“轻便耐用”；收紧提示词后，第二次仍生成资料未证明的“便于清洁”。代码只能检查引用 ID 是否存在，**不能判断事实是否支持文案**，风险词表也无法覆盖这些情况。该工作流必须人工核查，不得宣称可以自动审核通过。

## 导入并测试

1. 准备一个可登录的 Dify 环境，并确认允许导入 DSL；在工作室中选择从 DSL 文件导入，选择本目录的 `product-listing-workflow.yml`。界面名称可能随版本变化。
2. 打开“生成文案草稿”节点。文件中 `gpt-4o-mini` / OpenAI provider 是模型示例，**不包含密钥或可用额度**；按你的 Dify 环境安装/选择支持的模型供应商，配置自己的模型，然后在该节点重新选择模型。
3. 进入调试，打开上一级目录 `examples/product.json`，复制整个 JSON 到“商品资料 JSON”输入框，运行工作流。
4. 查看 `draft` 和 `review`，核查引用的事实 ID 与原商品资料是否真正一致，并检查缺失信息。模型输出不是有效 JSON、缺少引用或引用不存在的事实时，代码节点将报错停止；调整模型或提示词后重试。
5. 需分享画布时，可保存自己的脱敏截图或演示视频；确认结果后才在 Dify 中发布。此示例不会自动上架商品。

## 隐私与费用

模型运行会将输入的商品资料发送给你配置的模型服务商，可能产生费用；不要放客户敏感信息或真实密钥。只有预设词匹配的简单提示，**不能保证文案真实或合规**；输出永远是待人工审核草稿。没有接入 RAG、店铺、数据库或人审审批系统。

## 文件

- `product-listing-workflow.yml`：待导入 DSL。
- `build_dsl.py`：生成上述 DSL 的源码；修改后运行 `python build_dsl.py` 重新生成。
- `../examples/product.json`：虚构商品输入样例。
- `../tests/test_dify_dsl.py`：本地 DSL 节点与代码逻辑检查，不是 Dify 集成测试。

参考：[Dify 工作流示例](https://github.com/langgenius/dify/issues/15162)、[代码节点及结束节点 DSL 示例](https://github.com/aws-samples/dify-aws-tool/blob/main/workflow/term_based_translation_workflow.yml)。
