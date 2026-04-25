# 邮件报价抽取反馈闭环最小可行实现 TDD

## 1. 背景

本方案对应以下产品与设计文档：

- `docs/PRD/邮件报价抽取PRD.md`
- `docs/邮件报价抽取方案讨论稿.md`
- `docs/邮件报价抽取反馈闭环设计稿.md`

当前项目已经具备基础能力：

- 邮件导入
- 报价入库
- 报价列表与比价
- 系统设置

但当前实现仍主要停留在“导入后直接落库”的阶段，缺少以下关键能力：

- 邮件抽取过程可追溯
- 人工审核可回写
- 正确样本和错误样本可沉淀
- 后续策略可基于反馈调整

因此，本 TDD 的目标不是一次性做完整智能平台，而是先实现一个**最小可行闭环**：

1. 邮件导入
2. 统一重建
3. 抽取结果生成
4. 规则校验
5. 人工审核
6. 反馈回写

## 2. 方案概述

整体采用“处理过程记录 + 审核反馈记录 + 结果入库”的方式。

核心思路是：

- 邮件处理不再只产出最终 `Quote`
- 每次处理都先生成一条可审核的抽取记录
- 人工确认后，再决定是否正式入库或更新为修正后的结果
- 所有人工动作都会写入反馈记录，作为后续增强依据

### 2.1 最小闭环目标

最小版本只保证以下能力：

- 能记录原始邮件与重建后的内容
- 能记录抽取结果、来源位置、置信度
- 能记录人工确认、修改、驳回和原因
- 能把最终确认结果写入 `Quote`
- 能保留负样本，例如 `No Quote` / `暂无报价`

### 2.2 非目标

本阶段不做以下事项：

- 不训练专用模型
- 不做完整的模板画像系统
- 不做复杂策略引擎自动调参
- 不做多套强规则解析器替代
- 不追求一次覆盖所有附件格式

## 3. 输入输出定义

### 3.1 输入

输入包括：

- 邮件文件：`.eml`、`.msg`、`.txt`、`.html`、`.pdf`
- 邮件基础信息：主题、发件人、收件时间
- 附件内容：正文、表格、图片、PDF、Excel 的提取结果

### 3.2 输出

输出分为两类：

#### 3.2.1 抽取结果

至少包含以下字段：

- `part_number`
- `product_name`
- `quantity`
- `currency`
- `unit_price`
- `cny_price`
- `lead_time`
- `moq`
- `certificate`
- `shipping_term`
- `supplier_name`
- `quote_status`
- `remarks`
- `source_location`
- `confidence`

#### 3.2.2 反馈结果

至少包含以下字段：

- `review_status`：`pending` / `approved` / `corrected` / `rejected`
- `review_reason`
- `reviewed_fields`
- `final_values`
- `can_reuse_as_pattern`

### 3.3 中间表示

统一重建后的内容建议按 block 组织，例如：

- `email_meta`
- `body_text`
- `body_tables`
- `attachment_text`
- `attachment_tables`
- `ocr_text`

每个 block 必须保留来源信息，例如：

- `source_type`
- `source_name`
- `page_no`
- `sheet_name`
- `table_index`
- `line_no`

## 4. 详细设计

### 4.1 数据模型

建议新增以下核心表：

#### `email_message`

用于记录原始邮件元数据。

关键字段：

- `id`
- `subject`
- `sender`
- `received_at`
- `source_file_path`
- `source_type`
- `raw_status`
- `created_at`

#### `email_artifact`

用于记录清洗与重建结果。

关键字段：

- `id`
- `email_message_id`
- `cleaned_text`
- `rebuilt_text`
- `rebuilt_blocks_json`
- `extractable_status`
- `created_at`

#### `extraction_run`

用于记录一次抽取过程。

关键字段：

- `id`
- `email_message_id`
- `email_artifact_id`
- `extract_mode`
- `llm_input_snapshot`
- `llm_output_json`
- `validation_result_json`
- `confidence_score`
- `run_status`
- `created_at`

#### `review_action`

用于记录人工审核动作。

关键字段：

- `id`
- `extraction_run_id`
- `review_status`
- `review_reason`
- `reviewed_fields_json`
- `final_values_json`
- `can_reuse_as_pattern`
- `reviewer`
- `reviewed_at`

### 4.2 状态流转

建议状态流转如下：

1. `received`
2. `cleaned`
3. `rebuilt`
4. `extracted`
5. `validated`
6. `pending_review`
7. `approved` / `corrected` / `rejected`
8. `committed`

其中：

- `pending_review` 表示结果进入人工队列
- `committed` 表示最终结果已经写入业务报价表

### 4.3 服务拆分

建议把现有 `EmailProcessor` 拆成四个服务：

