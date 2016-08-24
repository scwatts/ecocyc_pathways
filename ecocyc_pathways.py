#!/usr/bin/env python3


# We're going to have to do this in two parts:
#   1. Convert gene names to accessions
#   2. Make HTTP requests to API to grab common-name for transcript units


import argparse
import os
import re
import xml.etree.ElementTree as et


import requests



# Constants
GENE_SEARCH_URL = 'http://websvc.biocyc.org/xmlquery?[g:g<-ecoli^^all-genes,g^common-name="%s"]'
TS_UNIT_URL = 'http://ecocyc.org/apixml?fn=transcription-units-of-gene&id=%s'

# Parsing XML with regex ¯\_(ツ)_/¯
ACCESSION_XML_RE = re.compile(r'^\s+?<Gene ID=\'(.+?)\'.+$')


def get_arguments():
    # Set arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--genes', required=True, help=('File containing'
        ' genes names'))

    # Check arguments
    args = parser.parse_args()
    if not os.path.exists(args.genes):
        parser.error('Input genes file %s does not exist' % args.genes)

    return args


def main():
    # Get and parse command line arguments
    args = get_arguments()

    # Read in gene names
    with open(args.genes) as f:
        genes = [l.rstrip() for l in f]

    # For each gene, get the accession from EcoCyc
    for gene in genes:
        # Get EcoCyc accession for gene
        gene_search_response = requests.get(GENE_SEARCH_URL % gene)
        gene_search_xml = gene_search_response.text
        for line in gene_search_xml.split('\n'):
            if '<Gene ID=' in line:
                gene_accession_line = line
        gene_accession = ACCESSION_XML_RE.match(gene_accession_line).group(1)

        # Get transcript gene unit for gene and print out
        ts_unit_response = requests.get(TS_UNIT_URL % gene_accession)
        ts_unit_xml = et.fromstring(ts_unit_response.text)
        for ts in ts_unit_xml.findall('Transcription-Unit'):
            print(gene, ts.find('common-name').text, sep='\t', flush=True)


if __name__ == '__main__':
    main()
