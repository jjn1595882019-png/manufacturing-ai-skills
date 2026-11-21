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

本文件参考 Dify 官方及其示例仓库的 DSL 结构编写，已进行本地结构、节点引用和代码测试。**目前没有 Dify 实例，尚未实际导入、在画布中运行或测试具体版本兼容性。** 若导入时提示版本、插件或节点字段不兼容，需要根据目标 Dify 版本调整，不能把本地测试当成 Dify 端验证。

## 导入并测试

1. 准备一个可登录的 Dify 环境，并确认允许导入 DSL；在工作室中选择从 DSL 文件导入，选择本目录的 `product-listing-workflow.yml`。界面名称可能随版本变化。
2. 打开“生成文案草稿”节点。文件中 `gpt-4o-mini` / OpenAI provider 仅是示例模型占位，**不包含密钥或可用额度**；按你的 Dify 环境安装/选择支持的模型供应商，配置自己的模型，然后在该节点重新选择模型。
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