#### `Cleaner`

职责：

- 去签名
- 去免责声明
- 去历史转发头
- 去重复引用
- 去 HTML 噪声

#### `Rebuilder`

职责：

- 把正文、表格、附件提取结果整理成统一上下文
- 保留 block 来源
- 输出可供模型阅读的重建文本

#### `Extractor`

职责：

- 基于统一上下文生成结构化报价结果
- 支持单段抽取
- 为后续两段式 LLM 预留接口
- LLM 输入应基于 `rebuilt_text`，而不是原始邮件正文

#### `Validator`

职责：

- 否定语义识别：`No Quote` / `暂无报价` / `cannot quote`
- 件号合法性校验：至少有一条可用件号时才进入可入库流程
- 价格数值校验：单价、人民币价、数量应为可解析数值
- 币种一致性校验：`USD` / `CNY` / `RMB` 等必须与价格字段一致
- 来源位置校验：抽取结果应保留可追溯的 `source_location`
- 置信度打分：综合件号、价格、来源位置、语义状态进行评分

### 4.3.1 清洗与重建最小实现约定

#### `Cleaner`

职责：

- 仅做确定性清洗，不做语义改写
- 去除明显噪声：签名线、免责声明、历史转发头、重复引用段、HTML 中的 `script/style`
- 保留业务信息：件号、数量、单价、币种、交期、MOQ、表格内容
- 对 HTML 内容保留可解析的结构信息，不应直接扁平成纯文本

#### `Rebuilder`

职责：

- 将清洗后的内容整理为统一上下文
- 最少输出以下 block：
  - `email_meta`
  - `body_text`
  - `body_tables`
  - `attachment_text`
  - `attachment_tables`
  - `ocr_text`
- 每个 block 必须带来源信息：
  - `source_type`
  - `source_name`
  - `page_no`
  - `sheet_name`
  - `table_index`
  - `line_no`
- `rebuilt_text` 应作为模型主要输入，`rebuilt_blocks_json` 作为追溯依据
- `rebuilt_text` 不是原文复制，而是适合阅读与抽取的结构化上下文

#### 与抽取器的关系

- `Extractor` 不直接依赖原始邮件文本
- `Extractor` 应优先消费 `Rebuilder` 产出的 `rebuilt_text`
- 若 `Rebuilder` 缺失某些 block，也应保证最小可用文本可抽取
- 后续两段式 LLM 方案应复用同一套 `rebuilt_text`

### 4.4 API 设计

建议新增以下接口：

#### 邮件处理

- `POST /api/emails/import`
  - 上传单封邮件
  - 返回 `extraction_run_id` 和待审核状态

- `POST /api/emails/import/batch`
  - 批量导入邮件
  - 返回批量任务统计

#### 审核相关

- `GET /api/reviews/pending`
  - 获取待审核列表

- `GET /api/reviews/{extraction_run_id}`
  - 获取抽取详情、重建内容和校验结果

#### 抽取详情展示方式

- 页面采用左右分栏布局
- 左侧展示上传的原邮件内容或文件预览，优先使用文件系统可直接读取的原始内容
- 右侧展示抽取数据表格，按行列呈现每一条报价结果
- 右侧每一行都应支持用户标记：
  - 是否置信
  - 是否可作为最终结果
- 用户可在右侧直接选择某一行作为最终提交结果，也可保留为待确认

- `POST /api/reviews/{extraction_run_id}/approve`
  - 确认抽取结果并写入 `Quote`

- `POST /api/reviews/{extraction_run_id}/correct`
  - 修改字段后写入 `Quote`

- `POST /api/reviews/{extraction_run_id}/reject`
  - 驳回并记录原因

#### 审核队列管理

- 审核队列页应提供删除按钮，用于移除不需要继续处理的审核记录
- 删除应保留最小审计痕迹，避免误删后无法追踪
- 审核状态建议至少包含以下几种：
  - `pending_review`：未审核
  - `rejected`：未通过
  - `approved`：已通过
- 若用户已进入审核流程，但未最终提交通过/驳回结果，则状态应回到 `pending_review`
- 状态更新应以“最终提交动作为准”，避免半完成操作污染队列

#### 反馈统计

- `GET /api/feedback/summary`
  - 返回人工修改率、拒绝率、No Quote 命中率等基础指标

### 4.6 Prompt 与模型约束

#### `LLM` 输入约束

- 仅输入 `rebuilt_text`
- 提示词中要明确说明这是“清洗 + 重建后”的内容
- 强调优先使用表格块和来源位置

#### `LLM` 输出约束

- 输出必须是 JSON
- `quote_status` 只能是 `quoted` / `no_quote` / `unknown`
- `quotes` 必须是数组
- 允许部分字段为空，但不得编造不存在的信息

