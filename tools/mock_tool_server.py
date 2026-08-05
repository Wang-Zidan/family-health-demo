#!/usr/bin/env python3
"""
Family Health AI Manager - Mock Tool Server (MCP 版)
=====================================================
家庭健康AI管家 - 模拟工具服务器（已改为标准 MCP 服务器）

为何改成 MCP 服务器：
    原版只是一个普通 HTTP 服务（/health + POST /tools/...），没有任何 JSON Schema。
    AgentTeams(基于 alibaba/hiclaw) 的 Worker 通过 spec.mcpServers 关联 MCP 服务器，
    框架用 MCP 协议拿到「带合法 JSON Schema 的工具列表」后，才能正确构造 OpenAI tools
    参数发给 LLM。原版没有 schema -> tools payload 非法 -> "provider rejected the
    request schema or tool payload"。本版用官方 mcp SDK(FastMCP) 暴露 10 个工具，
    每个工具都有完整参数 schema，问题即解决。

启动方式:
    pip install "mcp>=1.2"
    python3 tools/mock_tool_server.py --host 0.0.0.0 --port 18089

MCP 端点:   http://0.0.0.0:18089/mcp   (streamable-http)
健康检查:   GET  http://127.0.0.1:18089/health
"""

import json
import argparse
import random
from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field
from fastmcp import FastMCP

# ============================================================
# 模拟数据库（与原版一致，行为不变）
# ============================================================

# 医学术语翻译库
MEDICAL_TERMS = {
    "高血压": {"plain": "血压持续偏高，血管压力大的状态", "severity": "慢性病需长期管理"},
    "2型糖尿病": {"plain": "身体处理糖分的能力下降，血糖容易偏高", "severity": "慢性病需控制饮食"},
    "高脂血症": {"plain": "血液里的脂肪（胆固醇等）含量超标", "severity": "增加心脑血管风险"},
    "脂肪肝": {"plain": "肝脏里堆积了过多脂肪", "severity": "可通过饮食运动改善"},
    "窦性心律": {"plain": "心脏跳动节奏正常，是从心脏正常起搏点发出的", "severity": "正常"},
    "空腹血糖": {"plain": "空腹时血液中的糖分含量", "severity": "正常值3.9-6.1mmol/L"},
    "甘油三酯": {"plain": "血液中的一种脂肪", "severity": "正常值<1.7mmol/L"},
    "总胆固醇": {"plain": "血液中所有胆固醇的总量", "severity": "正常值<5.2mmol/L"},
    "低密度脂蛋白": {"plain": "俗称'坏胆固醇'，高了容易堵血管", "severity": "正常值<3.4mmol/L"},
    "高密度脂蛋白": {"plain": "俗称'好胆固醇'，高了反而好", "severity": "正常值>1.0mmol/L"},
    "ALT": {"plain": "谷丙转氨酶，反映肝细胞是否受损的指标", "severity": "正常值<40U/L"},
    "AST": {"plain": "谷草转氨酶，也反映肝功能", "severity": "正常值<40U/L"},
    "尿酸": {"plain": "体内嘌呤代谢的产物，高了可能引发痛风", "severity": "正常值男性<420umol/L"},
    "肌酐": {"plain": "反映肾脏过滤功能的指标", "severity": "正常值男性53-106umol/L"},
    "白细胞": {"plain": "免疫系统的士兵，高了可能有炎症", "severity": "正常值3.5-9.5x10^9/L"},
    "血红蛋白": {"plain": "红细胞里负责运氧气的蛋白质，低了就是贫血", "severity": "正常值男性130-175g/L"},
}

# 药物相互作用库
DRUG_INTERACTIONS = {
    ("二甲双胍", "格列美脲"): {
        "level": "注意",
        "description": "两者合用可能增加低血糖风险，需密切监测血糖",
        "advice": "建议错开服药时间，定期监测血糖"
    },
    ("阿司匹林", "华法林"): {
        "level": "危险",
        "description": "两者合用显著增加出血风险",
        "advice": "如非必要不建议合用，必须在医生指导下使用"
    },
    ("阿托伐他汀", "克拉霉素"): {
        "level": "危险",
        "description": "克拉霉素会显著升高阿托伐他汀血药浓度，增加肌肉损伤风险",
        "advice": "建议暂停他汀类药物或换用替代抗生素"
    },
    ("奥美拉唑", "氯吡格雷"): {
        "level": "注意",
        "description": "奥美拉唑会降低氯吡格雷的抗血小板效果",
        "advice": "建议改用泮托拉唑等影响较小的药物"
    },
    ("氨氯地平", "辛伐他汀"): {
        "level": "注意",
        "description": "氨氯地平会升高辛伐他汀血药浓度，增加肌肉不良反应风险",
        "advice": "辛伐他汀剂量不应超过20mg/日"
    },
}

