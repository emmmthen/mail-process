# Frontend

前端基于 `React + TypeScript + Vite` 构建，负责展示报价列表、比价结果、邮件处理和系统设置页面。

## 目录职责

- `src/`：前端源码
- `dist/`：构建产物
- `package.json`：前端项目配置
- `pnpm-lock.yaml`：依赖锁定文件

## 本地运行

```bash
cd frontend
pnpm install
pnpm run dev
```

常用命令：

- `pnpm run build`：构建生产包
- `pnpm run lint`：类型检查和静态检查
- `pnpm run preview`：预览构建结果

## 开发约定

- 页面级逻辑放在 `src/pages/`
- 可复用组件放在 `src/components/`
- API 调用放在 `src/services/`
- 类型定义放在 `src/types/`