#### `LLM` 使用原则

- 不把币种换算逻辑交给模型自由发挥
- 不把清洗、重建与抽取混在一个大 prompt 中
- prompt 目标是稳定抽取，不是做解释型分析

### 4.5 前端页面

建议新增一个审核页，至少包含：

- 待审核列表
- 抽取结果预览
- 来源 block 预览
- 字段编辑表单
- 通过 / 修改 / 驳回按钮
- 错误原因选择

当前已有的报价列表页和比价页可以继续保留，不需要推翻重做。

## 5. 核心实现

### 5.1 处理主流程

推荐处理流程如下：

1. 接收邮件文件
2. 保存原始输入
3. 进行确定性清洗，保留可追溯内容
4. 将正文、表格、附件、OCR 结果统一重建为 block 化上下文
5. 生成抽取结果
6. 进行规则校验
7. 生成待审核记录
8. 人工确认后入库或修正

### 5.2 `No Quote` 处理

对于“暂无报价”“No Quote”“cannot quote”等否定语义：

- 不直接当作失败
- 应写入一条负样本抽取记录
- `quote_status` 标记为 `no_quote`
- `part_number` 可置空或按业务规则处理

这样可以保留高价值负样本，后续用于风险分流和模板识别。

### 5.3 Schema 约束

抽取层必须采用固定 Schema 输出，禁止自由文本结果。

建议至少约束：

- 必填字段：`supplier_name`、`quote_status`
- 条件字段：当 `quote_status=quoted` 时，`part_number` 和 `unit_price` 至少要有其一，并且应尽量完整
- 来源字段：每个结果都必须有 `source_location`
- 置信度：必须输出数值或分档

### 5.4 入库策略

建议按照审核状态决定是否写入 `Quote`：

- `approved`：直接写入
- `corrected`：写入修正后的结果
- `rejected`：不写入业务表，仅保留反馈记录

如果后续存在自动通过策略，也应只是在“进入审核队列前”做分流，不改变审核结果的记录方式。

## 6. 异常与容错

### 6.1 输入异常

- 无正文
- 无附件
- 文件损坏
- 解析失败

处理方式：

- 保留原始文件记录
- 标记为 `parse_failed`
- 进入人工队列

### 6.2 抽取异常

- LLM 输出不符合 Schema
- 抽取字段缺失
- 来源位置缺失

处理方式：

- 标记为 `extract_failed`
- 保留原始输出
- 不直接入库

### 6.3 校验异常

- 件号格式不合法
- 价格不是有效数字
- 币种与价格不一致
- 多条矛盾报价

处理方式：

- 结果进入人工复核
- 给出校验告警

### 6.4 幂等性

同一封邮件重复导入时，应尽量避免重复入库。

建议通过以下组合做幂等控制：

- `source_file_hash`
- `message_id`
- `received_at`
- `supplier_name + part_number + unit_price`

## 7. 性能与成本

### 7.1 处理成本目标

最小版本优先保证可用性，不优先优化极致吞吐。

建议控制目标：

- 单封邮件处理可以接受秒级到十几秒级
- 复杂附件解析允许异步处理
- 批量导入允许逐封落库

### 7.2 成本优化方向

- 先清洗再重建，减少无效 token
- 简单场景单次抽取
- 复杂场景再启用两段式抽取
- 相似样本复用后续再做

## 8. 监控与日志

建议记录以下指标：

- 邮件导入成功率
- 抽取成功率
- 人工修改率
- 人工驳回率
- `No Quote` 命中率
- 待审核堆积量
- 规则校验失败率

建议记录以下日志内容：

- 原始输入文件标识
- 重建后的 block 内容
- LLM 输入与输出
- 规则校验结果
- 人工审核结果
- 最终入库结果

## 9. 风险与权衡

### 9.1 风险

- 重建层质量不足会影响抽取准确率
- 审核页过重会拖慢前期落地
- 负样本记录不完整会影响后续策略

### 9.2 权衡

本方案选择先做最小闭环，而不是直接做复杂策略引擎，原因是：

- 目前系统缺少反馈基础数据
- 没有审核闭环就没有持续学习
- 先跑通闭环比先做“聪明”更重要

### 9.3 后续可演进方向

- 引入相似样本检索
- 引入模板画像
- 引入风险分级自动分流
- 引入两段式 LLM
- 引入更细粒度字段级反馈

## 10. 落地顺序

### 第一步

- 新增数据表
- 打通抽取记录与审核记录

### 第二步

- 重构邮件处理服务
- 支持统一重建和基础校验

### 第三步

- 上线审核页和回写接口
- 完成最小闭环

### 第四步

- 接入反馈统计
- 再考虑策略增强和相似样本复用