# 疾病-营养建议库
NUTRITION_GUIDELINES = {
    "高血压": {
        "recommend": ["低盐饮食（每日食盐<5g）", "多吃富含钾的食物（香蕉、菠菜）", "适量补充钙和镁", "多吃全谷物和蔬菜"],
        "avoid": ["高盐食品（腌制品、方便面）", "高脂肪食物", "过量饮酒", "浓茶和浓咖啡"],
        "tips": "DASH饮食法（得舒饮食）对控制血压有明确效果"
    },
    "2型糖尿病": {
        "recommend": ["控制总热量摄入", "选择低GI食物（燕麦、糙米）", "多吃膳食纤维丰富的蔬菜", "定时定量进餐"],
        "avoid": ["精制糖和甜食", "高GI食物（白米饭、白面包）", "含糖饮料", "高脂肪食物"],
        "tips": "进餐顺序建议：先吃蔬菜，再吃蛋白质，最后吃主食"
    },
    "高脂血症": {
        "recommend": ["多吃富含Omega-3的食物（深海鱼）", "增加膳食纤维摄入", "选择植物油代替动物油", "适量食用坚果"],
        "avoid": ["动物内脏", "油炸食品", "奶油和黄油", "高胆固醇食物（蛋黄适量）"],
        "tips": "地中海饮食模式对改善血脂有帮助"
    },
    "脂肪肝": {
        "recommend": ["控制总热量", "多吃富含抗氧化物的食物（蓝莓、绿茶）", "适量优质蛋白（鱼、鸡胸肉）", "补充B族维生素"],
        "avoid": ["酒精", "高糖食物", "精制碳水化合物", "油炸食品"],
        "tips": "减重5%-10%可显著改善脂肪肝"
    },
    "高尿酸": {
        "recommend": ["多喝水（每日2000ml以上）", "多吃低嘌呤食物（鸡蛋、牛奶）", "适量樱桃和芹菜", "补充维生素C"],
        "avoid": ["高嘌呤食物（动物内脏、海鲜）", "酒精（尤其是啤酒）", "含糖饮料（果糖）", "浓肉汤"],
        "tips": "避免突然剧烈运动和快速减重，可能诱发痛风"
    },
}

# 食物-药物相互作用
FOOD_DRUG_INTERACTIONS = {
    ("葡萄柚", "阿托伐他汀"): "葡萄柚会显著升高他汀类药物血药浓度，增加肌肉损伤风险，服药期间避免食用",
    ("酒精", "二甲双胍"): "酒精会增强二甲双胍的乳酸酸中毒风险，服药期间应戒酒",
    ("酒精", "对乙酰氨基酚"): "酒精会加重对乙酰氨基酚的肝毒性，服药期间避免饮酒",
    ("牛奶", "四环素"): "牛奶中的钙会影响四环素吸收，建议间隔2小时服用",
    ("菠菜", "华法林"): "菠菜富含维生素K，会降低华法林抗凝效果，需保持每日摄入量稳定",
    ("酒精", "阿司匹林"): "酒精加阿司匹林显著增加胃出血风险，避免同用",
}


def generate_health_history(days=30):
    """生成模拟的健康指标历史数据"""
    history = []
    base_bp_systolic = 135
    base_bp_diastolic = 88
    base_glucose = 6.8
    base_heart_rate = 78
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        history.append({
            "date": date,
            "blood_pressure_systolic": base_bp_systolic + random.randint(-8, 8),
            "blood_pressure_diastolic": base_bp_diastolic + random.randint(-5, 5),
            "fasting_glucose": round(base_glucose + random.uniform(-0.5, 0.5), 1),
            "heart_rate": base_heart_rate + random.randint(-5, 5),
            "weight": round(72.5 + random.uniform(-0.3, 0.3), 1),
        })
    return history


