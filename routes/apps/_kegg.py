from myapp import app
from myapp.routes.apps._utils import make_table
from io import StringIO
from datetime import datetime
from io import BytesIO
import pandas as pd
import os
import Bio
from Bio.KEGG.REST import *
from Bio.KEGG.KGML import KGML_parser
from Bio.Graphics.KGML_vis import KGMLCanvas


PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

path_to_files="/flaski_private/kegg/"

def read_compound_pathway(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _read_compound_pathway(path_to_files=path_to_files):
        df=pd.read_csv(f"{path_to_files}/compound_pathway.tsv", sep="\t", names=['compound_id', 'compound_name', 'pathways'])
        return df.to_json()
    return pd.read_json(StringIO(_read_compound_pathway()))

def read_pathway_organism(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _read_pathway_organism(path_to_files=path_to_files):
        df=pd.read_csv(f"{path_to_files}/pathway_organisms.tsv", sep="\t", names=['pathway_id', 'pathway_name', 'organisms'])
        return df.to_json()
    return pd.read_json(StringIO(_read_pathway_organism()))

def compound_options(cache):
    compound_pathway_data=read_compound_pathway(cache)
    return [{'label': f"{cid}: {cname}", 'value': cid} for cid, cname in zip(compound_pathway_data['compound_id'], compound_pathway_data['compound_name'])]

def pathway_options(cache, compound_list):
    compound_pathway_data=read_compound_pathway(cache)
    pathway_organism_data=read_pathway_organism(cache)

    cp_row=compound_pathway_data[compound_pathway_data['compound_id'].isin(compound_list)]
    pathways_values = cp_row['pathways'].tolist()
    if not pathways_values or pathways_values==[None]:
        return None
    pathways_list = list(set([path.strip() for sublist in pathways_values for path in sublist.split(',')]))
    pw_rows = pathway_organism_data[pathway_organism_data['pathway_id'].isin(pathways_list)]
    
    return [{'label': f"{pid}: {pname}", 'value': pid} for pid, pname in zip(pw_rows['pathway_id'], pw_rows['pathway_name'])]

def organism_options(cache, pathway_id):
    pod=read_pathway_organism(cache)
    org_value=pod.loc[pod['pathway_id'] == pathway_id, 'organisms'].values[0] if not pod.loc[pod['pathway_id'] == pathway_id, 'organisms'].empty else None
    if org_value is None:
        return None

    return [{'label': org, 'value': org} for org in org_value.split(',')]

def additional_compound_options(cache, pathway_id, organism_id):
    compound_pathway_data=read_compound_pathway(cache)
    try:
        pathname = pathway_id.replace("map", organism_id)    
        pathway=KGML_parser.read(kegg_get(pathname, "kgml"))
        compound_list=[]
        for compound in pathway.compounds :
            c=compound.name.split(":")[-1]
            compound_list.append(c)

        # return [{'label': id, 'value': id} for id in compound_list] if compound_list else []
        return [{'label': f"{id}: {compound_pathway_data.loc[compound_pathway_data['compound_id'] == id, 'compound_name'].values[0]}" 
            if not compound_pathway_data.loc[compound_pathway_data['compound_id'] == id, 'compound_name'].empty else id, 'value': id} for id in compound_list] if compound_list else []
    except:
        return []

def kegg_operations(cache, selected_compound, pathway_id, organism_id, additional_compound):
    compound_pathway_data=read_compound_pathway(cache)
    overview=None
    compound_list=[]
    compound_dfl=[]
    gene_list=[]
    
    try:
        pathname = pathway_id.replace("map", organism_id)    
        pathway=KGML_parser.read(kegg_get(pathname, "kgml"))
        buffer = BytesIO()
        canvas = KGMLCanvas(pathway, import_imagemap=True)

        overview=str(pathway)

        for compound in pathway.compounds :
            c=compound.name.split(":")[-1]
            compound_list.append(c)
            if additional_compound:
                if c in additional_compound:
                    compound.graphics[0].bgcolor="#00FFFF"
            if c in selected_compound:
                compound.graphics[0].bgcolor="#FF0000"
        
        canvas.draw(buffer)
        buffer.seek(0)

        for compound_id in compound_list:
            if not compound_pathway_data.loc[compound_pathway_data['compound_id']==compound_id, 'compound_name'].empty:
                compound_name=compound_pathway_data.loc[compound_pathway_data['compound_id']==compound_id, 'compound_name'].values[0]
            else:
                compound_name="NA"
            compound_dfl.append({'compound_id': compound_id, 'compound_name': compound_name})

        compound_df=pd.DataFrame(compound_dfl)
        compound_table=make_table(compound_df,"compound_df")

        try:
            for gene in pathway.genes:
                if gene.name:
                    gene_list.append(gene.name)
        except:
            pass
        gene_df=pd.DataFrame(gene_list, columns=['gene_list'])
        gene_table=make_table(gene_df,"gene_df")

        return buffer, overview, compound_table, gene_table
    except Exception as e:
        return None, None, None, None


####### Generate/organize kegg data for faster use #######
### Generate pathway_organisms.tsv with pathway_id, pathway_name, available_organisms

# from Bio.KEGG import REST
# import csv

# # Fetch all pathways
# pathway_list = REST.kegg_list('pathway').read()

# # Write pathways to a TSV file without a header
# with open('pathway_organisms.tsv', 'w', newline='') as outfile:
#     tsv_writer = csv.writer(outfile, delimiter='\t')
#     for line in pathway_list.splitlines():
#         pathway_id, pathway_name = line.split('\t')
#         tsv_writer.writerow([pathway_id, pathway_name])

# # Fetch the list of all available organisms
# organism_list = REST.kegg_list('organism').read()

# # Extract the organism codes (e.g., 'hsa', 'ptr', 'pps', etc.)
# organism_codes = [line.split('\t')[1] for line in organism_list.splitlines()]


# # Function to get pathways for a given organism
# def get_pathways_from_org(organism_code):
#     pathway_list = REST.kegg_list('pathway', organism_code).read()
#     return [line.split('\t')[0][3:] for line in pathway_list.splitlines()]

# # Read TSV file, check pathways, and append organism code
# def update_tsv_with_organism(tsv_file, organism_code):
#     # Get the list of pathways for the organism
#     organism_pathways = get_pathways_from_org(organism_code)
    
#     # Read the contents of the TSV file into memory
#     updated_rows = []
#     with open(tsv_file, 'r') as infile:
#         tsv_reader = csv.reader(infile, delimiter='\t')
        
#         # Process each line of the TSV
#         for row in tsv_reader:
#             # Extract the pathway ID (e.g., 'map01100')
#             pathway_id = row[0][3:]  # Remove 'map' to get the numeric part

#             # Check if this pathway exists in the organism's pathways
#             if pathway_id in organism_pathways:
#                 # Append the organism code to the row
#                 if len(row) < 3:
#                     row.append(organism_code)
#                 else:
#                     row[2] += f",{organism_code}"  # If third column exists, append to it

#             # Add the updated row to the list
#             updated_rows.append(row)

#     # Overwrite the original file with the updated data
#     with open(tsv_file, 'w', newline='') as outfile:
#         tsv_writer = csv.writer(outfile, delimiter='\t')
#         tsv_writer.writerows(updated_rows)

# # Update pathway_organisms.tsv file with organisms
# tsv_file = 'pathway_organisms.tsv'
# for org in organism_codes:
#     update_tsv_with_organism(tsv_file, org)

### Generate compound_pathways.tsv with compound_id, compound_name, available_pathways

# # Function to get pathways associated with a given compound using KEGG REST API
# def get_pathways_for_compound(compound_id):
#     # Fetch pathways linked to the compound using the KEGG REST API
#     link_url = f"https://rest.kegg.jp/link/pathway/{compound_id}"
#     response = requests.get(link_url)
    
#     # Check if the response is empty (i.e., no linked pathways found)
#     if response.status_code != 200 or not response.text.strip():
#         return None
    
#     # Parse the linked pathways and extract pathway IDs (e.g., map00190)
#     pathway_ids = [line.split("\t")[1].split(":")[1] for line in response.text.strip().splitlines()]
    
#     # Return the comma-separated list of pathway IDs (e.g., map00190, map00195, etc.)
#     return ",".join(pathway_ids)

# # Function to append pathway list to the compounds and save the result to a TSV file
# def append_pathways_to_compounds(output_file):
#     # Fetch the list of all compounds from KEGG
#     request = REST.kegg_list("compound")
#     compound_data = request.read()
    
#     # Get the compound lines
#     compound_lines = compound_data.splitlines()[18800:]
    
#     # Process each compound and append data to the file one by one
#     for index, line in enumerate(compound_lines):
#         compound_id, compound_name = line.split("\t")
        
#         # Get the associated pathways for this compound
#         pathways = get_pathways_for_compound(compound_id)
#         if not pathways:
#             pathways = "NA"
        
#         mode = "w" if index == 0 else "a"
        
#         # Open the output file in the appropriate mode
#         with open(output_file, mode) as f:
#             # Write the compound ID, compound name, and pathway list to the file
#             f.write(f"{compound_id}\t{compound_name}\t{pathways}\n")

# # Generate the TSV file and append data one by one
# output_file = "compound_pathways.tsv"
# append_pathways_to_compounds(output_file)

# print(f"TSV file '{output_file}' generated successfully.")
