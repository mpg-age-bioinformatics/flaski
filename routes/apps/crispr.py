from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session
from pyflaski.scatterplot import make_figure, figure_defaults
from myapp.routes.apps._utils import check_access, make_options, GROUPS, GROUPS_INITALS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import traceback
import json
import pandas as pd
import time
import base64
import plotly.express as px
# from plotly.io import write_image
import plotly.graph_objects as go
from werkzeug.utils import secure_filename
from myapp import db
from myapp.models import UserLogging
from time import sleep
import zipfile

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("crispr",url_base_pathname=f'{PAGE_PREFIX}/crispr/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="CRISPR", assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

if app.config["SESSION_TYPE"] == "sqlalchemy":
    import sqlalchemy
    engine = sqlalchemy.create_engine(app.config["SQLALCHEMY_DATABASE_URI"] , echo=True)
    app.config["SESSION_SQLALCHEMY"] = engine
elif app.config["CACHE_TYPE"] == "RedisCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
    })
elif app.config["CACHE_TYPE"] == "RedisSentinelCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisSentinelCache',
        'CACHE_REDIS_SENTINELS': [ 
            [ os.environ.get('CACHE_REDIS_SENTINELS_address'), os.environ.get('CACHE_REDIS_SENTINELS_port') ]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER')
    })

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=True ),
        html.Div( id="protected-content" ),
    ] 
)

card_label_style={"margin-right":"2px"}
card_label_style_={"margin-left":"5px","margin-right":"2px"}

card_input_style={"height":"35px","width":"100%"}
# card_input_style_={"height":"35px","width":"100%","margin-right":"10px"}
card_body_style={ "padding":"2px", "padding-top":"2px"}#,"margin":"0px"}
# card_body_style={ "padding":"2px", "padding-top":"4px","padding-left":"18px"}




@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    header_access, msg_access = check_access( 'crispr' )
    if header_access :
        return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    # if "crispr" in PRIVATE_ROUTES :
    #     appdb=PrivateRoutes.query.filter_by(route="crispr").first()
    #     if not appdb:
    #         return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    #     allowed_users=appdb.users
    #     if not allowed_users:
    #         return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    #     if current_user.id not in allowed_users :
    #         allowed_domains=appdb.users_domains
    #         if current_user.domain not in allowed_domains:
    #             return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    eventlog = UserLogging(email=current_user.email, action="visit crispr")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("CRISPR",current_user),
            html.Div(id="app-content"),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

