## Simstack client - Installation from source with conda

All dependencies of SimStack can be installed within conda using a  `simstack_env.yml` file.
 Just follow these few steps:
 
```bash
git clone --recursive ssh://git@gitlab.nanobuild.de:2222/nanomatch/simstack.git
cd simstack
conda env create -f simstack_env.yml
conda activate simstack
./simstack
```
> **Note:** if the `conda env create -f simstack_env.yml` step fails due to certain dependencies that can't be met, it might be sufficient to remove the version string or the probmlematic dependency from the `simstack_env.yml` file.
{.is-warning}
