# 家庭健康 AI 管家 (Family Health AI Manager)

> 基于 AgentTeams 框架的多 Agent 家庭健康管理系统
>
> Datawhale AI 夏令营 2026 - Agent Infra 方向参赛作品

## 这是什么？

家庭健康 AI 管家是一个由 5 个 AI Agent 协作的家庭健康管理系统。它把"看懂医疗报告 → 管理用药 → 调整饮食 → 准备就医 → 追踪趋势"串成一个闭环，让家庭健康管理变得有条理。

## 核心创新

- **从"单次翻译"到"持续管理"**：不止看懂一次报告，而是持续追踪健康趋势
- **多 Agent 专业分工**：5 个 Agent 各司其职，有专业知识深度
- **信息自动流转**：病历翻译 → 用药检查 → 饮食建议 → 就医准备，信息自动传递
- **安全优先设计**：每个 Agent 都有安全红线，急诊识别协议，免责声明

## 团队成员

| Agent | 名字 | 职责 | 工具 |
|-------|------|------|------|
| 病历翻译官 | 小译 | 解读医疗报告，翻译术语为大白话 | medical_report.parse, medical_term.translate |
| 用药管理师 | 小药 | 管理用药时间表，检查药物相互作用 | drug_interaction.check, medication.schedule, food_drug_interaction.check |
| 营养顾问 | 小膳 | 根据疾病和用药提供个性化饮食建议 | nutrition.guidelines, food_drug_interaction.check |
| 就医导航员 | 小导 | 就医前准备清单，就医后整理医嘱 | visit_checklist.generate, medical_records.organize |
| 健康数据分析师 | 小析 | 追踪健康趋势，Team Leader 统筹全局 | health_metrics.track, health_trend.analyze |

## 协作架构

```
用户上传体检报告
        |
        v
  [小析] Team Leader 接收，分配任务
        |
        v
  [小译] 病历翻译官 解读报告
        |
        +---> 疾病信息 ---> [小药] 用药管理师 检查用药
        |                        |
        |                        +---> 药物信息 ---> [小膳] 营养顾问 生成饮食建议
        |
        +---> 异常趋势 ---> [小析] 健康分析师 预警
        |
        v
  [小导] 就医导航员 准备就医清单（需要时）
        |
        v
  [小析] 汇总所有结果，生成综合健康报告
```

## 快速开始

### 1. 启动工具服务器

```bash
cd family-health-demo
python3 tools/mock_tool_server.py --host 0.0.0.0 --port 18089
```

验证：

```bash
curl http://127.0.0.1:18089/health
# 应返回: {"ok": true, "service": "family-health-mock-tool-gateway"}
```

### 2. 安装 AgentTeams（如果还没装）

```bash
bash <(curl -sSL https://raw.githubusercontent.com/agentscope-ai/AgentTeams/main/install/agentteams-install.sh)
```

### 3. 登录 Element Web

打开浏览器访问 `http://127.0.0.1:18088`，用 admin 账号登录。

### 4. 创建 Agent

按照 `at/create_agents_messages.md` 中的步骤，在 Manager 私聊窗口中依次发送消息，创建 5 个 Worker 和 1 个 Team。

### 5. 开始使用

在 family-health-team 的 Team Room 中发送健康问题，Agent 团队会协同处理。

## 使用声明式 YAML（可选）

也可以用 YAML 文件批量创建：

```bash
bash install/agentteams-apply.sh -f yaml/workers.yaml
bash install/agentteams-apply.sh -f yaml/team.yaml
bash install/agentteams-apply.sh -f yaml/human.yaml
```

## 工具列表

| 工具名 | 功能 | 示例参数 |
|--------|------|---------|
| medical_report.parse | 解析医疗报告 | {"report_text": "...", "report_type": "体检报告"} |
| medical_term.translate | 翻译医学术语 | {"term": "高血压"} |
| drug_interaction.check | 检查药物相互作用 | {"drug_list": ["二甲双胍", "阿托伐他汀"]} |
| medication.schedule | 生成用药时间表 | {"medications": [{"name": "二甲双胍", "dose": "1片", "time": "morning"}]} |
| nutrition.guidelines | 获取疾病营养建议 | {"condition": "高血压"} |
| food_drug_interaction.check | 检查食物-药物相互作用 | {"foods": ["葡萄柚"], "drugs": ["阿托伐他汀"]} |
| visit_checklist.generate | 生成就医准备清单 | {"department": "心内科", "conditions": ["高血压"]} |
| medical_records.organize | 整理医疗记录 | {"records": [{"date": "2026-08-01", "type": "体检", "category": "检验"}]} |
| health_metrics.track | 记录健康指标 | {"metrics": {"blood_pressure": "135/85", "glucose": 6.5}} |
| health_trend.analyze | 分析健康趋势 | {"days": 30} |

## 安全声明

本系统所有输出仅供参考，不构成医疗诊断或治疗建议。具体诊疗请遵医嘱。遇到紧急情况请立即拨打 120。

## 技术栈

- **框架**: AgentTeams (Manager-Workers 架构, Matrix 协议)
- **运行时**: OpenClaw
- **模型**: qwen3.5-plus (通义千问)
- **工具服务器**: Python HTTP Server
- **通信**: Element Web (Matrix 客户端)

## 项目结构

```
family-health-demo/
├── README.md                          # 本文件
├── at/
│   └── create_agents_messages.md      # Agent 创建消息（发送给 Manager）
├── tools/
│   └── mock_tool_server.py            # 模拟工具服务器（10个健康工具）
└── yaml/
    ├── workers.yaml                   # 5个 Worker 的 YAML 定义
    ├── team.yaml                      # Team 定义
    └── human.yaml                     # 人类用户定义
```
