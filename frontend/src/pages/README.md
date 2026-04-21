# Pages

这里存放页面级组件，对应路由视图和业务场景。

## 当前页面

- `QuoteList.tsx`：报价列表
- `QuoteComparison.tsx`：比价视图
- `EmailProcessing.tsx`：邮件处理页面
- `EmailImport.tsx`：邮件导入页面
- `Settings.tsx`：系统设置页面

## 约定

- 页面负责数据拉取、状态编排和组件组合
- 可复用 UI 逻辑应下沉到 `components/`
- 与后端交互优先通过 `services/`

