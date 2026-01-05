# 心理测评综合管理系统 (示例后台)

本示例提供一个 FastAPI 后端，支持超级管理员、部门管理员、病人三种角色的心理测评管理流程。可在局域网内通过 uvicorn 部署，提供 REST API 供 PC、平板、手机端调用。

## 快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动开发服务器（默认端口 8000，可在局域网内访问）

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 访问自动文档
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 角色与关键接口

- **超级管理员**
  - 初始化账号：`POST /bootstrap/super-admin`
  - 创建部门：`POST /admin/departments`
  - 创建部门管理员：`POST /admin/departments/{department_id}/admins`
  - 导入/创建量表与题目：`POST /admin/scales`

- **部门管理员（医生/护士）**
  - 创建病人账号：`POST /department/patients`
  - 为病人下放量表：`POST /department/assignments`
  - 配置报告查看/表头：`PATCH /department/assignments/{id}/report-settings`

- **病人**
  - 查看自己的任务：`GET /patient/assignments`
  - 提交量表作答：`POST /patient/assignments/{id}/responses`

> 所有接口通过 `X-User-Id` 与 `X-User-Role` 请求头进行简易身份验证，示例代码未包含生产级别的登录逻辑，请在正式环境中替换为成熟的认证方案。

## 数据模型概览
- 部门（Department）
- 用户（User：超级管理员/部门管理员/病人）
- 病人资料（Patient）
- 量表与题目（Scale/ScaleItem）
- 量表任务与报告设置（ScaleAssignment）
- 病人回答（ScaleResponse）

## 提示
- 应用启动时自动创建 `psych_assessment.db`（SQLite）文件。
- 可根据需要替换为生产数据库，并扩展权限、审计、文件上传等功能。
