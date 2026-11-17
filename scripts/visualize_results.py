#!/usr/bin/env python3
"""Render result figures from validated LLM labels."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from review_mining.taxonomy import CAUSES, CAUSE_DESCRIPTIONS

ZH_NAMES = {
    "quality_durability": "质量耐用性",
    "performance_functionality": "性能功能",
    "size_fit_design": "尺寸设计",
    "description_expectation_gap": "描述落差",
    "value_for_money": "性价比",
    "delivery_packaging": "配送包装",
    "customer_service_return": "客服退换",
    "safety_health": "安全健康",
    "usability_setup": "易用安装",
    "wrong_item_counterfeit": "错发仿品",
    "other": "其他",
    "unclear": "无法判断",
}

CATEGORY_ZH = {
    "All_Beauty": "美妆个护",
    "Appliances": "家电",
    "Home_and_Kitchen": "家居厨具",
    "Pet_Supplies": "宠物用品",
}

ACCENT = "#2F6FED"
TEXT = "#1F2937"
GRID = "#E5E7EB"
SEVERITY_CMAP = LinearSegmentedColormap.from_list(
    "severity", ["#FDE68A", "#F59E0B", "#DC2626"]
)


def setup_chinese_font():
    for candidate in [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]:
        if Path(candidate).exists():
            font_manager.fontManager.addfont(candidate)
            name = font_manager.FontProperties(fname=candidate).get_name()
            plt.rcParams["font.family"] = [name, "DejaVu Sans"]
            return name
    return None


def style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT, labelsize=10)


def read_labels(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def label(cause):
    return f"{ZH_NAMES[cause]} {cause}"


def fig_distribution(rows, out_path):
    counts = Counter(row["primary_cause"] for row in rows)
    causes = [c for c in CAUSES if counts[c] > 0]
    causes.sort(key=lambda c: counts[c])
    total = len(rows)
    severity = {
        c: sum(r["severity"] for r in rows if r["primary_cause"] == c) / counts[c]
        for c in causes
    }
    norm = Normalize(vmin=1, vmax=5)
    colors = [SEVERITY_CMAP(norm(severity[c])) for c in causes]

    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=200)
    bars = ax.barh([label(c) for c in causes], [counts[c] for c in causes],
                   color=colors, edgecolor="white", height=0.72)
    for bar, c in zip(bars, causes):
        share = counts[c] / total
        ax.text(bar.get_width() + 4, bar.get_y() + bar.get_height() / 2,
                f"{counts[c]}  ({share:.1%})", va="center", fontsize=10, color=TEXT)
    ax.set_xlim(0, max(counts.values()) * 1.22)
    ax.set_xlabel("差评数（n=1000，1–2 星）", fontsize=11, color=TEXT)
    ax.set_title("差评归因分布：条形长度=评论数，颜色=平均严重度",
                 fontsize=13, color=TEXT, pad=14, fontweight="bold", loc="left")
    style_axes(ax)
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    sm = ScalarMappable(norm=norm, cmap=SEVERITY_CMAP)
    cbar = fig.colorbar(sm, ax=ax, pad=0.02, aspect=26)
    cbar.set_label("平均严重度 (1–5)", fontsize=10, color=TEXT)
    cbar.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_category_heatmap(rows, out_path):
    categories = sorted({r["product_category"] for r in rows})
    total = {c: sum(1 for r in rows if r["product_category"] == c) for c in categories}
    matrix = []
    for category in categories:
        counts = Counter(r["primary_cause"] for r in rows if r["product_category"] == category)
        matrix.append([counts.get(c, 0) / total[category] * 100 for c in CAUSES])

    fig, ax = plt.subplots(figsize=(11.5, 4.4), dpi=200)
    cmap = LinearSegmentedColormap.from_list("blues", ["#F8FAFC", "#2F6FED"])
    image = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0, vmax=40)
    ax.set_xticks(range(len(CAUSES)))
    ax.set_xticklabels([ZH_NAMES[c] for c in CAUSES], fontsize=10, color=TEXT,
                       rotation=30, ha="right")
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels([f"{CATEGORY_ZH[c]} {c}" for c in categories], fontsize=10, color=TEXT)
    for i in range(len(categories)):
        for j, cause in enumerate(CAUSES):
            value = matrix[i][j]
            color = "white" if value > 22 else TEXT
            ax.text(j, i, f"{value:.1f}%", ha="center", va="center",
                    fontsize=9.5, color=color,
                    fontweight="bold" if value >= 20 else "normal")
    ax.set_title("品类 × 归因：单元格为该归因占本品类差评的比例",
                 fontsize=13, color=TEXT, pad=14, fontweight="bold", loc="left")
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xticks([j - 0.5 for j in range(1, len(CAUSES))], minor=True)
    ax.set_yticks([i - 0.5 for i in range(1, len(categories))], minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="both", length=0)
    cbar = fig.colorbar(image, ax=ax, pad=0.015, aspect=22)
    cbar.set_label("占比 (%)", fontsize=10, color=TEXT)
    cbar.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_priority(rows, out_path):
    stats = defaultdict(lambda: {"n": 0, "sev": 0.0, "conf": 0.0})
    for row in rows:
        s = stats[row["primary_cause"]]
        s["n"] += 1
        s["sev"] += row["severity"]
        s["conf"] += row["confidence"]
    points = []
    for cause, s in stats.items():
        n = s["n"]
        avg_sev = s["sev"] / n
        avg_conf = s["conf"] / n
        points.append((cause, n, avg_sev, avg_conf, n * avg_sev * avg_conf))
    points.sort(key=lambda p: p[4], reverse=True)

    # 手工指定标签偏移，避免密集区文字重叠：(dx, dy, 水平对齐)
    offsets = {
        "quality_durability": (0, -34, "center"),
        "performance_functionality": (0, 18, "center"),
        "safety_health": (0, 14, "center"),
        "size_fit_design": (10, -36, "center"),
        "description_expectation_gap": (-14, 18, "center"),
        "value_for_money": (34, -10, "left"),
        "usability_setup": (-8, -44, "center"),
        "delivery_packaging": (34, -2, "left"),
        "wrong_item_counterfeit": (30, 6, "left"),
        "customer_service_return": (28, 6, "left"),
        "unclear": (30, -2, "left"),
        "other": (28, -12, "left"),
    }

    fig, ax = plt.subplots(figsize=(10.5, 6.4), dpi=200)
    for cause, n, avg_sev, avg_conf, priority in points:
        ax.scatter(n, avg_sev, s=60 + priority * 1.6,
                   color=SEVERITY_CMAP(Normalize(1, 5)(avg_sev)),
                   alpha=0.85, edgecolor="white", linewidth=1.2, zorder=3)
        dx, dy, ha = offsets.get(cause, (0, 14, "center"))
        ax.annotate(f"{ZH_NAMES[cause]}  优先级 {priority:.0f}",
                    (n, avg_sev), textcoords="offset points", xytext=(dx, dy),
                    ha=ha, fontsize=9, color=TEXT, zorder=4)
    ax.set_xlabel("评论数（出现频次）", fontsize=11, color=TEXT)
    ax.set_ylabel("平均严重度 (1–5)", fontsize=11, color=TEXT)
    ax.set_title("优先级 = 评论数 × 平均严重度 × 平均置信度（气泡大小 ∝ 优先级）",
                 fontsize=13, color=TEXT, pad=14, fontweight="bold", loc="left")
    ax.set_xlim(-12, 340)
    ax.set_ylim(1.25, 4.85)
    style_axes(ax)
    ax.grid(True, color=GRID)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    font = setup_chinese_font()
    rows = read_labels(args.labels)
    if not rows:
        raise SystemExit("No labels found.")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_distribution(rows, out_dir / "fig1_cause_distribution.png")
    fig_category_heatmap(rows, out_dir / "fig2_category_heatmap.png")
    fig_priority(rows, out_dir / "fig3_priority_bubble.png")
    print(f"Fonts: {font or 'fallback'}; wrote 3 figures to {out_dir}")


if __name__ == "__main__":
    main()
