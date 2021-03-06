#!/usr/bin/env python
"""
FAFSA SEQ
=========

Description
------------
Downloads the fafsa sequence from the pdb and sees where the sequence begins in
the fafsa sequence and adds it to the csv file.

Usage
-----
```
fafsaseq.py DFICSVFILE
```
"""
from __future__ import print_function
import pandas as pd
import numpy as np
from dfi.datafiles import *

mapres = {'ALA': 'A',
          'CYS': 'C',
          'ASP': 'D',
          'GLU': 'E',
          'PHE': 'F',
          'GLY': 'G',
          'HIS': 'H',
          'ILE': 'I',
          'LYS': 'K',
          'LEU': 'L',
          'MET': 'M',
          'PRO': 'P',
          'ARG': 'R',
          'GLN': 'Q',
          'ASN': 'N',
          'SER': 'S',
          'THR': 'T',
          'TRP': 'W',
          'TYR': 'Y',
          'VAL': 'V',
          'HIE': 'H'}


def getuniprols(pdbid):
    """
    Insert PDB and get UNIPROTID(s) from table

    Parameters
    -----
    pdbid: str
       4 letter code PDBID

    Returns
    ------
    ls_unipro: ls
       list of uniprotID(s) associated with PDBID
    """
    import pandas as pd
    pdbid = pdbid.upper()
    mapdata = pd.read_csv(unipro_pdb, index_col='pdbID')
    nids = len(mapdata.ix[pdbid].values)
    if nids > 1:
        return [unipro[0] for unipro in mapdata.ix[pdbid].values]
    else:
        return [unipro for unipro in mapdata.ix[pdbid].values]


def get_fastaseq(ID):
    """
    get_fasta sequence from the uniprot database

    Parameters
    ----------
    ID: str
       uniprotID or pdbID

    Returns
    -------
    fasta_seq: str
       fasta sequence
    """
    import urllib2

    if len(ID) == 4:
        pdbURL = "http://www.rcsb.org/pdb/files/fasta.txt?structureIdList="
        response = urllib2.urlopen(pdbURL + ID)
    else:
        uniproURL = "http://www.uniprot.org/uniprot/"
        response = urllib2.urlopen(uniproURL + ID + '.fasta')
    return response.read()


def parsefafstaurl(html,
                   seqonly=True,
                   Verbose=False):
    """Parses html fafasa sequence and returns a string of the sequence

    Parameters
    ----------
    html:str
       html output of fasta sequence
    seqonly:bool
       bool of sequence
    """
    html = html.split('\n')
    fseq = ''
    for line in html:
        if(Verbose):
            print(line)
        if line.startswith('>') and seqonly:
            continue
        fseq = fseq + line
    return fseq


def compareseq(smallseq, fseq, numseq=4):
    "Compare sequence to find contiguous sequence"
    for j in range(len(smallseq)):
        for i in range(len(fseq)):
            print(fseq[i:i + numseq], smallseq[j:j + numseq])
            if smallseq[j:j + numseq] == fseq[i:i + numseq]:
                match = i + 1
                print("Found a match at %d" % (i + 1))
                return j, match
    print("No match")
    return False


def parsefafsaseq(fname, uniprols=None):
    """
    Parse the fafas seq using the csv filename and uniprotids.
    Returns a list of the outfile names
    """
    outfilels = []
    data = pd.read_csv(fname, index_col='ResI')

    # convert three letter code to one letter code sequence
    bigseq = np.array(data['Res'].values, dtype=str)
    smallseq = ''
    for threeseq in bigseq:
        smallseq = smallseq + str(mapres[threeseq])

    import urllib2
    pdbURL = "http://www.pdb.org/pdb/files/fasta.txt?structureIdList="
    uniproURL = "http://www.uniprot.org/uniprot/"

    pdbname = fname.split('-')[0]

    if uniprols:
        for uniproid in uniprols:
            print(uniproid)
            print(uniproURL + uniproid + '.fasta')
            response = urllib2.urlopen(uniproURL + uniproid + '.fasta')
            fseq = parsefafstaurl(response.read())
            struc_match, seq_match = compareseq(smallseq, fseq, numseq=4)
            if seq_match:
                print("seq_match", seq_match)
                print("struc_match", struc_match)
                ind_match = seq_match - 1
                matchseq = [f for f in fseq[ind_match - struc_match:]]
                print('fseq', fseq)
                print("---")
                print('smallseq', smallseq)
                print('nmatchseq', len(matchseq))
                print('nsmallseq', len(smallseq))
                if len(matchseq) < len(smallseq):
                    ntimes = len(smallseq) - len(matchseq)
                    for i in range(ntimes):
                        matchseq.append('NA')

                while len(matchseq) > len(smallseq):
                    matchseq = matchseq[:-1]

                print("fafalen:" + str(len(fseq)))
                data['fafsa_seq'] = pd.Series(matchseq, index=data.index)
                fafsa_ls = range(seq_match - struc_match,
                                 len(smallseq) + seq_match - struc_match)
                print("fafsa_ls", fafsa_ls)
                data['fafsa_ind'] = pd.Series(fafsa_ls, index=data.index)
                data['unipro'] = pd.Series([uniproid for i in range(
                    seq_match, len(smallseq) + seq_match)], index=data.index)
                outfile = pdbname + '-' + uniproid + '-dfianalysis.csv'
                print("Writing out to: " + outfile)
                data.to_csv(outfile)
                outfilels.append(outfile)
    else:
        print("Taking from the PDB")
        response = urllib2.urlopen(pdbURL + pdbname)
        fseq = parsefafsaurl(response.read())
        struc_match, seq_match = compareseq(smallseq, fseq, numseq=4)
        if seq_match:
            data['fafsa_ind'] = pd.Series(
                range(seq_match, len(smallseq) + seq_match), index=data.index)
            outfile = pdbname + '-dfianalysis.csv'
            data.to_csv(outfile)
            outfilels.append(outfile)

    return outfilels


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit()

    pdbid = sys.argv[1].split('-')[0]

    uniprols = getuniprols(pdbid)
    if uniprols:
        parsefafsaseq(sys.argv[1], uniprols=uniprols)
    else:
        print("No UNIPRO IDs")
        sys.exit()
