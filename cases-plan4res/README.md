This folder contains the procedure to compare the performance offered by SMS++
on the stochastic instances of the generator of plan4res
([plan4res/resilient](https://github.com/plan4res/resilient)), i.e., the
capacity expansion of the European power system in 2030 (scenario ENVIS
NECPEssentials, 16 regions, hourly steps), whose demand and renewable
availability come in up to 105 scenarios. The workflow is that of
[pypsa-eur-instances](https://github.com/SPSUnipi/pypsa-eur-instances), a
submodule of this folder as it is of `cases-pypsa-eur`. Also the measure is
the same: one rule solves the networks, a benchmark of Snakemake records time
and memory, and one script collects them, which allows the results of the two
folders to be read with the same tools.

## Cases

The cases are the keys of `resilient.cases` in
`config/instances/resilient/expansion-power-EU16.yaml` of the submodule. Each
one gives the horizon (`begin`, `end` and possibly `days`), the number of
scenarios (the first ones of the generator, all equally likely), whether the
generators are extendable and the thermal ones committable, and the data that
change across the scenarios (`demand`, `renewables`):

| Case | Horizon | Hours | Scenarios | Unit commitment |
| --- | --- | ---: | ---: | --- |
| `w1_s21`, `w1_s52`, `w1_s105` | 2 to 8 July 2030 | 168 | 21, 52, 105 | no |
| `w2_s21`, `w2_s105` | 2 to 15 July 2030 | 336 | 21, 105 | no |
| `w4_s21`, `w4_s105` | 2 to 29 July 2030 | 672 | 21, 105 | no |
| `y1d12_s21` | the first day of each month of 2030 | 288 | 21 | no |
| `y1_s21` | 2030 | 8760 | 21 | no |
| `w1_s21_uc` | 2 to 8 July 2030 | 168 | 21 | yes |

The generator only builds a continuous interval. Hence, for `y1d12_s21` the
year is built and only the hours of the days in `days` are kept, each one
weighing (in `snapshot_weightings`) 365/12 hours; this keeps the operating
costs on the scale of the yearly investment costs. Note that the days kept
follow one another, and therefore a storage passes from the end of a day to
the beginning of the next day kept (say, from 1 January to 1 February). The
inflows of the hydro reservoirs are deterministic in all the cases, since the
SMS++ conversion of a stochastic network has no stochastic inflows. Finally,
`w1_s21_uc` differs from `w1_s21` only in the unit commitment, and comparing
the two should give the cost of the integer variables for each solver.

## Running the cases

The cases are run from this folder, after `git submodule update --init`, in
the environment of `pypsa-eur-instances` (`pixi install` there), with SMS++
installed through one of the channels of its
[installation guide](https://gitlab.com/smspp/smspp-project/-/wikis/Installing-SMS++):

```bash
cd pypsa-eur-instances
snakemake -c 32 solve_resilient_all \
  --configfile config/instances/resilient/expansion-power-EU16.yaml
```

First, the rule `retrieve_resilient_generator` clones the generator at the
commit in `resilient.generator.commit`. Next, `build_resilient_network` runs
the code cells of its notebook `CreateElecNetwork.ipynb` up to the export of
the network, with the settings of the case, and makes the network stochastic.
Finally, `solve_resilient_network` solves it with each pair of
`solving.solver.name` and `solving.solver.options`, by
`scripts/solve_network.py` as the other networks of the workflow are. One case
can be run by itself, asking for its network (e.g.,
`results/resilient-expansion-power-EU16/all/networks/resilient_w1_s21_gurobi.nc`).
The options compared by default are `gurobi-default` (PyPSA with Gurobi) and
`smspp-tssb-resilient`, i.e., SMS++ on the TwoStageStochasticBlock with the
run-of-river generators among the intermittent ones (their availability comes
in scenarios as that of wind and solar does). The Benders decomposition of
SMS++ is the option `smspp-tssb-bds`, to be added to both lists.

## Measure

Time and memory are those of the benchmark of Snakemake of the rule
`solve_resilient_network`, i.e., of the solve of one network by one solver.
This comprises reading the network, building the model (for SMS++, the
conversion by pypsa2smspp and the writing of the file), solving it and
reading the solution back into the network; it does not comprise building the
network. For SMS++ the file with suffix `.smspp` also gives the time of the
solver as pySMSpp measures it. The objective to compare is
`objective + objective_constant` of the solved network: PyPSA keeps the
constant part of the costs out of the objective of the solver, while SMS++
reports it. The runs should be made one at a time, on a machine with no other
load (the load average at the start of each run may be recorded too). The
Gurobi licence should not be shared with other runs at the same time, since a
licence that refuses a session usually makes the run fail, or leaves SMS++
without the subproblems it could not solve.

## Files

With `<case>` a key of `resilient.cases` and `<solver>` a solver of
`solving.solver.name`, the results are in
`results/resilient-expansion-power-EU16/all/` of the submodule:

```text
networks/resilient_<case>_<solver>.nc
configs/config.resilient_<case>_<solver>.yaml
benchmarks/solve_network/resilient_<case>_<solver>
benchmarks/solve_network/resilient_<case>_<solver>.smspp
logs/solve_network/resilient_<case>_<solver>_python.log
```

They are collected as those of `cases-pypsa-eur` are, by

```bash
python scripts/collect_solve_benchmarks.py \
  --folder resilient-expansion-power-EU16/all \
  --output results/resilient-expansion-power-EU16/solve_benchmarks.csv
```

which writes one row per network and solver. Each row has `network_type`
`resilient` and the case in `opts`, the objective and its constant, the
columns of the benchmark of Snakemake (`s` the seconds, `max_rss` the peak
memory in MB) and, for SMS++, `smspp_optimization_s`.
