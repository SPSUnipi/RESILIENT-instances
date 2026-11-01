"""
Solve a stochastic network of the generator of plan4res/resilient.

The solver is an entry of ``solvers`` in ``config.yaml``: with ``name`` the
name of a solver of PyPSA (e.g., ``gurobi``, ``highs``) the network is solved
by PyPSA with ``options`` as its solver options; with ``name: smspp`` it is
translated by pypsa2smspp, whose ``Transformation`` takes ``options`` as its
arguments, solved by the tool of SMS++ that pySMSpp runs, and the solution is
read back into the network. In both cases the solved network is written with
the objective (and its constant, which PyPSA keeps out of the objective of
the solver) and, in its metadata, the solver and its options, as the
networks of pypsa-eur-instances are; for SMS++ the times that pySMSpp
measures are also written, in the format of a benchmark of Snakemake, in
``results/benchmarks/solve_network/resilient_{case}_{solver}.smspp``.

Relevant settings
-----------------

.. code:: yaml

    solvers:
      <solver>:
        name:       # a solver of PyPSA, or smspp
        threads:    # the threads Snakemake gives the rule
        options:    # the solver options, or the arguments of Transformation

    cases:
      <case>:
        smspp:      # optional, more arguments of Transformation for the case

Outputs
-------

- ``results/networks/resilient_{case}_{solver}.nc``: the solved network
"""

import logging
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pypsa

logger = logging.getLogger(__name__)

# the columns of a benchmark of Snakemake, those of pypsa-eur-instances
BENCHMARK_COLUMNS = [
    "s",
    "h:m:s",
    "computational_time",
    "max_rss",
    "max_vms",
    "max_uss",
    "max_pss",
    "io_in",
    "io_out",
    "mean_load",
    "cpu_time",
]


def write_smspp_benchmark(path, subprocess_time, computational_time):
    """Write the times of pySMSpp in the format of a benchmark of Snakemake."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    values = {
        "s": f"{float(subprocess_time):.2f}",
        "h:m:s": str(timedelta(seconds=int(float(subprocess_time)))),
        "computational_time": f"{float(computational_time):.2f}",
        **dict.fromkeys(BENCHMARK_COLUMNS[3:], "NA"),
    }
    pd.DataFrame([values], columns=BENCHMARK_COLUMNS).to_csv(
        path, sep="\t", index=False
    )


def solve_smspp(n, options, workdir, name, benchmark):
    """Solve the network with SMS++ through pypsa2smspp."""
    import pypsa2smspp

    Path(workdir).mkdir(parents=True, exist_ok=True)
    transformation = pypsa2smspp.Transformation(
        **options, workdir=workdir, name=name
    )
    logger.info("Creating SMS++ model...")
    transformation.create_model(n)
    logger.info("Solving SMS++ model...")
    result = transformation.optimize()
    write_smspp_benchmark(
        benchmark,
        subprocess_time=getattr(result, "subprocess_time", 0) or 0,
        computational_time=getattr(result, "computational_time", 0) or 0,
    )
    status = str(getattr(result, "status", ""))
    if transformation.result is None or not result.is_optimal:
        return "warning", status
    transformation.retrieve_solution(n)
    return "ok", status


if __name__ == "__main__":
    logging.basicConfig(
        filename=snakemake.log.python,
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    solver = dict(snakemake.params.solver)
    name = solver["name"]
    options = dict(solver.get("options") or {})
    label = snakemake.wildcards.solver

    n = pypsa.Network(snakemake.input.network)

    if name == "smspp":
        # the options of the case for SMS++, e.g., enable_thermal_units where
        # the thermal generators are committable
        options.update(snakemake.params.case.get("smspp") or {})
        status, condition = solve_smspp(
            n,
            dict(options),
            workdir=snakemake.params.workdir,
            name=Path(snakemake.output.network).stem,
            benchmark=snakemake.params.smspp_benchmark,
        )
    else:
        status, condition = n.optimize(
            solver_name=name, solver_options=options, log_fn=snakemake.log.solver
        )
    logger.info(
        f"Solving status '{status}' with termination condition '{condition}'"
    )

    # the solver in the metadata, as pypsa-eur-instances records it
    n.meta = {
        "wildcards": dict(snakemake.wildcards),
        "solving": {
            "solver": {"name": name, "options": label},
            "solver_options": {label: options},
        },
    }
    # the network is written also when the solver fails, with no solution:
    # the status in the log says so to whoever collects the benchmarks
    n.export_to_netcdf(snakemake.output.network)
