# PyPSA-Eur instances for SMS++ benchmarks

This directory documents how the PyPSA-Eur instances used to compare SMS++
and the PyPSA/Gurobi formulation are generated. The workflow is maintained in
the [pypsa-eur-instances](https://github.com/SPSUnipi/pypsa-eur-instances)
submodule.

## How the instances are obtained

The instances are built from the PyPSA-Eur input data through its Snakemake
workflow: retrieve and prepare the electricity network, generation fleet,
demand and renewable profiles; select the countries; cluster the network
spatially and temporally; and prepare the optimisation model. Sector-coupled
cases additionally include the energy demands and technologies of the other
sectors. The YAML files under `config/instances/` select the benchmark family.

The Italian electricity benchmarks include fixed-capacity dispatch and
capacity expansion, with separate configurations for no unit commitment
(`noUC`), linearised unit commitment (`linUC`) and unit commitment (`UC`).
Spatial resolution is selected through `scenario.clusters`. Temporal
resolution uses representative periods: for example, `24c24` selects 24
representative periods of 24 hours. The scenario YAML can override the temporal
resolution specified in the main configuration.

For the stochastic capacity-expansion cases, `build_stochastic_network.py`
starts from the prepared deterministic network and applies the transformations
in `config/instances/scenarios/tssb/`. For example, the demand scenarios scale
`Load.p_set` using a normal distribution with mean 1, standard deviation 0.1,
bounds 0.8–1.2 and seed 123. The ten-scenario configuration assigns probability
0.1 to each scenario. The current `scenarios-power-limited.yaml` selects
`120c24` and 10, 20, 50, 100 or 200 demand scenarios.

The same prepared PyPSA network is solved through the configured backends.
`pypsa2smspp` converts it into the SMS++ block representation; `pySMSpp`
provides the Python interface to SMS++. The solver profiles and block
configuration files are in `config/config.default.yaml` and `config/smspp/`.
The stochastic profiles include Benders decomposition and an outer investment
formulation with parallel inner solves.

## Software revisions

The following are the local source revisions checked on **18 November 2026**.
They describe the working setup at documentation time; they are not a claim
that every previously generated result used these exact revisions.

| Repository | Branch | Commit |
| --- | --- | --- |
| `pypsa-eur-instances` (generation checkout) | `run-pr17` | `97db7e3f66ee526408a967721f1c2c6d32774d78` |
| `smspp-project` | `develop` | `9dec4ad3a51364a8c3544e5df7743be63eb92e33` |
| `pypsa2smspp` | `fix/sector-solution-mapping` | `30fef5eb4f616dc76842eadbfe56afbb9624563e` |
| `pySMSpp` | `main` | `b34cbe3cbda10535af28e545aad923129c6c0af5` |

The `pypsa-eur-instances` submodule recorded by this umbrella repository
currently points to `8687b29e24d3a345ca246aa00735d8d68952b707`, which differs
from the generation checkout above. Initialising the submodule alone therefore
does not reproduce that checkout. No submodule pointer is changed by this
documentation update.

The local Conda environment `pypsa-eur-smspp-instances` imports editable
installations from `/home/pampado/pypsa2smspp` and `/home/pampado/pySMSpp`
(package versions `0.0.5` and `0.2.0`). These are separate from the copies
inside `smspp-project`. At the SMS++ revision above, its own submodules point
to `pypsa2smspp` commit `5ffeb6251e36df5ec011e50c0efb21f438ebc0cd` and
`pySMSpp` commit `bb4f460a61d07982815f0f6c6c9ec1c624be7187`.

SMS++ sources and enabled submodules were updated on 17 November 2026;
the update did **not** rebuild the libraries or executables. Rebuild SMS++
and its Python bindings before using the new sources for tests.

## Commands

From the root of `RESILIENT-instances`, initialise the generation repository:

```bash
git submodule update --init --recursive cases-pypsa-eur/pypsa-eur-instances
cd cases-pypsa-eur/pypsa-eur-instances
```

To select the generation revision listed above in a clean checkout:

```bash
git fetch origin
git checkout 97db7e3f66ee526408a967721f1c2c6d32774d78
```

The commands below run from the root of `pypsa-eur-instances`. On the test
machine the environment is activated with:

```bash
conda activate pypsa-eur-smspp-instances
```

For a new installation, the PyPSA-Eur environment specification is
`envs/environment.yaml`; SMS++, its bindings and the converter must also be
installed, and the configured commercial solvers require their licences.
Input downloads may require the credentials of the corresponding data services.

Generate and solve the Italian electricity dispatch instances:

```bash
snakemake --cores 32 solve_elec_networks \
  --configfile config/instances/dispatch/power-IT-noUC.yaml
```

Generate and solve the deterministic Italian electricity capacity-expansion
instances:

```bash
snakemake --cores 32 solve_elec_networks \
  --configfile config/instances/capacity-expansion/power-IT-noUC.yaml
```

Generate and solve the stochastic Italian electricity capacity-expansion
instances with the configured Gurobi and SMS++ profiles:

```bash
snakemake --cores 32 solve_elec_networks \
  --configfile config/instances/tssb/power-IT-noUC.yaml
```

Use `--dry-run` before running to inspect the jobs and resolved output paths.
The main configuration selects a scenario file through `run.scenarios.file`;
`run.name: all` runs all entries in that file. Adjust the configurations to
select the desired sizes, scenarios and solver profiles. `--cores` controls
the workflow budget; solver thread counts are configured separately.

Sector-coupled configurations use the `solve_sector_networks` target and are
available under `config/instances/capacity-expansion/` and
`config/instances/tssb/`. Before running the current stochastic
`sector-IT-noUC.yaml`, correct its reference to
`config/instances/scenarios/tssb/stochastic-demand.yaml`: that file is absent
from the inspected checkout; numbered demand configurations are available.

## Generated files and reproducibility

Prepared networks are written under `resources/<run.prefix>/.../networks/`;
solved networks, resolved configurations, logs and benchmarks are under
`results/<run.prefix>/<run.name>/`. In particular:

- `networks/`: solved PyPSA NetCDF networks;
- `configs/`: resolved YAML configurations for each instance and solver;
- `smspp/`: the converter/solver working directory used by the SMS++ backend;
- `logs/` and `benchmarks/`: solver output and workflow measurements.

Keep the resolved configuration together with the source revisions and the
results. The generation checkout currently has uncommitted changes, including
`config/instances/capacity-expansion/sector-IT-noUC.yaml`; its commit alone
does not capture those edits. For historical benchmarks, use the saved
per-instance configuration and logs rather than assuming that today's YAML
files or package checkouts describe the original run.