style_cell={
        'height': '100%',
        # all three widths are needed
        'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }

def make_ed_table(field_id, columns=None , df=None):
    if  type(df) != type( pd.DataFrame() ):
        df=pd.DataFrame( columns=columns )
        if columns:
            df=df[columns]
    df=make_table(df,field_id)
    df.editable=True
    df.row_deletable=True
    df.style_cell=style_cell
    df.style_table["height"]="62vh"
    return df

def make_df_from_rows(rows):
    rows_=[]
    for row in rows:
        row=[ row[k] for k in list(row.keys()) ]
        rows_.append(row)
    df=pd.DataFrame(rows_,columns=list(rows[0].keys()))
    # df=pd.DataFrame(rows)
    # for row in rows:
    #     # print("!!!", row)
    #     df_=pd.DataFrame(row,index=[0])
    #     df=pd.concat([df,df_])
    df.reset_index(inplace=True, drop=True)
    df=df.to_json()
    return df

# Read in users input and generate submission file.
def generate_submission_file(samplenames, \
    samples, \
    library, \
    email, \
    group,\
    experiment_name,\
    folder,\
    md5sums,\
    cnv_file,\
    cnv_line,\
    upstreamseq,\
    sgRNA_size,\
    efficiency_matrix,\
    SSC_sgRNA_size,\
    gmt_file,\
    mageck_test_remove_zero,\
    mageck_test_remove_zero_threshold,\
    skip_mle,\
    species,\
    assembly,\
    use_bowtie,\
    depmap,\
    depmap_cell_line,\
    BAGEL_ESSENTIAL,\
    BAGEL_NONESSENTIAL,\
    mageckflute_organism,\
    nontargeting_tag,\
    magecku_fdr, \
    magecku_threshold_control_groups,\
    magecku_threshold_treatment_groups, \
    use_neg_ctrl, \
    using_master_library,\
    acer_master_library,\
    facs,\
    ctrl_guides,\
    mle_matrices,\
    ONLY_COUNT, \
    cleanR_control_reps ):
    @cache.memoize(60*60*2) # 2 hours
    def _generate_submission_file(samplenames,\
        samples,\
        library,\
        email,\
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        cnv_file,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        skip_mle,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism,\
        nontargeting_tag,\
        magecku_fdr,\
        magecku_threshold_control_groups,\
        magecku_threshold_treatment_groups,\
        use_neg_ctrl,\
        using_master_library,\
        acer_master_library,\
        facs,\
        ctrl_guides,\
        mle_matrices,\
        ONLY_COUNT, \
        cleanR_control_reps):
        samplenames_df=make_df_from_rows(samplenames)
        samples_df=make_df_from_rows(samples)
        library_df=make_df_from_rows(library)

        df_=pd.DataFrame({
            "Field":[
                "email", \
                "group",\
                "Group",
                "experiment_name",\
                "Project title",\
                "folder",\
                "Folder",\
                "md5sums",\
                "cnv_file",\
                "cnv_line",\
                "upstreamseq",\
                "sgRNA_size",\
                "efficiency_matrix",\
                "SSC_sgRNA_size",\
                "gmt_file",\
                "mageck_test_remove_zero",\
                "mageck_test_remove_zero_threshold",\
                "skip_mle",\
                "species",\
                "assembly",\
                "use_bowtie",\
                "depmap",\
                "depmap_cell_line",\
                "BAGEL_ESSENTIAL",\
                "BAGEL_NONESSENTIAL",\
                "mageckflute_organism",\
                "nontargeting_tag",\
                "magecku_fdr", \
                "magecku_threshold_control_groups",\
                "magecku_threshold_treatment_groups", \
                "use_neg_ctrl", \
                "using_master_library",\
                "acer_master_library",\
                "facs",\
                "ctrl_guides",\
                "mle_matrices",\
                "ONLY_COUNT",\
                "cleanR_control_reps"
                ],\
            "Value":[
                email, \
                group,\
                group,\
                experiment_name,\
                experiment_name,\
                folder,\
                folder,\
                md5sums,\
                cnv_file,\
                cnv_line,\
                upstreamseq,\
                sgRNA_size,\
                efficiency_matrix,\
                SSC_sgRNA_size,\
                gmt_file,\
                mageck_test_remove_zero,\
                mageck_test_remove_zero_threshold,\
                skip_mle,\
                species,\
                assembly,\
                use_bowtie,\
                depmap,\
                depmap_cell_line,\
                BAGEL_ESSENTIAL,\
                BAGEL_NONESSENTIAL,\
                mageckflute_organism,\
                nontargeting_tag,\
                magecku_fdr, \
                magecku_threshold_control_groups,\
                magecku_threshold_treatment_groups, \
                use_neg_ctrl, \
                using_master_library,\
                acer_master_library,\
                facs,\
                ctrl_guides,\
                mle_matrices,\
                ONLY_COUNT,\
                cleanR_control_reps
                ]
             }, index=list(range(38)))
        
        df_=df_.to_json()
     
        filename=make_submission_file(".crispr.xlsx")

        filename=os.path.basename(filename)

        json_filename=filename.replace(".xlsx",".json")

        paths={ "raven":{
            "code":"/nexus/posix0/MAGE-flaski/service/projects/code/",
            "raw_data":"/nexus/posix0/MAGE-flaski/ftp_data/",
            "run_data":"/raven/ptmp/flaski/projects/"
            },
            "studio":{
                "code":"/nexus/posix0/MAGE-flaski/service/projects/code/",
                "raw_data":"/nexus/posix0/MAGE-flaski/ftp_data/",
                "run_data":"/nexus/posix0/MAGE-flaski/service/projects/data/"
            },
            "local":{
                "code":"none",
                "raw_data":"<path_to_raw_data>",
                "run_data":"<path_to_run_data>",
            }
        }

        if group != "External" :
            if group in GROUPS :
                project_folder=group+"/"+GROUPS_INITALS[group]+"_at_"+secure_filename(experiment_name)
            else:
                user_domain=[ s.replace(" ","") for s in email.split(",") if "mpg.de" in s ]
                user_domain=user_domain[0].split("@")[-1]
                mps_domain="mpg.de"
                tag=user_domain.split(".mpg.de")[0]

                project_folder=group+"/"+tag+"_at_"+secure_filename(experiment_name)
        else:
            project_folder="Bioinformatics/bit_ext_at_"+secure_filename(experiment_name)

        nf={}

        for location in  [ s for s in list(paths.keys()) if s != "local"] + ["local"] :

            if location == "local":
                project_folder=""

            code=paths[location]["code"]
            raw_data=paths[location]["raw_data"]
            run_data=paths[location]["run_data"]

            nf_={ 
                "email":email,
                "group":group,
                "project_title":experiment_name,
                "image_folder":"/nexus/posix0/MAGE-flaski/service/images/" ,
                "project_folder" : os.path.join(run_data,project_folder),
                "reference_file": os.path.join(code,project_folder, "scripts.flaski", filename),
                "raw_fastq": os.path.join(raw_data),
                "renamed_fastq": os.path.join(run_data,project_folder,"raw_renamed"),
                "fastqc_raw_data" : os.path.join(run_data,project_folder,"raw_renamed"),
                "cutadapt_raw_data" : os.path.join(run_data,project_folder,"raw_renamed"),
                "sgRNA_size" : sgRNA_size,
                "SSC_sgRNA_size" : SSC_sgRNA_size,
                "upstreamseq" : upstreamseq,
                "library" : os.path.join(run_data,project_folder,"library.csv"),
                "input_count" : os.path.join(run_data,project_folder,"cutadapt_output"), 
                "output_count" : "mageck_output/count",
                "mageck_counts_type":"mageck",
                "samples_tsv": os.path.join(run_data,project_folder,"samples.tsv"),
                "output_test":"mageck_output/test",
                "mageck_test_remove_zero": mageck_test_remove_zero,
                "mageck_test_remove_zero_threshold": mageck_test_remove_zero_threshold , 
                "cnv_file": cnv_file,
                "cnv_line": cnv_line,
                "output_mle": "mageck_output/mle",
                "efficiency_matrix": f"/SSC0.1/matrix/{efficiency_matrix}",
                "mle_matrices": os.path.join(raw_data),
                "library_xlsx": os.path.join(run_data, project_folder,"library.xlsx"),
                "gmt_file":gmt_file,
                "output_pathway":"mageck_output/pathway",
                "output_plot":"mageck_output/plot",
                "output_vispr":"mageck_output/vispr",
                "vispr_fastqc": os.path.join(run_data,project_folder,"fastqc_output"),
                "vispr_species":species,
                "vispr_assembly":assembly,
                "output_flute":"mageck_output/flute",
                "mageckflute_organism":mageckflute_organism,
                "depmap":depmap,
                "depmap_cell_line":depmap_cell_line,
                "output_mageck_count" : os.path.join(run_data,project_folder,"mageck_output/count"),
                "output_magecku":"mageck_output/magecku",
                "magecku_fdr":magecku_fdr,
                "nontargeting_tag": nontargeting_tag ,
                "magecku_threshold_control_groups":magecku_threshold_control_groups,
                "magecku_threshold_treatment_groups":magecku_threshold_treatment_groups,
                "output_bagel": os.path.join(run_data,project_folder,"bagel_output"),
                "bagel_essential":BAGEL_ESSENTIAL,
                "bagel_nonessential":BAGEL_NONESSENTIAL,
                "output_drugz": os.path.join(run_data,project_folder,"drugz_output"), 
                "output_acer":os.path.join(run_data,project_folder,"acer_output"), 
                "use_neg_ctrl":use_neg_ctrl,
                "using_master_library":using_master_library,
                "acer_master_library":acer_master_library,
                "md5sums":md5sums,\
                "output_maude":os.path.join(run_data,project_folder,"maude_output"),
                "facs":facs,
                "ctrl_guides":ctrl_guides,
                "mle_matrices":mle_matrices,
                "skip_mle":skip_mle,
                "cleanR_input_mageck": os.path.join(run_data,project_folder,"mageck_output/count/counts.count.txt"),
                "cleanR_output" : os.path.join(run_data,project_folder,"cleanR_output"),
                "cleanR_lib_file" : os.path.join(run_data, project_folder,"library_cleanR.tsv"),
                "cleanR_control_reps" : int(cleanR_control_reps)
            }

            # if use_neg_ctrl == "F" :
            if not use_neg_ctrl:
                del(nf_["use_neg_ctrl"])
                del(nf_["using_master_library"])
                del(nf_["acer_master_library"])
                # del(nf_["output_acer"])

            if not nontargeting_tag:
                del(nf_["magecku_fdr"])
                del(nf_["nontargeting_tag"])
                del(nf_["magecku_threshold_control_groups"])
                del(nf_["magecku_threshold_treatment_groups"])
                del(nf_["output_magecku"])

            # if not facs :
            #     # del(nf_["output_maude"])
            #     del(nf_["facs"])
            #     del(nf_["ctrl_guides"])

            if skip_mle == "True" :
                del(nf_["output_mle"])
            
            if not gmt_file:
                del(nf_["gmt_file"])
            
            if not mle_matrices:
                del(nf_["mle_matrices"])
            
            if not efficiency_matrix:
                del(nf_["efficiency_matrix"])
            
            if depmap == 'False':
                del(nf_["depmap"])
                del(nf_["depmap_cell_line"])

            # if not depmap_cell_line :
            #     del(nf_["depmap_cell_line"])

            if not magecku_fdr:
                del(nf_["nontargeting_tag"])
                del(nf_["output_magecku"])
                del(nf_["magecku_fdr"])
                del(nf_["magecku_threshold_control_groups"])
                del(nf_["magecku_threshold_treatment_groups"])

            nf[location]=nf_
        
        nf=json.dumps(nf)

        json_config={filename:{"sampleNames":samplenames_df, "samples":samples_df, "library":library_df, "crispr":df_ }, json_filename:nf }

        return { "filename": filename, "json_filename":json_filename, "json":json_config }
        # return {"filename": filename, "sampleNames":samplenames_df, "samples":samples_df, "library":library_df, "crispr":df_}
    return _generate_submission_file(
        samplenames, \
        samples, \
        library, \
        email, \
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        cnv_file,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        skip_mle,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism ,\
        nontargeting_tag ,\
        magecku_fdr, \
        magecku_threshold_control_groups,\
        magecku_threshold_treatment_groups, \
        use_neg_ctrl, \
        using_master_library,\
        acer_master_library,\
        facs,\
        ctrl_guides,\
        mle_matrices,\
        ONLY_COUNT,\
        cleanR_control_reps
    )

@dashapp.callback( 
    Output('app-content', 'children'),
    Input('url', 'pathname'))
def make_app_content(pathname):

    CELL_LINES=['LOUNH91_LUNG', 'T98G_CENTRAL_NERVOUS_SYSTEM', 'IPC298_SKIN', 'RPMI8226_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'MIAPACA2_PANCREAS', 'HS695T_SKIN', 'COLO704_OVARY', 'SKMEL28_SKIN', 'K562_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'LK2_LUNG',\
        'NCIH2122_LUNG', 'SW620_LARGE_INTESTINE', 'NAMALWA_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KMS12BM_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'G361_SKIN', 'MCAS_OVARY', '22RV1_PROSTATE', 'FUOV1_OVARY', 'RS411_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'OVTOKO_OVARY', \
        'CPCN_LUNG', 'OV90_OVARY', 'NCIH2171_LUNG', 'MOLT4_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'COLO829_SKIN', 'SW579_THYROID',\
        'RL_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'DMS79_LUNG', 'PANC0403_PANCREAS', 'NCIH889_LUNG', 'DLD1_LARGE_INTESTINE', \
        'HL60_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HEYA8_OVARY', 'TCCSUP_URINARY_TRACT', 'HMCB_SKIN', 'PANC1005_PANCREAS', \
        'KARPAS299_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RERFLCAI_LUNG', 'NCIH524_LUNG', 'SW1463_LARGE_INTESTINE', 'TYKNU_OVARY', \
        'EFM19_BREAST', 'T84_LARGE_INTESTINE', 'SKMEL2_SKIN', 'SKMEL5_SKIN', 'DU145_PROSTATE', 'EFO21_OVARY', 'SKMEL30_SKIN', \
        'LN18_CENTRAL_NERVOUS_SYSTEM', 'MDAMB468_BREAST', 'MM1S_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SBC5_LUNG', 'RMGI_OVARY', \
        'CHL1_SKIN', 'U118MG_CENTRAL_NERVOUS_SYSTEM', 'A253_SALIVARY_GLAND', 'BXPC3_PANCREAS', 'TCCPAN2_PANCREAS', 'CAKI2_KIDNEY', \
        'EFO27_OVARY', 'NCIH2030_LUNG', 'ASPC1_PANCREAS', 'MFE296_ENDOMETRIUM', 'MFE280_ENDOMETRIUM', 'MV411_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'U87MG_CENTRAL_NERVOUS_SYSTEM', 'MDAMB231_BREAST', 'OVSAHO_OVARY', 'NCIH520_LUNG', 'MFE319_ENDOMETRIUM', 'NUGC3_STOMACH', 'NCIH446_LUNG', \
        'RT112_URINARY_TRACT', 'MELHO_SKIN', 'UACC257_SKIN', 'EFM192A_BREAST', 'SW900_LUNG', 'MELJUSO_SKIN', 'A2058_SKIN', 'A2780_OVARY', \
        'OVCAR4_OVARY', 'L33_PANCREAS', 'HS944T_SKIN', 'VMRCRCZ_KIDNEY', 'DBTRG05MG_CENTRAL_NERVOUS_SYSTEM', 'HCT116_LARGE_INTESTINE', 'HS766T_PANCREAS', \
        'SKMEL24_SKIN', 'CAOV3_OVARY', 'PANC0203_PANCREAS', 'DOV13_OVARY', 'HT29_LARGE_INTESTINE', 'AZ521_STOMACH', 'C32_SKIN', 'CAL851_BREAST', \
        'NCIH1975_LUNG', 'A549_LUNG', 'SCABER_URINARY_TRACT', 'BT549_BREAST', 'HCT15_LARGE_INTESTINE', 'K029AX_SKIN', 'TOV112D_OVARY', 'HS571T_OVARY', \
        'NCIH196_LUNG', 'PC3_PROSTATE', 'PANC0327_PANCREAS', 'CAPAN2_PANCREAS', 'IGROV1_OVARY', 'HEPG2_LIVER', 'OVCAR8_OVARY', 'EVSAT_BREAST', 'FU97_STOMACH', \
        'TOV21G_OVARY', 'KMRC1_KIDNEY', 'NUGC2_STOMACH', 'RMUGS_OVARY', 'HT1197_URINARY_TRACT', 'KM12_LARGE_INTESTINE', 'SF295_CENTRAL_NERVOUS_SYSTEM', \
        'WM115_SKIN', 'NCIH2228_LUNG', 'NCIH209_LUNG', 'OE33_OESOPHAGUS', 'OE19_OESOPHAGUS', 'COLO800_SKIN', 'CCK81_LARGE_INTESTINE', 'MDAMB453_BREAST', \
        'JHH1_LIVER', 'JHH4_LIVER', 'HT1376_URINARY_TRACT', 'NCIH1963_LUNG', 'HLF_LIVER', 'IGR37_SKIN', 'KMRC2_KIDNEY', 'OE21_OESOPHAGUS', 'IM95_STOMACH', \
        'COLO849_SKIN', '786O_KIDNEY', 'SKHEP1_LIVER', 'SJSA1_BONE', 'JHH2_LIVER', 'KP2_PANCREAS', 'JHH5_LIVER', 'COLO679_SKIN', 'VCAP_PROSTATE', \
        'SUIT2_PANCREAS', 'NCIH2444_LUNG', 'CALU1_LUNG', 'RL952_ENDOMETRIUM', 'SQ1_LUNG', 'HCC366_LUNG', 'NCIH2170_LUNG', 'NCIH647_LUNG', \
        'M059K_CENTRAL_NERVOUS_SYSTEM', 'J82_URINARY_TRACT', 'UACC62_SKIN', 'SKLU1_LUNG', 'ISHIKAWAHERAKLIO02ER_ENDOMETRIUM', 'TE15_OESOPHAGUS', \
        'A204_SOFT_TISSUE', 'SEM_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'PATU8902_PANCREAS', 'QGP1_PANCREAS', 'YAPC_PANCREAS', 'KLE_ENDOMETRIUM', \
        'EN_ENDOMETRIUM', 'HEC1A_ENDOMETRIUM', 'NCIH211_LUNG', 'SKMEL3_SKIN', 'PSN1_PANCREAS', 'COLO741_SKIN', 'ACHN_KIDNEY', 'NCIH650_LUNG', \
        'NCIH441_LUNG', 'KYSE510_OESOPHAGUS', 'JHUEM7_ENDOMETRIUM', 'ESS1_ENDOMETRIUM', 'BT474_BREAST', 'KELLY_AUTONOMIC_GANGLIA', \
        'LNCAPCLONEFGC_PROSTATE', 'LS411N_LARGE_INTESTINE', 'TE1_OESOPHAGUS', 'KYSE150_OESOPHAGUS', 'PATU8988T_PANCREAS', 'KYSE450_OESOPHAGUS', \
        'RERFLCAD1_LUNG', 'HCC78_LUNG', 'KYSE70_OESOPHAGUS', 'VMRCLCD_LUNG', 'MOGGCCM_CENTRAL_NERVOUS_SYSTEM', 'GAMG_CENTRAL_NERVOUS_SYSTEM', \
        'COLO818_SKIN', 'KASUMI1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'LOVO_LARGE_INTESTINE', 'LC1SQSF_LUNG', 'KYSE410_OESOPHAGUS', 'COLO783_SKIN', \
        'GOS3_CENTRAL_NERVOUS_SYSTEM', 'EFE184_ENDOMETRIUM', 'RERFLCMS_LUNG', 'MOGGUVW_CENTRAL_NERVOUS_SYSTEM', 'KYSE30_OESOPHAGUS', 'AGS_STOMACH', \
        'HDMYZ_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', '42MGBA_CENTRAL_NERVOUS_SYSTEM', 'SUPM2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KCIMOH1_PANCREAS', \
        'KS1_CENTRAL_NERVOUS_SYSTEM', '1321N1_CENTRAL_NERVOUS_SYSTEM', 'GMS10_CENTRAL_NERVOUS_SYSTEM', '8MGBA_CENTRAL_NERVOUS_SYSTEM', 'GI1_CENTRAL_NERVOUS_SYSTEM', \
        'HCC44_LUNG', 'KYSE140_OESOPHAGUS', 'KYSE180_OESOPHAGUS', 'SNB19_CENTRAL_NERVOUS_SYSTEM', 'MOLM13_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'YKG1_CENTRAL_NERVOUS_SYSTEM', 'TE11_OESOPHAGUS', 'NCIH2196_LUNG', 'MALME3M_SKIN', 'HUPT3_PANCREAS', 'DETROIT562_UPPER_AERODIGESTIVE_TRACT', \
        'JHUEM2_ENDOMETRIUM', 'TE5_OESOPHAGUS', 'A375_SKIN', 'NCIH526_LUNG', 'CALU6_LUNG', 'U251MG_CENTRAL_NERVOUS_SYSTEM', 'HCC15_LUNG', 'EPLC272H_LUNG',\
        'RPMI7951_SKIN', 'SKMES1_LUNG', 'LOXIMVI_SKIN', 'NCIH596_LUNG', 'L1236_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1299_LUNG', 'MORCPR_LUNG', \
        'PK59_PANCREAS', 'DANG_PANCREAS', 'NCIH838_LUNG', 'CORL23_LUNG', 'NCIH810_LUNG', 'CAL12T_LUNG', 'NCIH1155_LUNG', 'KNS62_LUNG', 'NCIH2172_LUNG',\
        'NCIH460_LUNG', 'NCIH522_LUNG', 'PC14_LUNG', 'SW1573_LUNG', 'NCIH1703_LUNG', 'HARA_LUNG', 'NCIH1581_LUNG', 'ABC1_LUNG', 'NCIH661_LUNG', \
        'HUPT4_PANCREAS', 'DKMG_CENTRAL_NERVOUS_SYSTEM', 'ES2_OVARY', 'VMRCLCP_LUNG', 'CFPAC1_PANCREAS', 'NCIH1781_LUNG', 'LS123_LARGE_INTESTINE', \
        'AU565_BREAST', 'SW403_LARGE_INTESTINE', 'NCIH1568_LUNG', 'MDAMB415_BREAST', 'NCIH358_LUNG', 'NCIH1563_LUNG', 'DAOY_CENTRAL_NERVOUS_SYSTEM', \
        'NCIH146_LUNG', 'CHP212_AUTONOMIC_GANGLIA', 'LS1034_LARGE_INTESTINE', 'SW1417_LARGE_INTESTINE', 'CA46_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'HPAC_PANCREAS', 'SW948_LARGE_INTESTINE', 'RT4_URINARY_TRACT', 'CAPAN1_PANCREAS', 'MC116_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'A673_BONE', \
        'A498_KIDNEY', 'G402_SOFT_TISSUE', 'NCIH747_LARGE_INTESTINE', 'BDCM_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1437_LUNG', 'SKCO1_LARGE_INTESTINE', \
        'LS180_LARGE_INTESTINE', 'SNU16_STOMACH', 'RDES_BONE', 'C3A_LIVER', 'NCIH82_LUNG', 'GCT_SOFT_TISSUE', 'NCIH1792_LUNG', 'HS578T_BREAST', \
        'PANC0213_PANCREAS', 'SJRH30_SOFT_TISSUE', 'CAL27_UPPER_AERODIGESTIVE_TRACT', 'BT20_BREAST', 'SW1271_LUNG', 'SKNMC_BONE', 'MDAMB436_BREAST', \
        'MDAMB361_BREAST', 'FADU_UPPER_AERODIGESTIVE_TRACT', 'HH_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'DB_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'SKBR3_BREAST', 'OVKATE_OVARY', 'OVISE_OVARY', 'OVMANA_OVARY', 'U2OS_BONE', 'NCIN87_STOMACH', 'HCC1395_BREAST', 'D283MED_CENTRAL_NERVOUS_SYSTEM',\
        'HCC1806_BREAST', 'NCIH1650_LUNG', 'G401_SOFT_TISSUE', 'NIHOVCAR3_OVARY', 'GDM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HCC1143_BREAST', 'NCIH1793_LUNG', \
        'DU4475_BREAST', 'H4_CENTRAL_NERVOUS_SYSTEM', 'HPAFII_PANCREAS', 'HGC27_STOMACH', 'EB2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SKNAS_AUTONOMIC_GANGLIA', \
        'JHUEM1_ENDOMETRIUM', 'KP4_PANCREAS', 'OV56_OVARY', 'HUG1N_STOMACH', 'BGC823_STOMACH', 'DAUDI_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'VMRCRCW_KIDNEY', \
        'HS604T_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'TE9_OESOPHAGUS', 'KMS26_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KE39_STOMACH', \
        'KE97_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'JHOS4_OVARY', 'GCIY_STOMACH', 'SCC15_UPPER_AERODIGESTIVE_TRACT', 'NMCG1_CENTRAL_NERVOUS_SYSTEM', \
        'CAS1_CENTRAL_NERVOUS_SYSTEM', 'KYSE270_OESOPHAGUS', 'NUGC4_STOMACH', 'KNS42_CENTRAL_NERVOUS_SYSTEM', 'SH10TC_STOMACH', 'COV504_OVARY', \
        'KYSE520_OESOPHAGUS', 'U266B1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SCC4_UPPER_AERODIGESTIVE_TRACT', 'COV318_OVARY', 'T3M4_PANCREAS', \
        'YH13_CENTRAL_NERVOUS_SYSTEM', 'PK1_PANCREAS', 'JHOS2_OVARY', 'KMS21BM_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'EB1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'MKN7_STOMACH', 'GA10_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SKNFI_AUTONOMIC_GANGLIA', 'CMK115_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KP3_PANCREAS', \
        'HEC265_ENDOMETRIUM', 'KMS28BM_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HCC70_BREAST', 'SKES1_BONE', 'HEC151_ENDOMETRIUM', 'JM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'HEC108_ENDOMETRIUM', 'NCIH508_LARGE_INTESTINE', 'HT_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HEL9217_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'KG1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'A3KAW_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KMS34_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'THP1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'MJ_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KPNSI9S_AUTONOMIC_GANGLIA', 'HCC38_BREAST', \
        'KO52_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KMS27_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'ZR751_BREAST', 'A4FUK_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'KNS60_CENTRAL_NERVOUS_SYSTEM', 'A172_CENTRAL_NERVOUS_SYSTEM', 'KURAMOCHI_OVARY', 'SW480_LARGE_INTESTINE', 'ALEXANDERCELLS_LIVER', 'WM2664_SKIN', \
        'HLE_LIVER', 'IGR39_SKIN', 'PATU8988S_PANCREAS', 'RERFLCSQ1_LUNG', 'NCIH1395_LUNG', 'HS606T_BREAST', 'SNU475_LIVER', 'SCC25_UPPER_AERODIGESTIVE_TRACT', \
        'T24_URINARY_TRACT', 'OCUM1_STOMACH', 'HCC1937_BREAST', 'SNU387_LIVER', 'CAOV4_OVARY', 'SNU398_LIVER', 'SNU423_LIVER', 'SNU449_LIVER', \
        'COLO205_LARGE_INTESTINE', 'HCC1187_BREAST', 'HCC202_BREAST', 'IMR32_AUTONOMIC_GANGLIA', 'C2BBE1_LARGE_INTESTINE', 'NCIH2052_PLEURA', 'NCIH1355_LUNG', \
        'MEG01_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SUPT1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'U937_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'REH_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HT144_SKIN', 'SKMEL1_SKIN', 'LOUCY_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS739T_BREAST', \
        'HS683_CENTRAL_NERVOUS_SYSTEM', 'CCFSTTG1_CENTRAL_NERVOUS_SYSTEM', 'DMS114_LUNG', 'SNUC1_LARGE_INTESTINE', 'MDAMB157_BREAST', 'MDAMB175VII_BREAST', \
        'NCIH2087_LUNG', 'SNUC2A_LARGE_INTESTINE', 'RPMI6666_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CAKI1_KIDNEY', 'ST486_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'MG63_BONE', 'SW1990_PANCREAS', 'PL45_PANCREAS', 'HT1080_SOFT_TISSUE', 'MSTO211H_PLEURA', 'TOLEDO_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'PANC0813_PANCREAS', \
        'PLCPRF5_LIVER', 'NCIH2029_LUNG', 'NCIH1734_LUNG', 'NCIH2106_LUNG', 'NCIH2347_LUNG', 'SW780_URINARY_TRACT', 'NCIH1666_LUNG', 'NCIH1651_LUNG', \
        'NCIH510_LUNG', 'RKO_LARGE_INTESTINE', 'NCIH2066_LUNG', 'HLFA_LUNG', 'SU8686_PANCREAS', 'BCP1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CALU3_LUNG',\
        'HS611T_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH2342_LUNG', 'PANC1_PANCREAS', 'NCIH2291_LUNG', 'SKNDZ_AUTONOMIC_GANGLIA', 'HS746T_STOMACH', \
        'SUPB15_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1341_LUNG', 'HUH1_LIVER', 'RAJI_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'IALM_LUNG', 'NCIH2227_LUNG', \
        'LUDLU1_LUNG', 'HCC1954_BREAST', 'HCC2218_BREAST', 'EBC1_LUNG', 'CAMA1_BREAST', 'NCIH322_LUNG', 'HMC18_BREAST', 'YMB1_BREAST', 'JHH7_LIVER', \
        'HUTU80_SMALL_INTESTINE', 'NCIH2452_PLEURA', 'LN229_CENTRAL_NERVOUS_SYSTEM', 'SNU1_STOMACH', 'SKLMS1_SOFT_TISSUE', 'HUCCT1_BILIARY_TRACT', 'NCIH1573_LUNG', \
        'MCF7_BREAST', 'SKUT1_SOFT_TISSUE', 'KPNYN_AUTONOMIC_GANGLIA', 'MKN1_STOMACH', 'SKMEL31_SKIN', 'KALS1_CENTRAL_NERVOUS_SYSTEM', 'LU99_LUNG', 'MKN74_STOMACH', \
        'KPNRTBM1_AUTONOMIC_GANGLIA', 'SNU5_STOMACH', 'KNS81_CENTRAL_NERVOUS_SYSTEM', 'AM38_CENTRAL_NERVOUS_SYSTEM', 'NH6_AUTONOMIC_GANGLIA', \
        'HS840T_UPPER_AERODIGESTIVE_TRACT', 'GB1_CENTRAL_NERVOUS_SYSTEM', 'HEC6_ENDOMETRIUM', 'BECKER_CENTRAL_NERVOUS_SYSTEM', 'T47D_BREAST', \
        'NCIH69_LUNG', 'NCO2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KMS11_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS839T_SKIN', 'HS618T_LUNG', \
        'HS939T_SKIN', 'SF126_CENTRAL_NERVOUS_SYSTEM', 'KMRC20_KIDNEY', 'NCIH23_LUNG', 'T173_BONE', 'KMBC2_URINARY_TRACT', 'TE617T_SOFT_TISSUE', \
        'HEC59_ENDOMETRIUM', 'OC316_OVARY', 'ISTMES2_PLEURA', 'NCIH929_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SKNBE2_AUTONOMIC_GANGLIA', \
        'CMK86_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'P31FUJ_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH226_LUNG', 'OUMS23_LARGE_INTESTINE', \
        'NCIH1648_LUNG', 'ONS76_CENTRAL_NERVOUS_SYSTEM', 'NCIH1693_LUNG', 'SW1088_CENTRAL_NERVOUS_SYSTEM', 'HS936T_SKIN', 'HEC251_ENDOMETRIUM', \
        'HSC2_UPPER_AERODIGESTIVE_TRACT', 'KHM1B_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RERFLCAD2_LUNG', 'HSC3_UPPER_AERODIGESTIVE_TRACT', \
        'KMS20_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RKN_SOFT_TISSUE', 'GLC82_LUNG', 'OC314_OVARY', 'KMM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'SNGM_ENDOMETRIUM', 'TT_OESOPHAGUS', 'HUH7_LIVER', 'D341MED_CENTRAL_NERVOUS_SYSTEM', 'HUNS1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1838_LUNG', \
        'HCC1500_BREAST', 'P3HR1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HCC4006_LUNG', 'HCC2157_BREAST', 'HCC1419_BREAST', 'NCIH1048_LUNG', 'SKNSH_AUTONOMIC_GANGLIA', \
        'NCIH1184_LUNG', 'BT483_BREAST', 'UMUC3_URINARY_TRACT', 'OCILY3_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SCC9_UPPER_AERODIGESTIVE_TRACT', \
        'PEER_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH2085_LUNG', 'G292CLONEA141B1_BONE', 'RCM1_LARGE_INTESTINE', 'CI1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'DMS53_LUNG', 'DV90_LUNG', 'RERFLCKJ_LUNG', 'AML193_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1944_LUNG', 'NCIH660_PROSTATE', 'NCIH1755_LUNG', \
        'HUT102_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', '143B_BONE', 'NCIH1435_LUNG', 'HUT78_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1373_LUNG', 'NCIH1930_LUNG', \
        'SW1783_CENTRAL_NERVOUS_SYSTEM', 'MKN45_STOMACH', 'HCC56_LARGE_INTESTINE', 'LU65_LUNG', 'KMRC3_KIDNEY', 'DMS153_LUNG', '8505C_THYROID', 'SKOV3_OVARY', \
        'TC71_BONE', 'ZR7530_BREAST', 'HS229T_LUNG', 'KU812_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'UACC812_BREAST', 'BL41_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'PFEIFFER_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'A101D_SKIN', 'NCIH716_LARGE_INTESTINE', 'NCIH2023_LUNG', 'HS729_SOFT_TISSUE', \
        'HS616T_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1623_LUNG', 'NCIH1618_LUNG', 'RERFGC1B_STOMACH', 'MPP89_PLEURA', 'HEP3B217_LIVER', \
        'ISTMES1_PLEURA', 'HS895T_SKIN', 'OCILY10_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH2073_LUNG', 'SHP77_LUNG', 'SKM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'SW1353_BONE', 'BL70_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS675T_LARGE_INTESTINE', 'HOS_BONE', 'NCIH1836_LUNG', 'HCC1599_BREAST', 'NCIH727_LUNG', \
        'P12ICHIKAWA_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'TT2609C02_THYROID', 'M07E_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'ML1_THYROID', \
        'JURKAT_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS737T_BONE', 'SIMA_AUTONOMIC_GANGLIA', 'COLO320_LARGE_INTESTINE', \
        'EJM_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS600T_SKIN', 'EM2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NB4_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'JIMT1_BREAST', \
        'SUDHL1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SIGM5_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HN_UPPER_AERODIGESTIVE_TRACT', 'SUDHL6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'BHY_UPPER_AERODIGESTIVE_TRACT', 'KOPN8_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'MEC2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'DEL_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'BC3C_URINARY_TRACT', 'TO175T_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CAL51_BREAST', 'BFTC909_KIDNEY', 'HS870T_BONE', 'NOMO1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'RI1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'MUTZ5_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', '2313287_STOMACH', 'CL11_LARGE_INTESTINE', 'JVM3_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'MHHES1_BONE', 'HDQP1_BREAST', 'COLO680N_OESOPHAGUS', 'BEN_LUNG', 'BHT101_THYROID', 'AMO1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'MOLT16_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'L428_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CAL29_URINARY_TRACT', 'CADOES1_BONE', 'HDLM2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'BFTC905_URINARY_TRACT', \
        'SKMM2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'S117_SOFT_TISSUE', 'WSUDLCL2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RH30_SOFT_TISSUE', \
        'RPMI8402_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'OPM2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'MOLP8_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'EHEB_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'OCIM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CAL78_BONE', 'MHHCALL4_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'HCC33_LUNG', 'BCPAP_THYROID', 'CAL120_BREAST', 'LCLC103H_LUNG', 'COLO678_LARGE_INTESTINE', 'SCLC21H_LUNG', 'REC1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'KCL22_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CAL62_THYROID', 'RVH421_SKIN', 'CL34_LARGE_INTESTINE', 'CHP126_AUTONOMIC_GANGLIA', \
        'SUDHL5_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SW1116_LARGE_INTESTINE', 'KU1919_URINARY_TRACT', 'JMSU1_URINARY_TRACT', 'HS688AT_SKIN', 'NCIH2141_LUNG', \
        'HS863T_BONE', 'SW1710_URINARY_TRACT', 'ME1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'L540_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CAL33_UPPER_AERODIGESTIVE_TRACT', \
        'TE441T_SOFT_TISSUE', 'HS698T_LARGE_INTESTINE', 'COLO668_LUNG', 'SUPHD1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1105_LUNG', 'SUDHL10_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE',\
        'DMS454_LUNG', 'NCIH2081_LUNG', 'IGR1_SKIN', 'BICR22_UPPER_AERODIGESTIVE_TRACT', 'HS274T_BREAST', 'PF382_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1876_LUNG', \
        'MOLM6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SUDHL4_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'F36P_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH841_LUNG', 'HS281T_BREAST', \
        'HPBALL_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'DMS273_LUNG', 'SUDHL8_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'TT_THYROID', 'LS513_LARGE_INTESTINE', 'RD_SOFT_TISSUE', \
        'MOLT13_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'WM983B_SKIN', 'SR786_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'WM88_SKIN', 'HS821T_BONE', \
        'OCILY19_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'BICR31_UPPER_AERODIGESTIVE_TRACT', 'MOLP2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CORL279_LUNG', \
        'NALM19_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'BICR16_UPPER_AERODIGESTIVE_TRACT', 'TF1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'UMUC1_URINARY_TRACT', \
        'CHAGOK1_LUNG', '647V_URINARY_TRACT', 'MOLM16_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'UT7_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'PL21_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'NB1_AUTONOMIC_GANGLIA', 'OCIAML3_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'JEKO1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HCC827_LUNG', \
        'NUDHL1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'GRANTA519_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'COV362_OVARY', 'NCIH2126_LUNG', 'LXF289_LUNG', 'NCIH1092_LUNG', \
        'HS888T_BONE', 'SUPT11_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RCHACV_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'MHHNB11_AUTONOMIC_GANGLIA', 'SW837_LARGE_INTESTINE', \
        'JURLMK1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HRT18_LARGE_INTESTINE', 'HS822T_BONE', 'CORL24_LUNG', 'CORL311_LUNG', 'KE37_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'COLO684_ENDOMETRIUM', 'KASUMI6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'DOHH2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'LCLC97TM1_LUNG', \
        'NALM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'GP2D_LARGE_INTESTINE', 'NCIH2110_LUNG', 'HTK_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'OCIAML2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH2405_LUNG', 'COLO792_SKIN', 'BICR6_UPPER_AERODIGESTIVE_TRACT', 'SW48_LARGE_INTESTINE', \
        'MHHCALL2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'VMCUB1_URINARY_TRACT', '5637_URINARY_TRACT', 'SH4_SKIN', 'OCIAML5_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'BICR56_UPPER_AERODIGESTIVE_TRACT', 'PECAPJ41CLONED2_UPPER_AERODIGESTIVE_TRACT', 'OAW42_OVARY', 'KMH2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'OV7_OVARY', \
        'BV173_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS751T_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', '769P_KIDNEY', 'MDAPCA2B_PROSTATE', 'CORL95_LUNG', 'KYO1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'EOL1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CMLT1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CORL51_LUNG', 'COV434_OVARY', 'CORL88_LUNG', \
        'MONOMAC1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'COLO775_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'LP1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'HS742T_BREAST', 'HS940T_SKIN', 'LAMA84_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KARPAS620_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'LC1F_LUNG', \
        'HS934T_SKIN', 'WM793_SKIN', 'PECAPJ49_UPPER_AERODIGESTIVE_TRACT', 'CAL54_KIDNEY', '59M_OVARY', '697_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'MINO_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH2286_LUNG', 'HS343T_BREAST', 'L363_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'AN3CA_ENDOMETRIUM', \
        'JVM2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RT11284_URINARY_TRACT', 'HS819T_BONE', 'GRM_SKIN', 'PECAPJ34CLONEC12_UPPER_AERODIGESTIVE_TRACT', \
        'PECAPJ15_UPPER_AERODIGESTIVE_TRACT', 'JK1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CORL47_LUNG', 'HS294T_SKIN', 'COV644_OVARY', 'NALM6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'MHHCALL3_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SNU503_LARGE_INTESTINE', 'SNU878_LIVER', 'SNU738_CENTRAL_NERVOUS_SYSTEM', 'SNU626_CENTRAL_NERVOUS_SYSTEM', \
        'SNU668_STOMACH', 'SNU1105_CENTRAL_NERVOUS_SYSTEM', 'SNU175_LARGE_INTESTINE', 'SNU489_CENTRAL_NERVOUS_SYSTEM', 'SNU81_LARGE_INTESTINE', 'SNU761_LIVER', \
        'SNU407_LARGE_INTESTINE', 'CW2_LARGE_INTESTINE', 'JHOC5_OVARY', 'SNUC4_LARGE_INTESTINE', 'SNU466_CENTRAL_NERVOUS_SYSTEM', 'SNU1272_KIDNEY', \
        'SNU899_UPPER_AERODIGESTIVE_TRACT', 'SNU601_STOMACH', 'ECC10_STOMACH', 'SNU1076_UPPER_AERODIGESTIVE_TRACT', 'SNU283_LARGE_INTESTINE', 'LI7_LIVER', \
        'HCC1171_LUNG', 'GSS_STOMACH', 'SNU685_ENDOMETRIUM', 'SNU620_STOMACH', 'SNU886_LIVER', 'LMSU_STOMACH', 'SNU245_BILIARY_TRACT', 'SNU324_PANCREAS', \
        'GSU_STOMACH', 'SNU719_STOMACH', 'HUH6_LIVER', 'JHOM1_OVARY', 'SNU1214_UPPER_AERODIGESTIVE_TRACT', 'SNUC5_LARGE_INTESTINE', 'SNU119_OVARY', \
        'SNU201_CENTRAL_NERVOUS_SYSTEM', 'SNU840_OVARY', 'SNU349_KIDNEY', 'HCC1195_LUNG', 'TE10_OESOPHAGUS', 'ECC12_STOMACH', 'RCC10RGB_KIDNEY', 'CJM_SKIN', \
        'SNU308_BILIARY_TRACT', 'HCC95_LUNG', 'SNU213_PANCREAS', 'SNU1079_BILIARY_TRACT', 'SNU61_LARGE_INTESTINE', 'OVK18_OVARY', 'KLM1_PANCREAS', 'SNU478_BILIARY_TRACT', \
        'SNU520_STOMACH', 'SNU1040_LARGE_INTESTINE', 'SET2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SNU410_PANCREAS', 'HLC1_LUNG', 'ECGI10_OESOPHAGUS', 'ACCMESO1_PLEURA', \
        'PCM6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SNU216_STOMACH', 'HUH28_BILIARY_TRACT', 'KG1C_CENTRAL_NERVOUS_SYSTEM', 'CMK_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'PANC0504_PANCREAS', 'HS172T_URINARY_TRACT', 'OUMS27_BONE', 'A704_KIDNEY', 'TUHR14TKB_KIDNEY', 'NCIH2009_LUNG', 'TUHR4TKB_KIDNEY', 'NCIH1915_LUNG', \
        'YD15_SALIVARY_GLAND', 'TE8_OESOPHAGUS', 'MDAMB134VI_BREAST', 'TGBC11TKB_STOMACH', 'PK45H_PANCREAS', 'SNU182_LIVER', 'TE4_OESOPHAGUS', 'KYM1_SOFT_TISSUE', \
        'NCIH28_PLEURA', 'MEWO_SKIN', 'HSC4_UPPER_AERODIGESTIVE_TRACT', 'TM31_CENTRAL_NERVOUS_SYSTEM', 'HEC50B_ENDOMETRIUM', 'HS706T_BONE', \
        'KIJK_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH1694_LUNG', 'TE6_OESOPHAGUS', 'YD10B_UPPER_AERODIGESTIVE_TRACT', 'TE14_OESOPHAGUS', \
        'YD38_UPPER_AERODIGESTIVE_TRACT', 'YD8_UPPER_AERODIGESTIVE_TRACT', 'SNU1196_BILIARY_TRACT', 'BICR18_UPPER_AERODIGESTIVE_TRACT', 'TUHR10TKB_KIDNEY', \
        '8305C_THYROID', 'SNU46_UPPER_AERODIGESTIVE_TRACT', 'SNU1077_ENDOMETRIUM', 'JHUEM3_ENDOMETRIUM', 'KASUMI2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NCIH854_LUNG', \
        'HCC2279_LUNG', 'NCCSTCK140_STOMACH', 'U138MG_CENTRAL_NERVOUS_SYSTEM', 'CORL105_LUNG', 'HEC1B_ENDOMETRIUM', 'JHOM2B_OVARY', 'SHSY5Y_AUTONOMIC_GANGLIA', \
        'HEL_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CGTHW1_THYROID', 'FTC133_THYROID', 'NCIH292_LUNG', 'KMS18_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'TALL1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'KPL1_BREAST', 'NCIH1436_LUNG', 'CAL148_BREAST', 'HT55_LARGE_INTESTINE', 'NCIH1339_LUNG', 'HCC2935_LUNG',\
        'MDAMB435S_SKIN', 'WM1799_SKIN', '639V_URINARY_TRACT', 'TEN_ENDOMETRIUM', 'UACC893_BREAST', 'HCC1428_BREAST', 'NCIH1385_LUNG', 'RH41_SOFT_TISSUE', \
        'MEC1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HS852T_SKIN', 'NCIH1869_LUNG', 'MDST8_LARGE_INTESTINE', 'DND41_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'JHH6_LIVER', 'OAW28_OVARY', 'HCC1569_BREAST', 'HT115_LARGE_INTESTINE', 'CL14_LARGE_INTESTINE', 'MOTN1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'NUDUL1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'CL40_LARGE_INTESTINE', 'JL1_PLEURA', 'MONOMAC6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'TE125T_SOFT_TISSUE', \
        'SNU8_OVARY', 'SNU1197_LARGE_INTESTINE', 'DM3_PLEURA', 'MESSA_SOFT_TISSUE', 'KATOIII_STOMACH', 'ALLSIL_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'OSRC2_KIDNEY', \
        'NCIH3255_LUNG', 'F5_CENTRAL_NERVOUS_SYSTEM', 'U178_CENTRAL_NERVOUS_SYSTEM', 'SF172_CENTRAL_NERVOUS_SYSTEM', 'HCC1897_LUNG', 'TC32_BONE', 'EWS502_BONE', \
        'HK2_KIDNEY', 'KARPAS422_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'UMRC2_KIDNEY', 'RCC4_KIDNEY', 'SLR25_KIDNEY', 'SLR21_KIDNEY', 'UOK101_KIDNEY', 'SLR20_KIDNEY', \
        'OELE_OVARY', 'SALE_LUNG', 'UMRC6_KIDNEY', 'SLR26_KIDNEY', 'PRECLH_PROSTATE', 'HMEL_BREAST', 'TE159T_SOFT_TISSUE', 'EW8_BONE', 'ONCODG1_OVARY', 'SLR23_KIDNEY', \
        'BJHTERT_SKIN', 'HEKTE_KIDNEY', 'TIG3TD_LUNG', 'FTC238_THYROID', 'HOP92_LUNG', 'SKRC31_KIDNEY', 'HCC2814_LUNG', 'LN235_CENTRAL_NERVOUS_SYSTEM', 'HCC364_LUNG', \
        'SLR24_KIDNEY', 'SNB75_CENTRAL_NERVOUS_SYSTEM', 'LN443_CENTRAL_NERVOUS_SYSTEM', 'A1207_CENTRAL_NERVOUS_SYSTEM', 'U343_CENTRAL_NERVOUS_SYSTEM', \
        'SNU1033_LARGE_INTESTINE', 'UO31_KIDNEY', 'KELLY_p_CCLE_AffySNP_Oct2012_01_GenomeWideSNP_6_B01_1217624_KMS18_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'NHA_HT_DD', \
        'KELLY_p_CCLE_AffySNP_Oct2012_01_GenomeWideSNP_6_B03_1217476_TALL1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'SF539_CENTRAL_NERVOUS_SYSTEM', 'LN340_CENTRAL_NERVOUS_SYSTEM', \
        'CH157MN_CENTRAL_NERVOUS_SYSTEM', 'HNT34', 'SIHA', 'C8166', 'MOLT3_MOLT4', 'PLB985_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'OCIMY5_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'SF268_CENTRAL_NERVOUS_SYSTEM', 'LN382_CENTRAL_NERVOUS_SYSTEM', 'OCIMY7_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'HCC1359_LUNG', 'SF767_CENTRAL_NERVOUS_SYSTEM', \
        'SNU869_BILIARY_TRACT', 'JHESOAD1_OESOPHAGUS', 'OVCAR5_OVARY', 'COLO201_COLO205', 'LNZ308_CENTRAL_NERVOUS_SYSTEM', 'HOP62_LUNG', 'OPM1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', \
        'LN319_CENTRAL_NERVOUS_SYSTEM', 'CACO2', 'INA6_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'T3M10_LUNG', 'SKNO1_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'EKVX_LUNG', \
        'JJN3_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE', 'RH18_SOFT_TISSUE']


    EFM=["human_CRISPRi_19bp.matrix","human_CRISPRi_20bp.matrix","human_CRISPRi_21bp.matrix","human_mouse_CRISPR_KO_30bp.matrix"]

    samplenames=make_ed_table('adding-rows-samplenames', columns=["Files","Name"] )
    samples=make_ed_table('adding-rows-samples', columns=["Label","Pairness (paired or unpaired)",\
        "List of control samples","List of treated samples",\
        "List of control sgRNAs", "List of control genes", "CNV line"] )
    librarydf=make_ed_table(  'adding-rows-library', columns=["gene_ID","UID","seq","Annotation","EXON","CHRM","STRAND","STARTpos","ENDpos"])

    groups_=make_options(GROUPS)
    groups_val="CRISPR_Screening"

    species=make_options(["homo_sapiens","mus_musculus"])
    species_value="homo_sapiens"

    assembly=make_options(["hg19","mm10"])
    assembly_value="hg19"

    TRUE_FALSE=make_options(["True","False"])

    mageckflute_organism=make_options(["hsa","mmu"])

    mageck_test_remove_zero_=make_options([ "none","control","treatment","both","any" ]) # {none,control,treatment,both,any}

    CELL_LINES=make_options(CELL_LINES)

    EFM=make_options(EFM)

    readme='''
## cutadapt
Trim the 5' end adapter and shorten the reads to the sgRNA size.

- Upstream sequence, "upstreamseq": \[cutadapt\] Upstream sequence for trimming.

- sgRNA size, "sgRNA_size": \[cutadapt\] sgRNA size used for trimming. \[bowtie2\] Generate full mapping stats.

## bowtie
- Bowtie, "use_bowtie": \[bowtie2\] Use Bowtie to map reads. Default is False. * Not implemented in nextflow pipe yet.

## mageck count
Get the count matrice of sgRNA reads. The matrice is used for mageck test, mle and also the other tools e.g Acer, Bagel... 

- Only count, "ONLY_COUNT": \[mageck\] Stop workflow after mageck count. * Not implemented in nextflow pipe yet.

## mageck test
Or MAGeCK-RRA, a modified robust ranking aggregation (RRA) algorithm to identify positively or negatively selected genes.

- Mageck test remove zero, "mageck_test_remove_zero": \[mageck test\] Whether to remove zero-count sgRNAs in control and/or treatment experiments. Default: none (do not remove those zero-count sgRNAs).

- Zero threshold, "mageck_test_remove_zero_threshold": \[mageck test\] Zero value.

- CNV file, "cnv_file": \[mageck test\] The name of file containing the cell line to be used for copy number variation to normalize CNV-biased sgRNA scores prior to gene ranking.

- CNV line, "cnv_line": \[mageck test\] The name of the cell line to be used for copy number variation to normalize CNV-biased sgRNA scores prior to gene ranking. Note that the pipeline first takes the `CNV line` in `Samples` tab for each test. And if the `CNV line` in `Samples` tab  is empty, it will take this for all tests. If both empty, then the option will be ignored.

## mageck pathway
GSEA analysis for testing enriched pathway.

- GMT file, "gmt_file": \[mageck pathway\] GMT file used for GSEA.

## SSC
For calculating sgrna efficiency. The output file could be an optional input parameter for mageck mle.

- Efficiency matrix, "efficiency_matrix": \[SSC\] Weight matrix provided in the SSC source for calculating sgRNA efficiencies. If not given SSC will be skipped.
    - human_mouse_CRISPR_KO_30bp.matrix: matrix for CRISPR/Cas9 knockout, spacer length <=20 (optimized for 19 and 20). This matrix is used for scanning sequences that contain 20bp upstream of the PAM, and 10bp downstream of the PAM (including PAM).
    - human_CRISPRi_19bp.matrix: matrix for CRISPRi/a, spacer length =19. This matrix is used for scanning sequences of 19-bp spacer upstream of the PAM.
    - human_CRISPRi_20bp.matrix: matrix for CRISPRi/a, spacer length =20. This matrix is used for scanning sequences of 20-bp spacer upstream of the PAM.
    - human_CRISPRi_21bp.matrix: matrix for CRISPRi/a, spacer length =21. This matrix is used for scanning sequences of 21-bp spacer upstream of the PAM.


- SSC sgRNA size, "SSC_sgRNA_size": \[SSC\] sgRNA size used for calculating sgRNA efficiencies.

## mageck mle
MLE extends MAGeCK-RRA by a maximum likelihood estimation method to call essential genes. It can do pairwise test as RRA and can also test multiple conditions (a matrice is then required).

- Skip MLE, "skip_mle": \[MLE\] Skip MLE when not needed / applicable.

- MLE matrices, "mle_matrices": \[MLE\] If MLE matrices are provided please put them all in one folder together with your raw data. If not provided, mle will run two-sample-comparison like mageck test.
   
    - design matrix

        - links of the confusing wikis of design matrix: [simple matrix](https://sourceforge.net/p/mageck/wiki/demo/#step-2-prepare-the-design-matrix-file), [advanced](https://sourceforge.net/p/mageck/wiki/advanced_tutorial/#tutorial-4-make-full-use-of-mageck-mle-for-more-complicated-experimental-design-eg-paired-samples-time-series), [paper supplement, page 8 bottom](https://static-content.springer.com/esm/art%3A10.1186%2Fs13059-015-0843-6/MediaObjects/13059_2015_843_MOESM1_ESM.pdf) 
        - the explanation of [simple matrix](https://sourceforge.net/p/mageck/wiki/demo/#step-2-prepare-the-design-matrix-file) is apparently wrong as discussed [here](https://groups.google.com/g/mageck/c/83V91NQl_04/m/pXGhkNCuBAAJ)
        - other discussion in the forum (to make it more confusing) [link1](https://groups.google.com/g/mageck/c/Sfdba-4_494/m/coW-o8mtCAAJ), [link2](https://groups.google.com/g/mageck/c/dMbJx4qStlw/m/xs1KonW3AQAJ), [link3](https://groups.google.com/g/mageck/c/mQBDf3UBCqc/m/JOXZKmN-BQAJ)

    - p-value
        - discussion about permutation test versus wald test ([link1](https://groups.google.com/g/mageck/c/S3ucRXD8Q-s/m/Ukvy-r3nAgAJ), [link2](https://groups.google.com/g/mageck/c/ZPQcRfnw868/m/jn0zJpg1CAAJ)).

## vispr
Generating a yaml file for web-based visualization.

- Species, "vispr_species": \[vispr\] Species

- Assembly, "vispr_assembly": \[vispr\] Organism assembly

## FluteMLE 

*! R script breaks, needs debugging*

Generating downstream plots for mageck test and mageck mle. FluteMLE works either using a pair-wise comparison as control or using Depmap as control.
In the the case of a pairwise comparison as control it requires therefore a complex MLE matrix with more than 2 samples.
For the case of Depmap usage, if the organism used is `mmu` it will try to convert the gene symbols from `mmu` into `hsa`.

- Mageckflute organism, "mageckflute_organism": \[FluteMLE\] Mageckflute reference organism

- Depmap, "depmap": \[FluteMLE\] In the current pipeline, FluteMLE will not run if Depmap=False. If Depmap=True, FLuteMLE will run on the output from MAGeCK MLE pairwise test using Depmap as reference. For MAGeCK MLE with a design matrice (multiple conditions), it is possible to specify a control in your CRISPR screen with FLuteMLE ([example](https://www.bioconductor.org/packages/release/bioc/vignettes/MAGeCKFlute/inst/doc/MAGeCKFlute.html#normalization-of-beta-scores)), but this is not implemented yet.

- Depmap cell line, "depmap_cell_line": \[FluteMLE\] A character vector, specifying the cell lines in Depmap to be considered. If none is given than the most close one will be identified automaticaly from the depmap collection. Only used when depmap is True.

## magecku
[MAGeCK-iNC](https://kampmannlab.ucsf.edu/mageck-inc), MAGeCK-including Negative Controls.

- MageckU nontargeting tag, "nontargeting_tag": \[magecku\] How the non targeting controls are labelled in the `Annoatation` column in the `Library` tab. If empty, magecku will not run.

- MageckU FDR, "magecku_fdr":  \[magecku\] Significance cutoff for magecku. If empty, magecku will not run.

- MageckU Tresh. Ctrl, "magecku_threshold_control_groups": \[magecku\] Counts threshold for control groups - applied on counts table pre-mageck test.

- MageckU Tresh. Treat., "magecku_threshold_treatment_groups": \[magecku\] Counts threshold for treatment groups - applied on counts table pre-mageck test.

## BAGEL
[github repo](https://github.com/hart-lab/bagel)

Bayesian Analysis of Gene EssentiaLity.

- Bagel essential, "bagel_essential": \[bagel\] Bagel [essential genes list](https://github.com/hart-lab/bagel/blob/master/CEGv2.txt). 

- Bagel essential, "bagel_nonessential": \[bagel\] Bagel [non essential genes list](https://github.com/hart-lab/bagel/blob/master/NEGv1.txt).

## ACER
[Paper](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-021-02491-z), [github repo](https://github.com/CshlSiepelLab/ACE)

Similar to bagel, but does maximum likelihood tests on raw counts instead of takeing log-fold change of read abundances as input data.

- Acer neg. ctrl., "use_neg_ctrl": \[Acer\] Use negative control. If empty, acer will not run. For specifying control genes, the current pipeline take the list in the `List of control gens` column in `Samples` tab and it shall be comma delimited.

- Acer master library, "using_master_library": \[Acer\] User Acer master library. If True, then acer_master_library needs to be provided. Acer will do a test taken master libary counts into account. eg. (T12 drug vs T12 DMSO taken T0 into account)

- Acer master library, "acer_master_library": \[Acer\] Acer master library.

## MAUDE
[Paper](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-020-02046-8), [github repo](https://github.com/de-Boer-Lab/MAUDE)

For sorting-based expression screen. For example, a pooled CRISPRi screen with expression readout by FACS sorting into discrete bins and sequencing the abundances of the guides in each bin.

- Maude FACS input, "facs": \[Maude\] Tab separated values file with FACS results for Maude ([example](https://github.com/de-Boer-Lab/MAUDE/blob/master/inst/extdata/CD69_bin_percentiles.txt)).

- Maude Ctrl guides, "ctrl_guides": \[Maude\] One column file with control sgRNAs ids

## drugZ
Designed for chemogenetic interactions. This differs from CRISPR knockout screen: cells are split into drug-treated and untreated control samples, grown for several doublings; and the relative abundance of CRISPR gRNA sequences in the treated and untreated population is compared (instead of comparing to starting gRNA abundance).
    '''
    readme=dcc.Markdown(readme, style={"width":"90%", "margin":"10px"} )



    arguments=[
        dbc.Row( 
            [
                dbc.Col( html.Label('email') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value=current_user.email, type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Your email address.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Group') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='group', options=groups_, value=groups_val, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Experiment name') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='experiment_name', placeholder="PinAPL-py_demo", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Name of your choice.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Folder') ,md=3 , style={"textAlign":"right" ,'display': 'none'}), 
                dbc.Col( dcc.Input(id='folder', placeholder="my_proj_folder", value="FTP", type='text', style={ "width":"100%",'display': 'none' } ) ,md=3 ),
                dbc.Col( html.Label('Folder on smb://octopus.age.mpg.de/group_bit_automation/ containing your files. No subfolders.'),md=3 ,  style={'display': 'none'} ), 
            ], 
            style={"margin-top":10 , 'display': 'none'}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('md5sums'), md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='md5sums', placeholder="md5sums.file.txt", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('File with md5sums of your fastq.gz files.'), md=3), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('ftp user') ,md=3 , style={"textAlign":"right"}), 
                dbc.Col( dcc.Input(id='ftp', placeholder="ftp user name", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label("if data has already been uploaded please provide the user name used for ftp login"), md=3 ), 
            ], 
            style={ "margin-top":10, "margin-bottom":10 }),
        dbc.Row( 
            [
                dbc.Col( html.Label('CNV file') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='cnv_file', value="CCLE_copynumber_byGene_2013-12-03.txt", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[mageck test] The name of file containing the cell line to be used for copy number variation to normalize CNV-biased sgRNA scores prior to gene ranking.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('CNV line') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='cnv_line', options=CELL_LINES, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[mageck test] The name of the cell line to be used for copy number variation to normalize CNV-biased sgRNA scores prior to gene ranking.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Upstream sequence') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='upstreamseq',placeholder="TCTTGTGGAAAGGACGAAACNNNN", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[cutadapt] Upstream sequence for trimming.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('sgRNA size') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='sgRNA_size', placeholder="20", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[cutadapt] sgRNA size used for trimming. [bowtie2] Generate full mapping stats.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Efficiency matrix') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='efficiency_matrix', options=EFM, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[SSC] Weight matrix provided in the SSC source for calculating sgRNA efficiencies. If not given SSC will be skipped.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('SSC sgRNA size') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='SSC_sgRNA_size', placeholder="20", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[SSC] sgRNA size used for calculating sgRNA efficiencies.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('GMT file') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='gmt_file', placeholder="msigdb.v7.2.symbols.gmt_", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[mageck pathway] GMT file used for GSEA.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Mageck test remove zero') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='mageck_test_remove_zero', options=mageck_test_remove_zero_, value='none', style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[mageck test] Whether to remove zero-count sgRNAs in control and/or treatment experiments. Default: none (do not remove those zero-count sgRNAs).'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Zero threshold') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='mageck_test_remove_zero_threshold', value="0", type='text', style={ "width":"100%"} ) ,md=3 ), 
                dbc.Col( html.Label('[mageck test] Zero value'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Skip MLE') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='skip_mle', options=TRUE_FALSE, value='False', style={ "width":"100%"}),md=3 ), 
                dbc.Col( html.Label('[MLE] Skip MLE when not needed / applicable'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),

        dbc.Row( 
            [
                dbc.Col( html.Label('MLE matrices') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='mle_matrices', placeholder="folder_name", type='text', style={ "width":"100%"} ) ,md=3 ), 
                dbc.Col( html.Label('[MLE] If MLE matrices are provided please put them all in one folder together with your raw data'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Species') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='species', options=species, value=species_value, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[vispr] Species'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Assembly') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='assembly', options=assembly, value=assembly_value, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[vispr] Organism assembly'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Bowtie') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='use_bowtie', options=TRUE_FALSE, value="False", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[bowtie2] Use Bowtie to map reads.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Depmap') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='depmap', options=TRUE_FALSE, value="False", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[FluteMLE] Use Depmap as reference. A character vector, specifying the names of control samples. If there is no controls in your CRISPR screen, you can specify "Depmap" as ctrlname'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Depmap cell line') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='depmap_cell_line', type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[FluteMLE] A character vector, specifying the cell lines in Depmap to be considered. If none is given than the most close one will be identified automaticaly from the depmap collection.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Mageckflute organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='mageckflute_organism', options=mageckflute_organism, value="hsa", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[FluteMLE] Mageckflute reference organism'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Bagel essential') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='BAGEL_ESSENTIAL', value="/bagel/CEGv2.txt", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[bagel] Bagel essential genes list'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Bagel essential') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='BAGEL_NONESSENTIAL', value="/bagel/NEGv1.txt", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[bagel] Bagel non essential genes list'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('MageckU FDR') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='magecku_fdr', value="0.05", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[magecku] Significance cutoff for magecku'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('MageckU Tresh. Ctrl') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='magecku_threshold_control_groups', value="5", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[magecku] Counts threshold for control groups - applied on counts table pre-mageck test'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('MageckU Tresh. Treat.') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='magecku_threshold_treatment_groups', value="5", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[magecku] Counts threshold for treatment groups - applied on counts table pre-mageck test'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('MageckU nontargeting tag') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='nontargeting_tag', placeholder="Non-Targeting Control", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('[magecku] How the non targeting controls are labelled'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Acer neg. ctrl.') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='use_neg_ctrl', options=make_options(["T","F"]), style={ "width":"100%"}),md=3  ),
                dbc.Col( html.Label('[Acer] Use negative control.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Acer master library') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='using_master_library', options=make_options(["T","F"]), style={ "width":"100%"}),md=3 ) ,
                dbc.Col( html.Label('[Acer] User Acer master library.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Acer master library') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input( id='acer_master_library', type='text', style={ "width":"100%"} ) ,md=3  ) ,
                dbc.Col( html.Label('[Acer] Acer master library.'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Maude FACS input') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input( id='facs', placeholder="facs.file.tsv", type='text', style={ "width":"100%"} ) ,md=3  ) ,
                dbc.Col( html.Label('[Maude] Tab separated values file with FACS results for Maude'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Maude Ctrl guides') ,md=3 , style={"textAlign":"right" }),
                dbc.Col( dcc.Input( id='ctrl_guides', placeholder="ctrl.guides.tsv", type='text', style={ "width":"100%"} ) ,md=3  ) ,
                dbc.Col( html.Label('[Maude] One column file with control sgRNAs ids'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Only count') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown(id='ONLY_COUNT', options=TRUE_FALSE, value="False", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[mageck] Stop workflow after mageck count'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Ctrl replicates') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='cleanR_control_reps', value="1", type='text', style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('[cleanR] No. of reference replicates'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
    ]

# Maude::
#   "facs":"",
#   "ctrl_guides":

    card=[
        dbc.Card( 
            [
                html.Div(
                    dcc.Upload(
                        id='upload-data',
                        children=dcc.Loading(
                            id=f"data-load",
                            type="default",
                            children=html.Div(
                                [ html.A('upload a file or fill up the form',id='upload-data-text') ],
                                style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
                            ),
                        ),               

                        style={
                            'width': '100%',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            "margin-bottom": "5px",
                            "margin-top": "5px",
                        },
                        multiple=False,
                    ),
                ),
                dcc.Tabs(
                    [
                        dcc.Tab( readme, label="Readme", id="tab-readme") ,
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    samplenames,
                                    id="updatable-samplenames"
                                ),
                                html.Button('Add Row', id='editing-rows-samplenames-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Sample Names", id="tab-samplenames"
                        ),
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    samples,
                                    id="updatable-samples"
                                ),
                                html.Button('Add Row', id='editing-rows-samples-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Samples", id="tab-samples"
                        ),
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    librarydf,
                                    id="updatable-library"
                                ),
                                html.Button('Add Row', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Library", id="tab-library",
                        ),
                        dcc.Tab( arguments ,label="Info", id="tab-info" ) ,
                    ]
                )
                    

            ],
            body=True,
            style={"min-width":"372px","width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"0px"}#,'display': 'block'}#,"max-width":"375px","min-width":"375px"}"display":"inline-block"
        ),
        dbc.Button(
            'Submit',
            id='submit-button-state', 
            color="secondary",
            n_clicks=0, 
            style={"max-width":"372px","width":"200px","margin-top":"8px", "margin-left":"4px","margin-bottom":"50px"}#,"max-width":"375px","min-width":"375px"}
        ),  
        dbc.Modal(
            dcc.Loading(
                id=f"modal-load",
                type="default",
                children=
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Whoopss..",id="modal_header") ),
                        dbc.ModalBody("something went wrong!", id="modal_body"),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="close", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
            ),
            id="modal",
            is_open=False,
        ),
    ]

    app_content=html.Div(
        [
            dcc.Store( id='session-data' ),
            # dcc.Store( id='json-import' ),
            dcc.Store( id='update_labels_field-import'),
            dcc.Store( id='generate_markers-import'),
            dbc.Row( 
                [
                    dbc.Col(
                        card,
                        sm=12,md=12,lg=12,xl=12,
                        align="top",
                        style={"padding":"0px","overflow":"scroll"},
                    )
                ],
            align="start",
            justify="left",
            className="g-0",
            style={"height":"100%","width":"100%","overflow":"scroll"} #"86vh" "64vh"
            ),
            dcc.Download( id="download-file" )
        ]
    )
    return app_content


###
### Work from here on:
###

fields = [     
    "email", \
    "group",\
    "experiment_name",\
    "folder",\
    "md5sums",\
    "ftp",\
    "cnv_file",\
    "cnv_line",\
    "upstreamseq",\
    "sgRNA_size",\
    "efficiency_matrix",\
    "SSC_sgRNA_size",\
    "gmt_file",\
    "mageck_test_remove_zero",\
    "mageck_test_remove_zero_threshold",\
    "skip_mle",\
    "species",\
    "assembly",\
    "use_bowtie",\
    "depmap",\
    "depmap_cell_line",\
    "BAGEL_ESSENTIAL",\
    "BAGEL_NONESSENTIAL",\
    "mageckflute_organism",\
    "nontargeting_tag",\
    "magecku_fdr", \
    "magecku_threshold_control_groups",\
    "magecku_threshold_treatment_groups", \
    "use_neg_ctrl", \
    "using_master_library",\
    "acer_master_library",\
    "facs",\
    "ctrl_guides",\
    "mle_matrices",\
    "ONLY_COUNT",\
    "cleanR_control_reps"
]

outputs = [ Output(o, 'value') for o in fields ]

@dashapp.callback( 
    [ Output('upload-data-text', 'children'), 
    Output("updatable-samplenames", 'children'),
    Output("updatable-samples", 'children'),
    Output("updatable-library", 'children') 
    ] + outputs ,
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    prevent_initial_call=True)
def read_file(contents,filename,last_modified):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    extension=filename.split(".")[-1]
    if extension not in ['xls', "xlsx"] :
        raise dash.exceptions.PreventUpdate
    exc=pd.ExcelFile(io.BytesIO(decoded))

    if "sampleNames" in exc.sheet_names :
        samplenames=pd.read_excel(io.BytesIO(decoded), sheet_name="sampleNames")
        samplenames=make_ed_table('adding-rows-samplenames', df=samplenames )
    else:
        samplenames= dash.no_update

    if "samples" in exc.sheet_names :
        samples=pd.read_excel(io.BytesIO(decoded), sheet_name="samples")
        samples=make_ed_table('adding-rows-samples', df=samples )
    else:
        samples=dash.no_update

    if "library" in exc.sheet_names :
        library=pd.read_excel(io.BytesIO(decoded), sheet_name="library")
        library=make_ed_table('adding-rows-library', df=library )
    else:
        library=dash.no_update
    
    if "crispr" not in exc.sheet_names :
        arguments=[ dash.no_update for f in fields ]
    else:
        arguments_df=pd.read_excel(io.BytesIO(decoded), sheet_name="crispr")
        arguments_list=arguments_df["Field"].tolist()
        arguments=[]
        for f in fields :
            if f in arguments_list :
                val= arguments_df[arguments_df["Field"]==f]["Value"].tolist()[0]
                arguments.append(val)
            else:
                arguments.append( dash.no_update )
            
    return [ filename ] + [ samplenames, samples, library ] +  arguments 


states=[ State(f, 'value') for f in fields ]

# # main submission call
@dashapp.callback(
    Output("modal_header", "children"),
    Output("modal_body", "children"),
    Output("download-file","data"),
    # Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    [ State("adding-rows-samplenames", 'data'),
    State("adding-rows-samples", 'data'),
    State("adding-rows-library", 'data') 
    ]+states,
    prevent_initial_call=True )
def update_output(n_clicks, \
        samplenames, \
        samples, \
        library, \
        email, \
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        ftp,\
        cnv_file,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        skip_mle,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism,\
        nontargeting_tag,\
        magecku_fdr, \
        magecku_threshold_control_groups,\
        magecku_threshold_treatment_groups, \
        use_neg_ctrl, \
        using_master_library,\
        acer_master_library,\
        facs,\
        ctrl_guides,\
        mle_matrices,\
        ONLY_COUNT,\
        cleanR_control_reps ):
    # header, msg = check_access( 'rnaseq' )
    # header, msg = None, None # for local debugging 
    # if msg :
    #     return header, msg
    # if not wget:
    #     wget="NONE"

    # try:

    # print(samplenames)
    # print("\n")
    # print(samples)
    header, msg = check_access( 'crispr' )
    if not msg:
        authorized = True
    else:
        authorized= False
    
    user_domain=current_user.email
    user_domain=user_domain.split("@")[-1]
    mps_domain="mpg.de"

    if ( user_domain[-len(mps_domain):] != mps_domain ) and ( authorized ) :
        group="Bioinformatics"

    if ONLY_COUNT == "False":
        sample_names_tab=pd.json_normalize(samplenames)
        all_samples=list(set(sample_names_tab["Name"].tolist()))
        
        samples_tab=pd.json_normalize(samples)
        
        ## checking list of control samples
        cont_samples=[s.split(",") for s in samples_tab["List of control samples"].tolist()]
        cont_samples=list(set( [item for sublist in cont_samples for item in sublist] ))

        ## checking list of treat samples
        treat_samples=[s.split(",") for s in samples_tab["List of treated samples"].tolist()]
        treat_samples=list(set( [item for sublist in treat_samples for item in sublist]))

        control_treat=cont_samples+treat_samples
        control_treat=list(set(control_treat))

        for sam in control_treat:
            if sam not in all_samples:
                header="Attention"
                msg='''One or more samples in your list of control or treated samples does not match the sample names.'''
                return header, msg, dash.no_update

    subdic=generate_submission_file( samplenames,\
        samples,\
        library,\
        email,\
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        cnv_file,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        skip_mle,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism,\
        nontargeting_tag,\
        magecku_fdr,\
        magecku_threshold_control_groups,\
        magecku_threshold_treatment_groups,\
        use_neg_ctrl,\
        using_master_library,\
        acer_master_library,\
        facs,\
        ctrl_guides,\
        mle_matrices,\
        ONLY_COUNT,\
        cleanR_control_reps )
    
    # samples=pd.read_json(subdic["samples"])
    # metadata=pd.read_json(subdic["metadata"])

    # validation=validate_metadata(metadata)
    # if validation:
    #     header="Attention"
    #     return header, validation

    filename=subdic["filename"]
    json_filename=subdic["json_filename"]
    json_config=subdic["json"]

    json_config[os.path.basename(json_filename)]=json.loads(json_config[os.path.basename(json_filename)])

    # print(json_config[os.path.basename(json_filename)]["studio"])


    if os.path.isfile(subdic["filename"]):
        header="Attention"
        msg='''You have already submitted this data. Re-submission will not take place.'''
        return header, msg, dash.no_update
    else:
        header="Success!"
        msg='''Please allow a summary file of your submission to download and check your email for confirmation.'''
    


    # user_domain=user_domain.split("@")[-1]
    # mps_domain="mpg.de"
    # if user_domain[-len(mps_domain):] == mps_domain :
    # if user_domain !="age.mpg.de" :
        # subdic["filename"]=subdic["filename"].replace("/submissions/", "/submissions_ftp/")
    if ( user_domain[-len(mps_domain):] == mps_domain ) or ( authorized ) :


        filename=os.path.join("/submissions_ftp/",filename)
        json_filename=os.path.join("/submissions_ftp/",json_filename)
        filename_=os.path.basename(filename)
        json_filename_=os.path.basename(json_filename)
        
        # subdic["filename"]=subdic["filename"].replace("/submissions/", "/submissions_ftp/")

        sampleNames=pd.read_json(json_config[filename_]["sampleNames"])
        samples=pd.read_json(json_config[filename_]["samples"])
        library=pd.read_json(json_config[filename_]["library"])
        arguments=pd.read_json(json_config[filename_]["crispr"])

        def writeout(subdic=subdic, json_config=json_config, json_filename=json_filename, arguments=arguments,filename=filename ):
            EXCout=pd.ExcelWriter(filename)
            sampleNames[["Files","Name"]].to_excel(EXCout,"sampleNames",index=None)
            samples[["Label","Pairness (paired or unpaired)", "List of control samples","List of treated samples","List of control sgRNAs", "List of control genes", "CNV line" ]].to_excel(EXCout,"samples",index=None)
            
            ## Checking if library positional info was provided
            optional_columns = ["EXON", "CHRM", "STRAND", "STARTpos", "ENDpos"]
            # Base columns that are always needed
            base_columns = ["gene_ID", "UID", "seq", "Annotation"]
            # Check if the optional columns are in the DataFrame
            columns_to_include = base_columns + [col for col in optional_columns if col in library.columns]
            library[columns_to_include].to_excel(EXCout, "library", index=None)
            #library[["gene_ID","UID","seq","Annotation"]].to_excel(EXCout,"library",index=None)
            
            arguments.to_excel(EXCout,"crispr",index=None)
            EXCout.save()
        
            with open(json_filename, "w") as out:
                json.dump(json_config,out)

        writeout()

        ftp_user=send_submission_ftp_email(user=current_user, submission_type="crispr", submission_tag=json_filename, submission_file=json_filename, attachment_path=json_filename, ftp_user=ftp)
        arguments=pd.concat([arguments,ftp_user])
        ftp_user=ftp_user["Value"].tolist()[0]
        raw_folder=json_config[json_filename_]["raven"]["raw_fastq"]
        raw_folder=os.path.join( raw_folder, ftp_user  )
        json_config[os.path.basename(json_filename)]["raven"]["ftp"]=ftp_user
        json_config[os.path.basename(json_filename)]["studio"]["ftp"]=ftp_user
        json_config[os.path.basename(json_filename)]["raven"]["raw_fastq"]=raw_folder
        json_config[os.path.basename(json_filename)]["studio"]["raw_fastq"]=raw_folder

        if mle_matrices:
            json_config[os.path.basename(json_filename)]["raven"]["mle_matrices"]=os.path.join(raw_folder,mle_matrices)
            json_config[os.path.basename(json_filename)]["studio"]["mle_matrices"]=os.path.join(raw_folder,mle_matrices)

        if BAGEL_NONESSENTIAL != "/bagel/NEGv1.txt" :
            json_config[os.path.basename(json_filename)]["raven"]["bagel_nonessential"]=os.path.join(raw_folder,BAGEL_NONESSENTIAL)
            json_config[os.path.basename(json_filename)]["studio"]["bagel_nonessential"]=os.path.join(raw_folder,BAGEL_NONESSENTIAL)
        
        if BAGEL_ESSENTIAL != "/bagel/CEGv2.txt" :
            json_config[os.path.basename(json_filename)]["raven"]["bagel_essential"]=os.path.join(raw_folder,BAGEL_ESSENTIAL)
            json_config[os.path.basename(json_filename)]["studio"]["bagel_essential"]=os.path.join(raw_folder,BAGEL_ESSENTIAL)
        
        if gmt_file:
            if gmt_file == "msigdb.v7.2.symbols.gmt" :
                json_config[os.path.basename(json_filename)]["raven"]["gmt_file"]="/nexus/posix0/MAGE-flaski/service/projects/data/CRISPR_Screening/CS_main_pipe/msigdb.v7.2.symbols.gmt"
                json_config[os.path.basename(json_filename)]["studio"]["gmt_file"]="/nexus/posix0/MAGE-flaski/service/projects/data/CRISPR_Screening/CS_main_pipe/msigdb.v7.2.symbols.gmt"
            else:
                json_config[os.path.basename(json_filename)]["raven"]["gmt_file"]=os.path.join(raw_folder,gmt_file)
                json_config[os.path.basename(json_filename)]["studio"]["gmt_file"]=os.path.join(raw_folder,gmt_file)
        
        if cnv_file == "CCLE_copynumber_byGene_2013-12-03.txt" :
            json_config[os.path.basename(json_filename)]["raven"]["cnv_file"]="/nexus/posix0/MAGE-flaski/service/projects/data/CRISPR_Screening/CS_main_pipe/CCLE_copynumber_byGene_2013-12-03.txt"
            json_config[os.path.basename(json_filename)]["studio"]["cnv_file"]="/nexus/posix0/MAGE-flaski/service/projects/data/CRISPR_Screening/CS_main_pipe/CCLE_copynumber_byGene_2013-12-03.txt"
        else:
            json_config[os.path.basename(json_filename)]["raven"]["cnv_file"]=os.path.join(raw_folder,cnv_file)
            json_config[os.path.basename(json_filename)]["studio"]["cnv_file"]=os.path.join(raw_folder,cnv_file)
        
        writeout(json_config=json_config, arguments=arguments )

        # json_config=json.dumps(json_config)

        def write_archive(bytes_io):
            with zipfile.ZipFile(bytes_io, mode="w") as zf:
                for f in [ filename, json_filename ]:
                    zf.write(f,  os.path.basename(f) )

        return header, msg, dcc.send_bytes(write_archive, os.path.basename(filename).replace("xlsx","zip") )

    else:
        json_config=json.dumps(json_config)

        return header, msg, dict(content=json_config, filename=os.path.basename(json_filename)) 


    # if user_domain == "age.mpg.de" :
    # send_submission_email(user=current_user, submission_type="crispr", submission_tag=subdic["filename"], submission_file=None, attachment_path=None)
    # return header, msg, dcc.send_file( subdic["filename"] )
    # else:
        #     send_submission_ftp_email(user=current_user, submission_type="RNAseq", submission_file=os.path.basename(subdic["filename"]), attachment_path=subdic["filename"])
    # except:
    #     return dash.no_update, dash.no_update, dash.no_update
    

@dashapp.callback(
    Output('adding-rows-samplenames', 'data'),
    Input('editing-rows-samplenames-button', 'n_clicks'),
    State('adding-rows-samplenames', 'data'),
    State('adding-rows-samplenames', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output('adding-rows-samples', 'data'),
    Input('editing-rows-samples-button', 'n_clicks'),
    State('adding-rows-samples', 'data'),
    State('adding-rows-samples', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output('adding-rows-library', 'data'),
    Input('editing-rows-library-button', 'n_clicks'),
    State('adding-rows-library', 'data'),
    State('adding-rows-library', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output("modal", "is_open"),
    [Input("submit-button-state", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    )
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
