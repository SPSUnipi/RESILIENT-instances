This folder compares SMS++ with PyPSA on the stochastic instances of the
generator of plan4res ([plan4res/resilient](https://github.com/plan4res/resilient),
the submodule `resilient`), i.e., the capacity expansion of the European power
system in 2030 over 16 regions, with up to 105 scenarios of the demand and of
the availability of the renewables. The workflow uses PyPSA, pypsa2smspp and
pySMSpp only, and its results have the format of those of pypsa-eur-instances,
whose scripts read them as they are.

```bash
git submodule update --init cases-plan4res/resilient
conda env create -f envs/environment.yaml && conda activate plan4res-smspp
snakemake -c 32 solve_all && snakemake -c 1 collect_benchmarks
```

SMS++ is installed separately (see the
[installation guide](https://gitlab.com/smspp/smspp-project/-/wikis/Installing-SMS++)).

The cases (`config.yaml`) sample 1 or 2 days per month of 2030, whose hourly
costs are weighted by the days they stand for, while the storages evolve hour
by hour from one day kept to the next; one case covers all of 2030, and one
adds the unit commitment of the thermal generators. The inflows of the hydro
reservoirs are deterministic, since the SMS++ conversion has no stochastic
inflows, and there is no reserve. Time and memory are those of the benchmark of
Snakemake of `solve_network`, from reading the network to writing the solved
one, and the value to compare is `objective + objective_constant`; the runs are
best made one at a time on an otherwise idle machine.
