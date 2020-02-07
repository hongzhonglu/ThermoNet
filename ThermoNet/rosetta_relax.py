#!/usr/bin/env python3

import os
from argparse import ArgumentParser


def main():
    """
    """
    # parse command-line arguments
    parser = ArgumentParser()
    parser.add_argument('-l', '--variant-list', dest='variant_list', type=str,
            required=True, help='A list of variants, one per line in the format "PDB CHAIN POS WT MUT"')
    # parser.add_argument('-s', '--start-struct', dest='start_struct', type=str,
    #        required=True, help='PDB file of the starting structure.')
    parser.add_argument('--rosetta-bin', dest='rosetta_bin', type=str,
            required=True, help='Rosetta FastRelax binary executable.')
    parser.add_argument('--base-dir', dest='base_dir', type=str,
            required=True, help='The base directory to store all data generated by this script.')
    args = parser.parse_args()

    # parse all the variants into a list
    variants = []
    with open(args.variant_list, 'rt') as ipf:
        for l in ipf:
            pdb_chain, pos, w, m = l.strip().split()
            variants.append((pdb_chain, w + pos + m))

    # create relevant directories and input files for submitting slurm jobs
    # for each pair of wild-type and variant
    base_dir = os.path.abspath(args.base_dir)
    for pdb_chain, variant in variants:
        # create and change to necessary directory
        chain_dir = os.path.join(base_dir, pdb_chain)
        if not os.path.exists(chain_dir):
            os.mkdir(chain_dir)
            print('Created directory:', chain_dir)

        os.chdir(chain_dir)
        print('Changed to', chain_dir)

        # create a resfile
        variant_resfile = pdb_chain + '_' + variant + '.resfile'
        with open(variant_resfile, 'wt') as opf:
            opf.write('NATAA\n')
            opf.write('start\n')
            opf.write(variant[1:-1] + ' ' + pdb_chain[-1] + ' PIKAA ' + variant[-1])

        # rosetta_cmd
        start_struct = os.path.join(base_dir, pdb_chain, pdb_chain + '_relaxed.pdb')
        rosetta_relax_cmd = ' '.join([args.rosetta_bin, 
            '-in:file:s', start_struct, '-in:file:fullatom',
            '-relax:constrain_relax_to_start_coords',
            '-out:no_nstruct_label', '-relax:ramp_constraints false',
            '-relax:respect_resfile',
            '-packing:resfile', variant_resfile,
            # '-out:nstruct', '1',
            '-out:file:scorefile', os.path.join(chain_dir, pdb_chain + '_relaxed.sc'),
            '-out:suffix', '_' + variant + '_relaxed'
        ])

        # run Rosetta FastRelax
        os.system(rosetta_relax_cmd)


if __name__ == '__main__':
    main()