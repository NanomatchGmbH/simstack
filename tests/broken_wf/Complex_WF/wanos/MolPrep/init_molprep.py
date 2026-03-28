#!/usr/bin/env python3

"""
Script that uses WaNo input to write QuantumPatch input.
"""

from os import environ
import yaml

# Reads rendered WaNo file
with open("rendered_wano.yml", "r") as ymlin:
    wano = yaml.safe_load(ymlin)

with open("parametrizer_settings_template.yml", "r") as ymlin:
    param_settings = yaml.safe_load(ymlin)

param_settings["Molecule Settings"]["Optimize Molecule"] = wano["Optimize Molecule"]
param_settings["DFT Engine"]["Threads"] = environ["UC_TOTAL_PROCESSORS"]
param_settings["DFT Engine"]["Memory (MB)"] = (
    float(environ["UC_MEMORY_PER_NODE"]) * 0.85
)

with open("parametrizer_settings.yml", "w") as ymlout:
    yaml.safe_dump(param_settings, ymlout)


do_dh = wano["Compute Dihedral Forcefield"]
print("do_dh from wano")
print(do_dh)

if do_dh:
    with open("dhp_settings_template.yml", "r") as ymlin:
        dhp_settings = yaml.safe_load(ymlin)
    dhp_settings["DFT_options"]["memory_per_thread"] = int(
        float(environ["UC_MEMORY_PER_NODE"]) / float(environ["UC_TOTAL_PROCESSORS"])
    )
    with open("dhp_settings.yml", "w") as ymlout:
        print("saving dhp settings")
        yaml.safe_dump(dhp_settings, ymlout)

report_dict = {}
report_dict["DFT Method"] = "Psi4"
report_dict["DFT Settings"] = param_settings["DFT Engine"][
    param_settings["DFT Engine"]["Engine"] + " Settings"
]
report_dict["Geometry Optimization"] = wano["Optimize Molecule"]
report_dict["Generated DH forcefields"] = do_dh

with open("output_dict.yml", "w") as reportout:
    yaml.safe_dump(report_dict, reportout)
