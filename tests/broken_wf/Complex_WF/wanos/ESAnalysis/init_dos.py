#!/usr/bin/env python3

"""
Script that uses WaNo input to write QuantumPatch input.
"""

import copy
import yaml
import sys
import math

from QuantumPatch.Shredder.Parsers.ParserCommon import parse_system


class QuantumPatchWaNoError(Exception):
    pass


def get_disorder_settings(wano, cpu_per_node=1):
    # Shorthands
    wano_env = wano["Tabs"]["General"]["Shell for Disorder and Couplings"]
    wano_engines = wano["Tabs"]["Engines"]

    with open("disorder_settings_template.yml", "r") as qpngin:
        cfg = yaml.safe_load(qpngin)  # Script will modify this and re-write it

    # Shells
    number_core_mols = min(100, int(wano_env["Number of molecules"]))
    cfg["System"]["Core"]["number"] = number_core_mols
    env_shell = cfg["System"]["Shells"]["0"]
    env_shell["number"] = int(wano_env["Number of molecules"]) - number_core_mols

    # Adapt engines
    mem_per_cpu = wano_engines["General engine settings"]["Memory per CPU (MB)"]
    cfg["DFTEngine"]["user"]["PySCF env"]["mem_per_cpu"] = mem_per_cpu
    cfg["DFTEngine"]["user"]["polFF"]["threads"] = cpu_per_node - 1

    return cfg


def get_IPEA_settings(wano, cpu_per_node=1, tot_nodes=1):
    # Shorthands
    wano_general = wano["Tabs"]["General"]["General Settings"]
    wano_core = wano["Tabs"]["General"]["Core Shell"]
    wano_env = wano["Tabs"]["General"]["Shell for Disorder and Couplings"]
    wano_engines = wano["Tabs"]["Engines"]

    do_disorder = wano_general["Compute disorder"]

    with open("dos_settings_template.yml", "r") as qpngin:
        cfg = yaml.safe_load(qpngin)  # Script will modify this and re-write it

    # Shells
    ## Adapt and analyse core shell re numer of molecules
    core_mode = wano_core["Shell size defined by"]
    core_shell = cfg["System"]["Core"]
    if core_mode == "Number of Molecules":
        core_shell["type"] = "number"
        core_shell["number"] = wano_core["Number of molecules"]
        number_core_mols = wano_core["Number of molecules"]
    elif core_mode == "Number of Molecules of each Type":
        core_shell["type"] = "number_by_type"
        core_shell["number"] = wano_core["Number of molecules"]
        number_core_mols = wano_core["Number of molecules"]

        system = parse_system("morphology.cml")
        number_types = len(set(system.moltypes))
        number_core_mols *= number_types
    elif core_mode == "List of Molecule IDs":
        core_shell["type"] = "list"
        core_shell["list"] = wano_core["List of molecule IDs"]
        number_core_mols = 0
        mol_list = wano_core["List of molecule IDs"].split(";")
        for m_id in mol_list:
            if "-" in m_id:
                m_ids = m_id.split("-")
                number_core_mols += 1 + int(m_ids)[1] - int(m_ids[0])
            else:
                number_core_mols += 1
    else:
        raise QuantumPatchWaNoError(
            "only core modes number, number by type and list supported in DOS WaNo. Exiting"
        )

    # Env shell
    if do_disorder:
        env_shell = cfg["System"]["Shells"]["1"]
        env_shell["shellsize_by"] = "number_or_cutoff"
        env_shell["number"] = wano_env["Number of molecules"] - number_core_mols
    # if no disorder, we do not set shellsize_by and number of molecules

    # Adapt engines
    mem_per_cpu = wano_engines["General engine settings"]["Memory per CPU (MB)"]

    ## Adapt PySCF 1 and 2 engines
    pyscf_1_engine = cfg["DFTEngine"]["user"]["PySCF 1"]
    pyscf_1_engine["mem_per_cpu"] = mem_per_cpu
    pyscf_1_engine["polFF_env"] = True
    threads = int((cpu_per_node - 1) // math.ceil(number_core_mols / tot_nodes))
    thread_string = f"auto.min.{threads}"
    pyscf_1_engine["threads"] = thread_string
    pyscf_2_engine = copy.deepcopy(pyscf_1_engine)
    pyscf_2_engine["polFF_env"] = False
    cfg["DFTEngine"]["user"]["PySCF 2"] = pyscf_2_engine

    ## Small adaptations in polFF and PySCF env
    cfg["DFTEngine"]["user"]["polFF"]["threads"] = cpu_per_node - 1  # thread_string
    cfg["DFTEngine"]["user"]["PySCF env"]["mem_per_cpu"] = mem_per_cpu

    # Adapt SpecialSteps -> engine
    GW_engine = wano_engines["GW settings"]["GW Engine"]
    GW_func = wano_engines["GW settings"][f"Functional GW {GW_engine}"]

    eval_engine = cfg["DFTEngine"]["user"][f"{GW_engine} Evalstep"]
    eval_engine["functional"] = GW_func
    eval_engine["threads"] = cpu_per_node - 1
    mem_scale = {"PySCF": 0.85, "Turbomole": 0.75}
    eval_engine["memory"] = int(mem_per_cpu * (cpu_per_node - 1) * mem_scale[GW_engine])
    cfg["SpecialSteps"]["EvalStep"]["engine"] = f"{GW_engine} Evalstep"

    return cfg


if __name__ == "__main__":
    # get available resources from arguments
    tot_cpu = int(sys.argv[1])
    tot_nodes = int(sys.argv[2])
    cpu_per_node = int(sys.argv[3])
    assert (
        cpu_per_node * tot_nodes == tot_cpu
    ), "total cpu does not match total nodes times cpu per node"

    with open("rendered_wano.yml", "r") as wanoin:
        wano = yaml.safe_load(wanoin)

    wano_general = wano["Tabs"]["General"]["General Settings"]
    wano_core = wano["Tabs"]["General"]["Core Shell"]
    wano_env = wano["Tabs"]["General"]["Shell for Disorder and Couplings"]
    wano_engines = wano["Tabs"]["Engines"]
    wano_storage = wano["Tabs"]["Storage"]
    # depending on IPEA absolute levels, use different template
    if wano_general["Compute absolute levels of IP/EA"]:
        cfg = get_IPEA_settings(wano, cpu_per_node=cpu_per_node, tot_nodes=tot_nodes)
    elif wano_general["Compute disorder"]:
        cfg = get_disorder_settings(wano, cpu_per_node=cpu_per_node)
    else:
        # if neither disorder nor absolute levels: crash
        raise QuantumPatchWaNoError(
            "One of computation of absolute levels or disorder is required"
        )

    if wano_general[
        "Compute disorder"
    ]:  # if not compute disorder, leave couplings on false, as in template
        cfg["QuantumPatch"]["calculateJs"] = wano_general["Compute couplings"]
    else:
        cfg["QuantumPatch"]["calculateJs"] = False

    storage_location = wano_storage["Storage Location"]
    if storage_location == "Scratch":
        cfg["QuantumPatch"]["default_storage_location"] = "scratch"

    # Write modified settings file to disk.
    with open("settings_ng.yml", "w") as qpngout:
        yaml.dump(cfg, qpngout, default_flow_style=False)

    with open("output_dict.yml", "w") as report:
        yaml.dump(cfg, report, default_flow_style=False)