# ============================================================
# 工具实现（与原版一致，仅入参改为 dict）
# ============================================================

def tool_parse_medical_report(params):
    report_text = params.get("report_text", "")
    report_type = params.get("report_type", "体检报告")
    return {
        "report_type": report_type,
        "parsed_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "abnormal_items": [
            {"item": "血压", "value": "148/92 mmHg", "reference": "<140/90 mmHg", "status": "偏高"},
            {"item": "空腹血糖", "value": "7.2 mmol/L", "reference": "3.9-6.1 mmol/L", "status": "偏高"},
            {"item": "甘油三酯", "value": "2.1 mmol/L", "reference": "<1.7 mmol/L", "status": "偏高"},
            {"item": "低密度脂蛋白", "value": "3.8 mmol/L", "reference": "<3.4 mmol/L", "status": "偏高"},
            {"item": "ALT", "value": "52 U/L", "reference": "<40 U/L", "status": "偏高"},
        ],
        "normal_items": [
            {"item": "心率", "value": "76 次/分", "reference": "60-100 次/分", "status": "正常"},
            {"item": "血红蛋白", "value": "145 g/L", "reference": "130-175 g/L", "status": "正常"},
            {"item": "白细胞", "value": "6.2 x10^9/L", "reference": "3.5-9.5 x10^9/L", "status": "正常"},
        ],
        "preliminary_assessment": "血压偏高、血糖偏高、血脂异常，建议关注心血管和代谢健康",
        "disclaimer": "本解析仅供参考，不构成诊断，请以医生判断为准"
    }


def tool_translate_medical_term(params):
    term = params.get("term", "")
    if term in MEDICAL_TERMS:
        info = MEDICAL_TERMS[term]
        return {
            "term": term,
            "plain_explanation": info["plain"],
            "severity_info": info["severity"],
            "analogy": _get_analogy(term)
        }
    return {
        "term": term,
        "plain_explanation": f"'{term}'暂未在常用术语库中找到，建议咨询医生获取准确解释",
        "severity_info": "未知",
        "analogy": ""
    }


def _get_analogy(term):
    analogies = {
        "高血压": "就像水管里水压太大，时间久了管壁（血管）容易受损",
        "2型糖尿病": "就像细胞的'门锁'坏了，糖分进不去细胞，全堵在血液里",
        "高脂血症": "就像水管里流的不只是水，还混了很多油脂，容易堵塞",
        "脂肪肝": "就像肝脏被脂肪'糊住'了，干活效率下降",
        "低密度脂蛋白": "就像血管里的'垃圾车'，到处丢垃圾（胆固醇），容易堵路",
        "高密度脂蛋白": "就像血管里的'清洁车'，专门回收垃圾，越多越好",
    }
    return analogies.get(term, "")


def tool_check_drug_interaction(params):
    drug_list = params.get("drug_list", [])
    interactions = []
    for i, drug1 in enumerate(drug_list):
        for drug2 in drug_list[i + 1:]:
            key = (drug1, drug2)
            reverse_key = (drug2, drug1)
            if key in DRUG_INTERACTIONS:
                interactions.append({"drug1": drug1, "drug2": drug2, **DRUG_INTERACTIONS[key]})
            elif reverse_key in DRUG_INTERACTIONS:
                interactions.append({"drug1": drug1, "drug2": drug2, **DRUG_INTERACTIONS[reverse_key]})
    if not interactions:
        return {
            "drug_list": drug_list,
            "interactions_found": 0,
            "result": "未发现已知的主要药物相互作用",
            "advice": "仍建议告知医生您正在服用的所有药物"
        }
    dangerous = [i for i in interactions if i["level"] == "危险"]
    return {
        "drug_list": drug_list,
        "interactions_found": len(interactions),
        "interactions": interactions,
        "dangerous_count": len(dangerous),
        "advice": "发现药物相互作用，请务必告知医生" if dangerous else "注意药物相互作用，建议咨询药师"
    }


