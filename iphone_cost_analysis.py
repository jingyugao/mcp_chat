import matplotlib.pyplot as plt
import numpy as np

# 成本数据（单位：美元）
components = {
    "显示屏和触控": 65,
    "处理器芯片": 55,
    "存储和内存": 45,
    "摄像头系统": 40,
    "外壳和玻璃": 30,
    "电池": 25,
    "组装人工": 20,
    "其他零件": 40,
}

# 创建饼图
plt.figure(figsize=(10, 8))
plt.pie(
    components.values(),
    labels=components.keys(),
    autopct="%1.1f%%",
    startangle=90,
    colors=[
        "#FF9999",
        "#66B2FF",
        "#99FF99",
        "#FFCC99",
        "#FF99CC",
        "#99CCFF",
        "#FFB366",
        "#C2C2F0",
    ],
)

# 添加标题
plt.title("iPhone 成本构成分析", fontsize=15, pad=20)

# 添加图例
plt.legend(
    components.keys(),
    title="成本项目",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
)

# 确保图形完整显示
plt.tight_layout()

# 保存图片
plt.savefig("iphone_cost_breakdown.png", bbox_inches="tight", dpi=300)
plt.close()
