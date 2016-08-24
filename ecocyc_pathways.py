#!/usr/bin/env python3


# We're going to have to do this in two parts:
#   1. Convert gene names to accessions via API search
#   2. Make HTTP requests to API to grab common-name for transcript units


import argparse
import os
import xml.etree.ElementTree as et


import requests


# Constants
GENE_SEARCH_URL = 'http://websvc.biocyc.org/xmlquery?[g:g<-ecoli^^all-genes,g^common-name="%s"]'
TS_UNIT_URL = 'http://ecocyc.org/apixml?fn=transcription-units-of-gene&id=%s'
PROMOTER_URL = 'http://websvc.biocyc.org/getxml?%s'


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

    # For each gene, do the thing
    for gene in genes:
        ####
        # Part 1: Get accession for gene
        ####
        # Make request for query (extact match for gene name, case sensitive)
        gene_search_response = requests.get(GENE_SEARCH_URL % gene)

        # Convert parse XML structure and grab the Gene tag
        gene_search_xml = et.fromstring(gene_search_response.text)
        gene_tag = gene_search_xml.find('Gene')
        gene_accession = gene_tag.get('ID')


        ####
        # Part 2: Get the promoter name and transcript gene unit
        ####
        # Make initial request for transcript unit and parse XML
        ts_unit_response = requests.get(TS_UNIT_URL % gene_accession)
        ts_unit_xml = et.fromstring(ts_unit_response.text)

        # Extract desired parts from XML
        for ts in ts_unit_xml.findall('Transcription-Unit'):
            # First get the promoter name
            promoter_xml = ts.find('component/Promoter')

            # In some cases the API returns XML data that does not contain the
            # common name for the promoter. In these such cases, we can grab
            # the EcoCyc accession and make another request for the specific
            # promoter and grab the common name from there
            try:
                # Promoter common-name exists in XML
                promoter_name = promoter_xml.find('common-name').text
            except AttributeError:
                # No promoter common-name, finding accession to make request
                promoter_id = promoter_xml.get('resource').replace('#', '')

                # Making request and parse XML
                promoter_page_reponse = requests.get(PROMOTER_URL % promoter_id)
                promoter_page_xml = et.fromstring(promoter_page_reponse.text)

                # Extract promoter common-name
                promoter_name = promoter_page_xml.find('Promoter/common-name').text

            # Lastly, grab the genes in the transcript unit and then print
            unit_genes = ts.find('common-name').text
            print(gene, promoter_name, unit_genes, sep='\t', flush=True)


if __name__ == '__main__':
    main()
