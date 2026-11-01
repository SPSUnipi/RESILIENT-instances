This folder contains the procedure to compare the performance offered by SMS++
on the stochastic instances of the generator of plan4res
([plan4res/resilient](https://github.com/plan4res/resilient)), i.e., the
capacity expansion of the European power system in 2030 (scenario ENVIS
NECPEssentials, 16 regions, hourly steps), whose demand and renewable
availability come in up to 105 scenarios. The workflow is a Snakemake one of
its own, which only uses PyPSA, pypsa2smspp and pySMSpp (PyPSA-Eur is not
needed).
However, its results, benchmarks and logs have the names and the format of
those of [pypsa-eur-instances](https://github.com/SPSUnipi/pypsa-eur-instances),
and the same scripts read the results of both.

## Assumptions

The instances are built as follows; everything not listed is as the generator
makes it.

- The network is that of the notebook `CreateElecNetwork.ipynb` of the
  generator, at the commit in `generator.commit` of `config.yaml`, whose code
  cells are run up to the export of the network. Of the settings of the
  generator only the horizon (`BeginDataset`, `EndDataset`) and the flags
  `extendable` and `committable` are changed.
- 16 buses, one per region, all electric, linked by 34 links (the
  interconnections, extendable when `extendable` is set); one slack generator
  per bus, the load shedding.
- With `extendable`, the solar generators (16), 14 of the 24 batteries and
  the 34 links are extendable, with continuous investment; the other
  generators and the 23 hydro storage units are not.
- With `committable`, the thermal generators (biomass, coal, gas, geothermal,
  nuclear, ocean, oil) are committable, and none of them is extendable.
- The scenarios are the first `scenarios` ones of the generator (`2020_0`,
  `2020_1`, and so on, at most 105), all equally likely.
- The scenarios change the demand of each bus and the availability
  (`p_max_pu`) of each renewable generator with a positive maximum power, as
  the generator gives them. The inflows of the hydro reservoirs are those of
  the deterministic network in all the scenarios, since the SMS++ conversion
  of a stochastic network has no stochastic inflows.
- The investment is the first stage, common to all the scenarios, and the
  operation is the second one, per scenario.
- With `days`, only the hours of those days are kept, each weighing (in
  `snapshot_weightings`) as many hours as the horizon has days over the days
  kept (365/12 for the first day of each month of a year). This keeps the
  operating costs on the scale of the yearly investment costs. The days kept
  follow one another, and a storage passes from the end of a day to the
  beginning of the next day kept.
- The storage units are cyclic, or not, as the generator makes them (the
  batteries and 14 of the hydro units are).
- There is no reserve requirement, which PyPSA would not have to compare
  with.

## Cases

The cases are the keys of `cases` in `config.yaml`:

| Case | Horizon | Hours | Scenarios | Unit commitment |
| --- | --- | ---: | ---: | --- |
| `w1_s21`, `w1_s52`, `w1_s105` | 2 to 8 July 2030 | 168 | 21, 52, 105 | no |
| `w2_s21`, `w2_s105` | 2 to 15 July 2030 | 336 | 21, 105 | no |
| `w4_s21`, `w4_s105` | 2 to 29 July 2030 | 672 | 21, 105 | no |
| `y1d12_s21` | the first day of each month of 2030 | 288 | 21 | no |
| `y1_s21` | 2030 | 8760 | 21 | no |
| `w1_s21_uc` | 2 to 8 July 2030 | 168 | 21 | yes |

`w1_s21_uc` differs from `w1_s21` only in the unit commitment, and comparing
the two should give the cost of the integer variables for each solver.

## Running the cases

The environment is that of `envs/environment.yaml`, with SMS++ installed
through one of the channels of its
[installation guide](https://gitlab.com/smspp/smspp-project/-/wikis/Installing-SMS++)
(the tools of SMS++ have to be in the `PATH`, where pySMSpp looks for them):

```bash
conda env create -f envs/environment.yaml
conda activate plan4res-smspp
snakemake -c 32 solve_all
snakemake -c 1 collect_benchmarks
```

First, the rule `retrieve_generator` clones the generator at the commit in
`generator.commit`. Next, `build_network` (`scripts/build_network.py`) runs
the code cells of the notebook with the settings of the case and makes the
network stochastic. Finally, `solve_network` (`scripts/solve_network.py`)
solves it with each solver of `solvers` in `config.yaml`. With `name` a
solver of PyPSA (`gurobi`) PyPSA solves it; with `name: smspp` the
`Transformation` of pypsa2smspp does, with a template of pySMSpp as
`configfile`, and the solution is read back into the network. One case can
be run by itself, asking for its network (e.g.,
`results/networks/resilient_w1_s21_gurobi.nc`). The solvers are
`gurobi`, `smspp-tssb` (SMS++ on the TwoStageStochasticBlock as one
problem, solved by Gurobi) and `smspp-tssb-bds` (its Benders decomposition).
A case may add arguments of the `Transformation` for the solvers of SMS++
(`smspp`): `w1_s21_uc` adds `enable_thermal_units`, without which SMS++
writes every generator as an intermittent one.

## Measure

Time and memory are those of the benchmark of Snakemake of the rule
`solve_network`, i.e., of the solve of one network by one solver. This
comprises reading the network, building the model (for SMS++, the conversion
by pypsa2smspp and the writing of the file), solving it and reading the
solution back into the network; it does not comprise building the network.
For SMS++ the file with suffix `.smspp` also gives the time of the tool of
SMS++ as pySMSpp measures it. The objective to compare is
`objective + objective_constant` of the solved network: PyPSA keeps the
constant part of the costs out of the objective of the solver, while SMS++
reports it. The runs should be made one at a time, on a machine with no other
load (the load average at the start of each run may be recorded too). The
Gurobi licence should not be shared with other runs at the same time, since a
licence that refuses a session usually makes the run fail, or leaves SMS++
without the subproblems it could not solve.

## Files

With `<case>` a key of `cases` and `<solver>` one of `solvers`:

```text
resources/networks/resilient_<case>.nc
results/networks/resilient_<case>_<solver>.nc
results/benchmarks/solve_network/resilient_<case>_<solver>
results/benchmarks/solve_network/resilient_<case>_<solver>.smspp
results/logs/solve_network/resilient_<case>_<solver>_python.log
results/solve_benchmarks.csv
```

The last one is written by `collect_benchmarks`
(`scripts/collect_solve_benchmarks.py`, the script of pypsa-eur-instances),
with one row per network and solver. Each row has `network_type`
`resilient` and the case in `opts`, the objective and its constant, the
columns of the benchmark of Snakemake (`s` the seconds, `max_rss` the peak
memory in MB) and, for SMS++, `smspp_optimization_s`.
