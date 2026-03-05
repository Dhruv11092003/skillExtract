import json
from pathlib import Path


def main():
    metrics_path = Path("models/training_metrics.json")
    if not metrics_path.exists():
        raise FileNotFoundError("models/training_metrics.json not found. Run training first.")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    print("Evaluation Metrics")
    for k, v in metrics.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
