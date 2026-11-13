"""
Solve a stochastic network of the generator of Man0euVRE with the solver
``wildcards.solver`` of ``config.yaml``: with PyPSA if its ``name`` is a
solver of PyPSA, with SMS++ through pypsa2smspp if it is ``smspp`` (the
``options`` being the arguments of its ``Transformation``). The solved network
is written with the solver and its options in its metadata, as the networks of
pypsa-eur-instances are; time and memory are measured by the benchmark of
Snakemake.
"""

import logging
from pathlib import Path

import pypsa

logger = logging.getLogger(__name__)


def solve_smspp(n, options, workdir, name):
    import pypsa2smspp

    Path(workdir).mkdir(parents=True, exist_ok=True)
    transformation = pypsa2smspp.Transformation(**options, workdir=workdir,
                                                name=name)
    transformation.create_model(n)
    result = transformation.optimize()
    if not result.is_optimal:
        return "warning", str(result.status)
    transformation.retrieve_solution(n)
    return "ok", str(result.status)


if __name__ == "__main__":
    logging.basicConfig(filename=snakemake.log.python, level=logging.INFO)

    solver = snakemake.params.solver
    options = dict(solver.get("options") or {})
    n = pypsa.Network(snakemake.input.network)

    if solver["name"] == "smspp":
        # the case may add arguments of the Transformation, e.g.,
        # enable_thermal_units where the thermal generators are committable
        options.update(snakemake.params.case.get("smspp") or {})
        status, condition = solve_smspp(n, options, snakemake.params.workdir,
                                        Path(snakemake.output.network).stem)
    else:
        status, condition = n.optimize(solver_name=solver["name"],
                                       solver_options=options,
                                       log_fn=snakemake.log.solver)
    logger.info(f"Solving status '{status}' with termination condition "
                f"'{condition}'")
    # a network that is not solved is not written
    if status != "ok":
        raise RuntimeError(f"Solving status '{status}' with termination "
                           f"condition '{condition}'.")

    n.meta = {
        "wildcards": dict(snakemake.wildcards),
        "solving": {
            "solver": {"name": solver["name"],
                       "options": snakemake.wildcards.solver},
            "solver_options": {snakemake.wildcards.solver: options},
        },
    }
    n.export_to_netcdf(snakemake.output.network)
