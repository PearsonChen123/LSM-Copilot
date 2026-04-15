# Follow-Up: Post-Analysis Interaction

## When to Trigger

**Immediately after Phase 1 analysis is complete** — before ending your turn.

This is NOT optional. Every analysis session must include a follow-up.

---

## What to Do

### 1. Present Results Summary

Give the user a concise summary of key findings:
- Total objects detected
- Key size/volume statistics (mean ± SD, median)
- Notable spatial patterns
- Any anomalies or concerns

### 2. Ask for Sample Context

Ask the user to provide (in whatever language they prefer):

```
分析已完成。为了更好地解读结果并生成报告，请提供以下信息：

1. **样本描述**：这是什么样本？
   例如：小鼠脑组织切片、HeLa 细胞培养、聚合物薄膜...

2. **实验背景**：这个实验要回答什么科学问题？
   例如：验证 CryoChem 方法能否保留组织形态、比较两种固定方法...

3. **标记/通道信息**：各荧光通道对应什么？
   例如：ch1=DAPI(核), ch2=GFP-CRF, ch3=tdTomato, ch4=DRAQ5...

4. **处理条件**：样本经过什么特殊处理？
   例如：CryoChem 固定、4% PFA 固定、透明化处理、冷冻切片...

5. **是否有对照/比较组？**
   例如：有未处理的对照组、有另一种固定方法的对照...

6. **是否需要我生成正式的分析报告 (REPORT.md)？**
```

### 3. If User Provides Context but Declines Report

- Store the context for future reference in the session
- Offer specific follow-up analysis based on context (e.g., "Since this is CryoChem tissue, would you like me to analyze fluorescence preservation in the GFP channel?")

### 4. If User Wants a Report

Proceed to Phase 3 (Report Generation):
1. **Search the web** for relevant literature based on sample context
2. **Generate the report** with literature-contextualized interpretation
3. See `report.md` for formatting guidelines

---

## Special Follow-Up Triggers

### If user mentions fluorescent proteins (GFP, tdTomato, mCherry, etc.)

Ask: "是否需要做荧光保留分析？这可以量化处理方法对荧光信号的影响。需要提供处理前后的数据，或者我可以将当前数据与文献参考值进行比较。"

### If user has multiple channels

Ask: "是否需要做通道间的共定位分析？"

### If user has multiple files/conditions

Ask: "是否需要做批量处理和条件间比较？"

---

## Anti-Patterns

- Do NOT skip the follow-up — it's the most important step for producing useful analysis
- Do NOT generate a report without asking first
- Do NOT assume you know the experimental context — always ask
- Do NOT use jargon without explaining it if the user seems unfamiliar