def tool_get_medication_schedule(params):
    medications = params.get("medications", [])
    schedule = {"morning": [], "noon": [], "evening": [], "before_sleep": []}
    for med in medications:
        name = med.get("name", "")
        freq = med.get("frequency", "每日1次")
        time = med.get("time", "morning")
        dose = med.get("dose", "1片")
        entry = {"medication": name, "dose": dose, "instruction": med.get("instruction", "饭后服用")}
        if time in schedule:
            schedule[time].append(entry)
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "schedule": schedule,
        "total_medications": len(medications),
        "reminder": "请按时服药，不要自行增减剂量",
        "disclaimer": "用药时间表仅供参考，请遵医嘱"
    }


def tool_get_nutrition_guidelines(params):
    condition = params.get("condition", "")
    if condition in NUTRITION_GUIDELINES:
        guide = NUTRITION_GUIDELINES[condition]
        return {
            "condition": condition,
            "recommended_foods": guide["recommend"],
            "foods_to_avoid": guide["avoid"],
            "dietary_tips": guide["tips"],
            "disclaimer": "营养建议仅供参考，具体饮食方案请咨询营养师或医生"
        }
    return {
        "condition": condition,
        "recommended_foods": ["均衡饮食", "多吃蔬菜水果", "适量优质蛋白", "控制油盐摄入"],
        "foods_to_avoid": ["高油高盐食品", "过度加工食品"],
        "dietary_tips": "保持均衡饮食，规律进餐",
        "disclaimer": "通用建议，具体请咨询医生"
    }


def tool_check_food_drug_interaction(params):
    foods = params.get("foods", [])
    drugs = params.get("drugs", [])
    interactions = []
    for food in foods:
        for drug in drugs:
            key = (food, drug)
            if key in FOOD_DRUG_INTERACTIONS:
                interactions.append({"food": food, "drug": drug, "description": FOOD_DRUG_INTERACTIONS[key]})
    return {
        "foods": foods,
        "drugs": drugs,
        "interactions_found": len(interactions),
        "interactions": interactions,
        "advice": "注意饮食与药物的相互影响" if interactions else "未发现已知食物-药物相互作用"
    }


