# -*- coding: utf-8 -*-
"""生成家庭健康AI管家初赛方案PPT所需的架构/流程/体系图。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager as fm
import os

FONT = "C:/Windows/Fonts/simhei.ttf"
fm.fontManager.addfont(FONT)
PROP = fm.FontProperties(fname=FONT)
plt.rcParams["font.family"] = PROP.get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11

OUT = os.path.dirname(os.path.abspath(__file__))
PALETTE = {
    "input":  "#4C9AFF",
    "lead":   "#7C4DFF",
    "agent":  "#26A69A",
    "base":   "#FF8F3C",
    "output": "#EF5350",
    "soft":   "#90CAF9",
    "soft2":  "#B39DDB",
    "soft3":  "#80CBC4",
    "soft4":  "#FFCC80",
    "grey":   "#CFD8DC",
}
# 圆角矩形
def box(ax, x, y, w, h, text, fc, ec="#37474F", tc="white", fs=11, lw=1.5, rad=0.06):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.0,rounding_size={rad}",
                                fc=fc, ec=ec, lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontproperties=PROP, fontsize=fs, zorder=4, wrap=False)

def arrow(ax, x1, y1, x2, y2, color="#37474F", lw=1.8, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                 mutation_scale=14, color=color, lw=lw, zorder=2))

def title(ax, t, fs=14):
    ax.text(0.5, 1.06, t, ha="center", va="center", color="#1A237E",
            fontproperties=PROP, fontsize=fs, weight="bold", transform=ax.transAxes)

def newfig(w=10, h=6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax

def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight", dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", p)

# ----------------------------------------------------------------------------
# 1) 整体方案架构图 (slide 7)  10x6
# ----------------------------------------------------------------------------
def arch():
    fig, ax = newfig(10, 6)
    title(ax, "家庭健康 AI 管家 · 整体方案架构")
    # 输入层
    box(ax, 0.3, 4.6, 1.9, 1.0, "用户 / 家属\n(输入)", PALETTE["input"], fs=11)
    box(ax, 0.3, 3.3, 1.9, 1.1, "体检报告\n门诊病历\n药品说明书\n可穿戴数据", PALETTE["soft"], tc="#0D47A1", fs=9)
    # 编排层
    box(ax, 2.5, 3.3, 2.0, 2.3, "进度管家 · 小析\n(Team Lead)\n\n任务拆解 / 编排\n状态管理 / 冲突仲裁\n依赖调度", PALETTE["lead"], fs=10)
    # 协作层 5个Agent
    agents = [
        ("病历翻译官", PALETTE["agent"]),
        ("健康数据分析师", PALETTE["agent"]),
        ("用药管理师", PALETTE["agent"]),
        ("营养顾问", PALETTE["agent"]),
        ("就医导航员", PALETTE["agent"]),
    ]
    ay = 4.9
    for i, (nm, c) in enumerate(agents):
        yy = 4.9 - i * 0.46
        box(ax, 4.8, yy, 2.3, 0.40, nm, c, fs=10)
    box(ax, 4.8, 2.55, 2.3, 0.4, "并行层→串行依赖链", PALETTE["grey"], tc="#263238", fs=9)
    # 能力底座
    box(ax, 7.4, 4.6, 2.3, 1.0, "Mock Tool Server\n10 个健康工具", PALETTE["base"], fs=10)
    box(ax, 7.4, 3.0, 2.3, 1.4, "MCP 接入\n文件系统 / GitHub\n\nRAG 知识库\n医疗知识 / 安全红线\n个人健康档案", PALETTE["soft4"], tc="#BF360C", fs=9)
    # 输出层
    box(ax, 0.3, 0.5, 9.4, 1.3,
        "多模态健康输出：大白话解读 · 用药提醒 · 就医清单 · 趋势预警 · 健康档案",
        PALETTE["output"], fs=10.5)
    # 连线
    arrow(ax, 2.2, 4.1, 2.5, 4.1)            # input->lead
    arrow(ax, 4.5, 4.4, 4.8, 4.4)            # lead->agents
    arrow(ax, 7.1, 4.1, 7.4, 4.1)            # lead->base
    arrow(ax, 7.4, 3.0, 7.1, 2.6, color=PALETTE["base"])  # base up hint
    arrow(ax, 5.0, 2.55, 5.0, 1.8)           # agents->output
    arrow(ax, 7.4, 2.6, 5.0, 1.8, color=PALETTE["base"])
    arrow(ax, 2.5, 3.3, 5.0, 1.8, color=PALETTE["lead"])
    save(fig, "arch.png")

# ----------------------------------------------------------------------------
# 2) 多Agent协作流程图 (slide 9 左) 9x5
# ----------------------------------------------------------------------------
def agents_flow():
    fig, ax = newfig(9, 5)
    title(ax, "多 Agent 协作编排：并行层 + 串行依赖链")
    # 顶层输入
    box(ax, 3.3, 4.2, 2.4, 0.55, "用户上传 体检报告/病历", PALETTE["input"], fs=11)
    # 并行层
    box(ax, 0.4, 3.0, 2.6, 0.6, "病历翻译官", PALETTE["agent"], fs=11)
    box(ax, 6.0, 3.0, 2.6, 0.6, "健康数据分析师", PALETTE["agent"], fs=11)
    box(ax, 3.1, 3.0, 2.7, 0.6, "进度管家(编排/调度)", PALETTE["lead"], fs=10)
    # 串行层
    box(ax, 1.0, 1.9, 2.4, 0.6, "用药管理师", PALETTE["agent"], fs=11)
    box(ax, 3.4, 1.9, 2.4, 0.6, "营养顾问", PALETTE["agent"], fs=11)
    box(ax, 5.8, 1.9, 2.4, 0.6, "就医导航员", PALETTE["agent"], fs=11)
    # 输出
    box(ax, 2.6, 0.6, 3.8, 0.6, "健康日报 + 就医清单 + 预警", PALETTE["output"], fs=11)
    # 连线
    arrow(ax, 4.5, 4.2, 4.5, 3.6)
    arrow(ax, 1.7, 3.0, 1.7, 2.5)     # 翻译->用药
    arrow(ax, 4.45, 3.0, 2.2, 2.5, color=PALETTE["lead"])  # lead->用药
    arrow(ax, 7.3, 3.0, 7.0, 2.5, color=PALETTE["lead"])  # lead->就医
    arrow(ax, 2.2, 1.9, 3.4, 1.9)     # 用药->营养
    arrow(ax, 5.8, 1.9, 5.8, 1.25, color=PALETTE["base"])  # 分析->就医? 跳过
    arrow(ax, 4.6, 1.9, 4.6, 1.25)    # 营养->output
    arrow(ax, 7.0, 1.9, 4.5, 1.25, color=PALETTE["base"])
    # 依赖标注
    ax.text(4.5, 2.55, "依赖链", ha="center", color="#607D8B", fontproperties=PROP, fontsize=9)
    save(fig, "agents_flow.png")

# ----------------------------------------------------------------------------
# 3) 上下文传递/状态流转/安全边界 (slide 9 右) 9x5
# ----------------------------------------------------------------------------
def agents_state():
    fig, ax = newfig(9, 5)
    title(ax, "上下文传递 · 状态流转 · 安全边界")
    # 共享黑板
    box(ax, 2.6, 3.6, 3.8, 0.7, "共享黑板 (JSON Schema)\n任务状态 / 用户健康画像 / 会话上下文", PALETTE["soft2"], tc="#311B92", fs=10)
    # 状态机
    boxes = [("pending", "#90A4AE"), ("in_progress", "#42A5F5"), ("completed", "#66BB6A"), ("failed", "#EF5350")]
    bx = 0.6
    for i, (s, c) in enumerate(boxes):
        box(ax, bx + i * 2.05, 2.5, 1.75, 0.55, s, c, fs=9)
        if i < 3:
            arrow(ax, bx + i * 2.05 + 1.75, 2.775, bx + (i+1)*2.05, 2.775, lw=1.4, style="-|>")
    # 安全边界
    box(ax, 0.6, 1.0, 3.6, 0.9, "7 条安全红线\n不下诊断 / 不开药 / 不替代医生\n急诊识别→引导 120", PALETTE["output"], fs=9)
    box(ax, 4.8, 1.0, 3.6, 0.9, "高风险动作审批\n用药冲突 / 异常预警\n需人类确认才执行", PALETTE["base"], tc="#BF360C", fs=9)
    # 连线
    arrow(ax, 4.5, 3.6, 4.5, 3.05, color=PALETTE["soft2"])
    arrow(ax, 2.0, 2.5, 2.4, 1.45, color="#607D8B")
    arrow(ax, 6.6, 2.5, 6.6, 1.9, color="#607D8B")
    save(fig, "agents_state.png")

# ----------------------------------------------------------------------------
# 4) Skill / Worker / Tool 体系映射 (slide 11) 9x5
# ----------------------------------------------------------------------------
def skills_map():
    fig, ax = newfig(9, 5)
    title(ax, "Skill / Worker 体系与工具依赖映射")
    # 5 workers
    workers = ["病历翻译官", "用药管理师", "营养顾问", "就医导航员", "健康数据分析师"]
    wy = 3.7
    for i, w in enumerate(workers):
        yy = wy - i * 0.78
        box(ax, 0.5, yy, 2.5, 0.62, w, PALETTE["agent"], fs=10)
    # 4 核心 Skill
    skills = ["code→human 翻译\n(复用Skill②)", "安全红线审查\n(复用Skill⑥)", "概念图谱\n(复用Skill④)", "日志聚合\n(复用Skill⑧)"]
    for i, s in enumerate(skills):
        box(ax, 3.3, 3.9 - i * 0.85, 2.6, 0.66, s, PALETTE["soft2"], tc="#311B92", fs=9)
    # 10 tools
    box(ax, 6.3, 2.2, 2.6, 2.3,
        "Mock Tool Server (10)\n\n医学术语翻译\n药物相互作用\n营养指南\n健康趋势分析\n体检指标解析\n药品说明书解析\n紧急程度分级\n用药提醒生成\n就医清单生成\n家庭档案查询",
        PALETTE["base"], tc="#BF360C", fs=8.5)
    # MCP / RAG
    box(ax, 6.3, 0.5, 2.6, 1.4, "MCP: 文件系统 / GitHub\nRAG: 医疗知识库\n     安全红线库\n     个人健康档案", PALETTE["soft4"], tc="#BF360C", fs=9)
    # 连线
    arrow(ax, 3.0, 3.9, 3.3, 3.9)
    arrow(ax, 5.9, 3.9, 6.3, 3.3)
    arrow(ax, 5.9, 1.5, 6.3, 1.9, color=PALETTE["base"])
    save(fig, "skills_map.png")

# ----------------------------------------------------------------------------
# 5) 四张工程/安全图 (slide 13) 各 7x3.9
# ----------------------------------------------------------------------------
def panel(name, t, lines, color):
    fig, ax = newfig(7, 3.9)
    title(ax, t, fs=12)
    y = 3.2
    for ln in lines:
        ax.text(0.4, y, "· " + ln, ha="left", va="center", color="#263238",
                fontproperties=PROP, fontsize=10.5, zorder=4)
        y -= 0.62
    box(ax, 0.4, 0.35, 6.2, 0.55, "可审计：全链路日志记录每个 Agent 决策与置信度", color, tc="white", fs=9.5)
    save(fig, name)

def sec_run():
    panel("sec_run.png", "① 可运行性与运行证据",
          ["AgentTeams 声明式 work team：YAML + mock 工具服务器",
           "已实测 10 个工具：术语翻译 / 用药冲突 / 营养 / 趋势",
           "样例：阿司匹林+华法林 → 识别为高危相互作用",
           "样例：高血压 → 返回 DASH 饮食原则与限盐建议"], PALETTE["agent"])

def sec_obs():
    panel("sec_obs.png", "② 可观测与检索链路",
          ["RAG 检索链路：医疗知识→安全红线→个人档案三级",
           "每个 Agent 输出写入共享黑板，可追溯输入/输出",
           "任务状态机 pending→done 全程可观测",
           "异常自动回退失败分支并告警，不静默出错"], PALETTE["input"])

def sec_gov():
    panel("sec_gov.png", "③ 安全治理机制",
          ["7 条安全红线：不下诊断/不开药/不替代医生…",
           "高危动作(用药冲突/异常预警)需人类确认才执行",
           "数据脱敏 + 沙箱隔离 + 明文健康数据本地加密",
           "急诊识别协议：触发即引导拨打 120"], PALETTE["output"])

def sec_cloud():
    panel("sec_cloud.png", "④ 云产品选型必要性与边界",
          ["知识库托管：医疗/安全红线语料持续更新",
           "函数计算：弹性运行 mock 工具与 RAG 检索",
           "向量数据库：个人健康档案低延迟检索",
           "边界：敏感原始数据不出本地，仅上云脱敏特征"], PALETTE["base"])

# ----------------------------------------------------------------------------
# 6) 场景与价值两图 (slide 5) 9x5
# ----------------------------------------------------------------------------
def scene_pain():
    fig, ax = newfig(9, 5)
    title(ax, "目标用户与核心痛点")
    pains = [
        ("看不懂报告", "诊断证明/检验单满是术语"),
        ("管不好用药", "多种药同时吃，怕相互作用"),
        ("吃不对营养", "有病不知什么该忌口"),
        ("就医没准备", "见到医生想不起要问啥"),
        ("趋势不掌握", "指标变化无人持续追踪"),
    ]
    for i, (h, d) in enumerate(pains):
        y = 4.2 - i * 0.78
        box(ax, 0.5, y, 2.6, 0.62, h, PALETTE["output"], fs=11)
        box(ax, 3.3, y, 5.0, 0.62, d, PALETTE["soft"], tc="#0D47A1", fs=10)
    save(fig, "scene_pain.png")

def scene_value():
    fig, ax = newfig(9, 5)
    title(ax, "可量化价值与行业可复制性")
    vals = [
        ("效率", "1 份报告 → 5 分钟生成大白话解读+清单"),
        ("安全", "用药冲突识别覆盖常见 30+ 药物组合"),
        ("依从", "每日用药提醒提升服药依从性"),
        ("可复制", "框架迁移至慢病管理/母婴/养老场景"),
        ("降本", "减少非必要就医与重复问诊"),
    ]
    for i, (h, d) in enumerate(vals):
        y = 4.2 - i * 0.78
        box(ax, 0.5, y, 2.6, 0.62, h, PALETTE["agent"], fs=11)
        box(ax, 3.3, y, 5.0, 0.62, d, PALETTE["soft3"], tc="#004D40", fs=10)
    save(fig, "scene_value.png")

# ----------------------------------------------------------------------------
# 7) 落地计划与进展两图 (slide 17) 8x4.3 / 8x3.7
# ----------------------------------------------------------------------------
def progress_timeline():
    fig, ax = newfig(8, 4.3)
    title(ax, "里程碑与落地计划（6 周）")
    steps = [("W1-2", "3 Agent + CLI\nPython 支持"),
             ("W3-4", "5 Agent 齐全\nWeb 界面 + 图谱"),
             ("W5-6", "仪表盘 + MCP\n演示视频")]
    x = 0.8
    for i, (w, d) in enumerate(steps):
        box(ax, x, 2.4, 1.9, 1.0, d, PALETTE["lead"], fs=9.5)
        box(ax, x, 3.6, 1.9, 0.5, w, PALETTE["input"], fs=11)
        if i < 2:
            arrow(ax, x + 1.9, 2.9, x + 2.4, 2.9)
        x += 2.4
    box(ax, 0.8, 0.7, 6.6, 0.8, "当前进展：work team 已就绪 — 5 Worker YAML + Team/H-uman 定义 + mock 工具服务器(10 工具实测通过)", PALETTE["agent"], fs=9.5)
    save(fig, "progress_timeline.png")

def risk_ctrl():
    fig, ax = newfig(8, 3.7)
    title(ax, "风险控制", fs=12)
    risks = [
        "合规风险 → 7 红线 + 免责声明 + 急诊协议，定位为辅助而非诊疗",
        "数据风险 → 本地加密 + 脱敏上云 + 沙箱隔离",
        "质量风险 → RAG 检索可溯源 + Agent 输出置信度评分",
        "进度风险 → MVP 仅 3 Agent 即可运行，分阶段交付",
    ]
    y = 3.0
    for r in risks:
        ax.text(0.4, y, "√ " + r, ha="left", va="center", color="#263238",
                fontproperties=PROP, fontsize=10, zorder=4)
        y -= 0.72
    save(fig, "risk_ctrl.png")

if __name__ == "__main__":
    arch()
    agents_flow()
    agents_state()
    skills_map()
    sec_run(); sec_obs(); sec_gov(); sec_cloud()
    scene_pain(); scene_value()
    progress_timeline(); risk_ctrl()
    print("ALL DONE")
