"""Plot the time and the objective of each solver against the scenarios.

The first figure is the time of solve_network, the second the relative
difference of objective + objective_constant from that of the reference
solver, on a symmetric logarithmic axis.
"""

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--reference", default="gurobi")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    data = pd.read_csv(args.input)
    data = data.loc[data.benchmark_rule == "solve_network"].copy()
    data["value"] = data.objective + data.objective_constant.fillna(0)
    reference = data.loc[data.solver == args.reference].set_index(
        "scenarios"
    ).value
    reference = data.scenarios.map(reference)
    data["error"] = (data.value - reference) / reference
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data[["solver", "scenarios", "s", "value", "error"]].to_csv(
        args.output_dir / "benchmarks.csv", index=False
    )

    scenarios = sorted(data.scenarios.unique())
    for column, stem, label in [
        ("s", "time", "time of solve_network (s)"),
        ("error", "objective_error",
         f"(objective - {args.reference}) / {args.reference}"),
    ]:
        fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
        # one marker per solver, since two solvers may give the same values
        for (solver, subset), marker in zip(data.groupby("solver", sort=False),
                                            "osD^vP*X"):
            if column == "error" and solver == args.reference:
                continue
            subset = subset.sort_values("scenarios")
            ax.plot(subset.scenarios, subset[column], marker=marker,
                    markersize=8, linewidth=2, label=solver)
        if column == "s":
            ax.set_yscale("log")
        else:
            nonzero = data.error.abs().loc[data.error != 0]
            threshold = (10 ** math.floor(math.log10(nonzero.min()))
                         if not nonzero.empty else 1e-8)
            ax.set_yscale("symlog", linthresh=threshold)
            ax.axhline(0, color="#777777", linewidth=0.8)
        ax.set_xticks(scenarios)
        ax.set_xlabel("scenarios")
        ax.set_ylabel(label)
        ax.grid(True, color="#e0e0e0", linewidth=0.8)
        ax.legend(frameon=False)
        fig.savefig(args.output_dir / f"{stem}.png", dpi=150)
        plt.close(fig)


if __name__ == "__main__":
    main()
