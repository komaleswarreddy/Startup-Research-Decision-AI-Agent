from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def create_projection_chart(
    labels: list[str], values: list[float], output_dir: str = "artifacts/charts"
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"projection-{uuid4().hex[:8]}.png"
    output_path = Path(output_dir) / filename

    plt.figure(figsize=(8, 4))
    plt.plot(labels, values, marker="o")
    plt.title("Revenue Projection")
    plt.xlabel("Year")
    plt.ylabel("Revenue")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return str(output_path)