def tool_generate_visit_checklist(params):
    visit_reason = params.get("visit_reason", "复诊")
    department = params.get("department", "内科")
    current_conditions = params.get("conditions", [])
    checklist = {
        "visit_info": {
            "department": department,
            "reason": visit_reason,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "documents_needed": [
            "医保卡/就诊卡",
            "既往病历本",
            "近期检查报告（3个月内）",
            "正在服用的药物清单（或带上药盒）",
            "上次就诊的医嘱记录"
        ],
        "questions_to_ask": [],
        "symptoms_to_describe": [],
        "notes": "建议提前整理好想问医生的问题，避免忘记"
    }
    if "高血压" in current_conditions:
        checklist["questions_to_ask"].extend([
            "我最近血压控制在什么范围比较理想？",
            "需要调整降压药的剂量或种类吗？",
            "家里测血压有什么注意事项？"
        ])
    if "2型糖尿病" in current_conditions:
        checklist["questions_to_ask"].extend([
            "我最近的血糖控制达标了吗？",
            "糖化血红蛋白指标如何？",
            "需要调整饮食或运动方案吗？"
        ])
    if "高脂血症" in current_conditions:
        checklist["questions_to_ask"].extend([
            "血脂指标有改善吗？",
            "需要继续服用降脂药吗？",
            "饮食方面需要特别注意什么？"
        ])
    if not checklist["questions_to_ask"]:
        checklist["questions_to_ask"] = [
            "我的各项指标有什么变化？",
            "接下来需要注意什么？",
            "需要做什么复查？"
        ]
    return checklist


def tool_organize_medical_records(params):
    records = params.get("records", [])
    organized = {
        "total_records": len(records),
        "by_category": {},
        "timeline": [],
        "latest_abnormal": [],
        "summary": ""
    }
    for record in records:
        category = record.get("category", "其他")
        organized["by_category"].setdefault(category, []).append(record)
        organized["timeline"].append({
            "date": record.get("date", ""),
            "type": record.get("type", ""),
            "category": category,
            "summary": record.get("summary", "")
        })
    organized["summary"] = f"共整理{len(records)}条医疗记录，分为{len(organized['by_category'])}个类别"
    organized["advice"] = "建议每年至少整理一次完整的医疗档案，便于就医时提供参考"
    return organized


def tool_track_health_metrics(params):
    metrics = params.get("metrics", {})
    return {
        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": metrics,
        "status": "已记录",
        "comparison": {
            "vs_yesterday": "血压较昨日下降2mmHg",
            "vs_last_week": "血糖较上周平均值降低0.3mmol/L"
        },
        "encouragement": "坚持记录健康数据，有助于发现趋势和问题"
    }


def tool_analyze_health_trend(params):
    days = params.get("days", 30)
    history = generate_health_history(days)
    recent_week = history[-7:]
    previous_week = history[-14:-7] if len(history) >= 14 else history[:7]

    avg_bp_recent = sum(d["blood_pressure_systolic"] for d in recent_week) / len(recent_week)
    avg_bp_previous = sum(d["blood_pressure_systolic"] for d in previous_week) / len(previous_week) if previous_week else avg_bp_recent
    avg_glucose_recent = sum(d["fasting_glucose"] for d in recent_week) / len(recent_week)
    avg_glucose_previous = sum(d["fasting_glucose"] for d in previous_week) / len(previous_week) if previous_week else avg_glucose_recent

    bp_trend = "下降" if avg_bp_recent < avg_bp_previous else ("上升" if avg_bp_recent > avg_bp_previous else "稳定")
    glucose_trend = "下降" if avg_glucose_recent < avg_glucose_previous else ("上升" if avg_glucose_recent > avg_glucose_previous else "稳定")

    alerts = []
    if avg_bp_recent > 140:
        alerts.append({"level": "warning", "message": "近一周平均收缩压偏高，建议关注血压管理"})
    if avg_glucose_recent > 7.0:
        alerts.append({"level": "warning", "message": "近一周平均空腹血糖偏高，建议关注血糖控制"})

    return {
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "period": f"近{days}天",
        "averages": {
            "avg_systolic_bp": round(avg_bp_recent, 1),
            "avg_diastolic_bp": round(sum(d["blood_pressure_diastolic"] for d in recent_week) / len(recent_week), 1),
            "avg_fasting_glucose": round(avg_glucose_recent, 1),
            "avg_heart_rate": round(sum(d["heart_rate"] for d in recent_week) / len(recent_week), 1),
        },
        "trends": {
            "blood_pressure": bp_trend,
            "fasting_glucose": glucose_trend,
            "trend_description": f"血压趋势{bp_trend}，血糖趋势{glucose_trend}"
        },
        "alerts": alerts,
        "recommendation": "继续保持健康监测，规律作息，合理饮食" if not alerts else "建议尽快就医复诊，调整治疗方案",
        "disclaimer": "趋势分析仅供参考，具体诊疗请遵医嘱"
    }


# ============================================================
# MCP 服务器（FastMCP，标准 JSON Schema 由类型注解自动生成）
# ============================================================

mcp = FastMCP("family-health-tools")


class Medication(BaseModel):
    name: str = Field(..., description="药物名称，例如 二甲双胍")
    frequency: str = Field(default="每日1次", description="服药频率，例如 每日1次/每日2次")
    time: str = Field(default="morning", description="服药时段：morning(早)/noon(午)/evening(晚)/before_sleep(睡前)")
    dose: str = Field(default="1片", description="单次剂量，例如 1片/500mg")
    instruction: str = Field(default="饭后服用", description="用药说明，例如 饭后服用/睡前")


class MedicalRecord(BaseModel):
    category: str = Field(default="其他", description="记录类别，例如 检验/影像/门诊")
    date: str = Field(default="", description="记录日期，格式 YYYY-MM-DD")
    type: str = Field(default="", description="记录类型，例如 血常规/CT")
    summary: str = Field(default="", description="记录摘要")


@mcp.tool()
def medical_report_parse(report_text: str, report_type: str = "体检报告") -> dict:
    """解析医疗报告，提取异常项与正常项，给出初步评估。

    当用户上传/描述体检报告、化验单、诊断证明时调用。
    """
    return tool_parse_medical_report({"report_text": report_text, "report_type": report_type})


@mcp.tool()
def medical_term_translate(term: str) -> dict:
    """把医学专业术语翻译成大白话，并给出通俗比喻。

    当报告里出现看不懂的医学名词（如 低密度脂蛋白、ALT）时调用。
    """
    return tool_translate_medical_term({"term": term})


@mcp.tool()
def drug_interaction_check(drug_list: List[str]) -> dict:
    """检查一组药物之间的相互作用，标注危险/注意等级。

    当用户提供正在服用的多种药物清单时调用。
    """
    return tool_check_drug_interaction({"drug_list": drug_list})


@mcp.tool()
def medication_schedule(medications: List[Medication]) -> dict:
    """根据药物清单生成每日用药时间表（早/午/晚/睡前）。

    当用户需要安排每天吃药时间时调用。
    """
    meds = [m.model_dump() for m in medications]
    return tool_get_medication_schedule({"medications": meds})


@mcp.tool()
def nutrition_guidelines(condition: str) -> dict:
    """获取某疾病对应的营养建议（推荐食物/避免食物/饮食贴士）。

    当需要根据高血压、2型糖尿病、高脂血症等疾病给出饮食方案时调用。
    """
    return tool_get_nutrition_guidelines({"condition": condition})


@mcp.tool()
def food_drug_interaction_check(foods: List[str], drugs: List[str]) -> dict:
    """检查食物与药物之间的相互作用（如 葡萄柚+他汀、酒精+二甲双胍）。

    当已知用户常吃的某些食物和正在服用的药物时调用。
    """
    return tool_check_food_drug_interaction({"foods": foods, "drugs": drugs})


@mcp.tool()
def visit_checklist_generate(visit_reason: str = "复诊", department: str = "内科", conditions: List[str] = []) -> dict:
    """生成就医准备清单（需带资料、要问医生的问题等）。

    当用户准备去看病/复诊，需要整理就医材料与问题时调用。
    """
    return tool_generate_visit_checklist({
        "visit_reason": visit_reason,
        "department": department,
        "conditions": conditions
    })


@mcp.tool()
def medical_records_organize(records: List[MedicalRecord]) -> dict:
    """整理历史医疗记录，按类别汇总并生成时间线。

    当用户提供多条分散的就医/检查记录需要归档时调用。
    """
    recs = [r.model_dump() for r in records]
    return tool_organize_medical_records({"records": recs})


@mcp.tool()
def health_metrics_track(metrics: dict) -> dict:
    """记录一次健康指标（血压/血糖/体重等），并给出口径对比。

    当收到用户最新的健康测量数据时调用，用于留痕与追踪。
    """
    return tool_track_health_metrics({"metrics": metrics})


@mcp.tool()
def health_trend_analyze(days: int = 30) -> dict:
    """分析最近若干天的健康指标趋势，识别异常并给出预警。

    当需要看长期趋势、做健康预警时调用。
    """
    return tool_analyze_health_trend({"days": days})


# ------------------------------------------------------------
# 健康检查端点（保留，便于手动验证服务器在线）
# ------------------------------------------------------------
try:
    from starlette.responses import JSONResponse
    if hasattr(mcp, "custom_route"):
        @mcp.custom_route("/health", methods=["GET"])
        def _health(request):
            return JSONResponse({"ok": True, "service": "family-health-mock-mcp-server"})
except Exception:
    # 老版本 mcp 不支持 custom_route 时，MCP 端点本身仍可正常工作
    pass


def main():
    parser = argparse.ArgumentParser(description="Family Health AI Manager - Mock MCP Tool Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=18089, help="Port to bind (default: 18089)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Family Health AI Manager - Mock MCP Tool Server")
    print("=" * 60)
    print(f"  Host : {args.host}")
    print(f"  Port : {args.port}")
    print(f"  MCP  : http://127.0.0.1:{args.port}/mcp   (streamable-http)")
    print(f"  Health: http://127.0.0.1:{args.port}/health")
    print()
    print("  Exposed Tools (10):")
    for t in [
        "medical_report_parse", "medical_term_translate", "drug_interaction_check",
        "medication_schedule", "nutrition_guidelines", "food_drug_interaction_check",
        "visit_checklist_generate", "medical_records_organize", "health_metrics_track",
        "health_trend_analyze",
    ]:
        print(f"    - {t}")
    print("=" * 60)
    print()

    # 以 streamable-http 传输运行；worker(YAML 中 spec.mcpServers.url) 指向 /mcp
    mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
