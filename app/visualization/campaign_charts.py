import matplotlib.pyplot as plt

# Sample data
campaigns = ["Email", "Social", "Search", "Display", "Direct"]
conversions = [420, 310, 580, 190, 260]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(campaigns, conversions, color="#4C72B0")

ax.set_title("Conversions by Channel")
ax.set_xlabel("Channel")
ax.set_ylabel("Conversions")

# Optional: label each bar with its value
for bar in bars:
    height = bar.get_height()
    ax.annotate(
        f"{height}",
        xy=(bar.get_x() + bar.get_width() / 2, height),
        xytext=(0, 3),  # 3 points vertical offset
        textcoords="offset points",
        ha="center",
    )

plt.tight_layout()
plt.savefig("bar_chart.png", dpi=150)
plt.show()