#!/usr/bin/env python3
from __future__ import print_function
import sys

import yaml
from yaml import CLoader


def merge(user, default):
    if isinstance(user, dict) and isinstance(default, dict):
        for k, v in default.items():
            if k not in user:
                user[k] = v
            else:
                user[k] = merge(user[k], v)
    return user


fileone = yaml.load(open(sys.argv[1], "r"), Loader=CLoader)
for resname in fileone["residues"]:
    break
otherfile = sys.argv[2]
with open(otherfile, "r") as infile:
    otherfileyaml = yaml.load(infile, Loader=CLoader)
    for resname2 in otherfileyaml["residues"]:
        break
    if resname2 != resname:
        otherfileyaml["residues"][resname] = otherfileyaml["residues"][resname2].copy()
        del otherfileyaml["residues"][resname2]

    fileone = merge(fileone, otherfileyaml)

print(yaml.dump(fileone))
