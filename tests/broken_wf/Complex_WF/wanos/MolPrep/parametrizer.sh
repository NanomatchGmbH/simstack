#!/bin/bash

set -euo pipefail

echo "Converting molecule input to mol2 format"
filetype=`QPGuessMoltype input_molecule`
filetype=${filetype,,}
mv input_molecule initial_input_molecule.$filetype

obabel initial_input_molecule.$filetype -oxyz -Oinitial_input_molecule.xyz
obabel initial_input_molecule.xyz -omol2 -Oinput_molecule.mol2

echo "Running QPParametrizer"
QPParametrizer
$DEPTOOLS/add_dihedral_angles.sh output_molecule.mol2 molecule.spf

zip report.zip output_molecule.mol2 molecule.pdb molecule.spf
# cp rendered_wano.yml output_dict.yml
cat mol_data.yml >> output_dict.yml

obabel -imol2 output_molecule.mol2 -osvg > output_molecule.svg
