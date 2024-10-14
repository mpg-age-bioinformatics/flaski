from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from flask_login import current_user
from flask_caching import Cache
import plotly.graph_objects as go
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import make_options, make_table
import os
import uuid
import json
import base64
import pandas as pd
import humanize
from myapp.models import User
import stat
from datetime import datetime
import shutil
from time import sleep
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from ._neanderthalage import read_agegene, read_drug, read_agedist


PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

FONT_AWESOME = 'https://use.fontawesome.com/releases/v5.7.2/css/all.css'


# Step 1: Setting Up the Dash Application
dashapp = dash.Dash('neanderthalage', # sets the name of the App
                    url_base_pathname=f'{PAGE_PREFIX}/neanderthalage/',  # sets the base URL path for the app
                    meta_tags=META_TAGS,  # allows setting meta tags for the HTML head.
                    server=app, # integrates the Dash app with a Flask server instance.
                    external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], # includes external stylesheets, here Bootstrap and Font Awesome.
                    title='Neanderthal age', # sets the title of the webpage.
                    assets_folder=app.config['APP_ASSETS'])# , assets_folder='/flaski/flaski/static/dash/') # specifies the folder for storing additional static assets.

# Step 2: Protecting the Dash Views
protect_dashviews(dashapp)

# Step 3: Configuring Sessions and Caching

if app.config['SESSION_TYPE'] == 'sqlalchemy':
    import sqlalchemy
    engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'] , echo=True)
    app.config['SESSION_SQLALCHEMY'] = engine
elif app.config['CACHE_TYPE'] == 'RedisCache' :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
    })
elif app.config['CACHE_TYPE'] == 'RedisSentinelCache' :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisSentinelCache',
        'CACHE_REDIS_SENTINELS': [ 
            [ os.environ.get('CACHE_REDIS_SENTINELS_address'), os.environ.get('CACHE_REDIS_SENTINELS_port') ]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER')
    })

# Step 4: Define helper functions:

def change_table_minWidth(tb,minwidth): # Sets the minimum width of a table.
    st=tb.style_table
    st['minWidth']=minwidth
    tb.style_table=st
    return tb

def change_fig_minWidth(fig,minwidth): # Sets the minimum width of a figure.
    st=fig.style
    st['minWidth']=minwidth
    fig.style=st
    return fig

# Step 5: # Layout Definition
dashapp.layout = html.Div(
    [
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),  # Stores a session ID in the client-side.
        dcc.Store(id='data-store'),  # Stores the loaded DataFrame
        dcc.Location(id='url', refresh=False),  # Manages the URL of the app
        html.Div(id='protected-content'),  # Container for the protected content
        html.Div(id='my-output'),  # Example output div for displaying the DataFrame
    ]
)


# Step 6: Define Styles for card element

card_label_style={'margin-top':'5px'}
card_input_style={'width':'100%','height':'35px'}
card_body_style={ 'padding':'2px', 'padding-top':'4px'}


# Step 7: Define callback
# Callback for protected content
# -1. Callback definition: This callback updates the protected-content based on the session ID.
@dashapp.callback(
    Output('protected-content', 'children'),
    Input('session-id', 'data')
    )
def make_layout(session_id): 
    # -2. Authorization check:
    # Checks if 'neanderthalage' is a private route.
    # Queries the database for route-specific accessible information.
    # Validates the current user against the list of allowed users and domains.
    # Redirects to the index page if the user is not authorized.

    if 'neanderthalage' in PRIVATE_ROUTES :
        appdb=PrivateRoutes.query.filter_by(route='neanderthalage').first()
        if not appdb:
            return dcc.Location(pathname=f'{PAGE_PREFIX}/', id='index')
        allowed_users=appdb.users
        if not allowed_users:
            return dcc.Location(pathname=f'{PAGE_PREFIX}/', id='index')
        if current_user.id not in allowed_users :
            allowed_domains=appdb.users_domains
            if current_user.domain not in allowed_domains:
                return dcc.Location(pathname=f'{PAGE_PREFIX}/', id='index')

    eventlog = UserLogging(email=current_user.email, action='visit neanderthalage')
    db.session.add(eventlog)
    db.session.commit()

    def make_loading(children,i):
        return dcc.Loading(
            id=f'menu-load-{i}',
            type='default',
            children=children,
        )
    
    # 5: Define the Protected Content Layout

    protected_content=html.Div(
        [
            make_navbar_logged('Neanderthal age',current_user), # Navbar: Includes a navigation bar indicating the current user.
            html.Div(id='app_access'), 
            dcc.Store(data=str(uuid.uuid4()), id='session-id'), # Session ID Store: Stores a new session ID.
            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dbc.Card(
                                [   
                                    html.H5('Filters', style={'margin-top':10}), 
                                    html.Label('Gene Query'), make_loading( dcc.Dropdown(id='opt-genenames', multi=True), 1),
                                    dcc.Checklist(options=[{'label':'Neanderthal mutated genes', 'value':'disable'}], value=[], id='altaimut-only', style={'width':'100%', 'margin-top':10}, inputStyle={'margin-right': '10px'}),
                                    dcc.Checklist(options=[{'label':'Only drug targeted genes', 'value':'disable'}], value=[], id='drug-target-gene', style={'width':'100%', 'margin-top':10}, inputStyle={'margin-right': '10px'}),
                                    html.Label('Drug Query'),  make_loading( dcc.Dropdown( id='opt-drugnames', multi=True), 4 ),
                                    dcc.Checklist(options=[{'label':'Natural products', 'value':'disable'}], value=[], id='natural-only', style={'width':'100%', 'margin-top':10}, inputStyle={'margin-right': '10px'}),
                                ],
                                body=True # Filters Column: Contains filters for gene queries, drug queries, and checklists for specific options.
                            ),
                            dbc.Button(
                                'Submit',
                                id='submit-button-state', 
                                color='secondary',
                                n_clicks=0, 
                                style={'width':'100%','margin-top':'2px','margin-bottom':'2px'}#,'max-width':'375px','min-width':'375px'}
                            ), # Includes a submit button.
                        ],
                        xs=12,sm=12,md=6,lg=4,xl=3,
                        align='top',
                        style={'padding':'0px','margin-bottom':'50px'} 
                    ),               
                    dbc.Col(
                        [ 
                            dcc.Loading(
                                id='loading-output-2',
                                type='default',
                                children=[ html.Div(id='my-output')],
                                style={'margin-top':'50%'} 
                            ), # Output Column: Displays loading spinner and output content.
                        ],
                        xs=12,sm=12,md=6,lg=8,xl=9,
                        style={'margin-bottom':'50px'}
                    ),
                ],
                align='start',
                justify='left',
                className='g-0',
                style={'width':'100%'}
            ),
            navbar_A,
        ],
        style={'height':'100vh','verticalAlign':'center'}
    )

    return protected_content 


@dashapp.callback(
    Output(component_id='opt-genenames', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-genenames', 'data'),
    Input('altaimut-only', 'value') )
def update_genes(session_id, genenames, altai_only):
    print('functions is called')
    agegenedf=read_agegene(cache=cache)
    agegenedf_=agegenedf

    if genenames:
        agegenedf_=agegenedf.loc[ agegenedf['Gene symbol'].isin(genenames) ]
        if len(altai_only) > 0 and altai_only[0] == 'disable':
            agegenedf_=agegenedf_.loc[ agegenedf_['Altai mutated'] == 'True' ]

    elif len(altai_only) > 0 and altai_only[0] == 'disable':
        agegenedf_=agegenedf_.loc[ agegenedf_['Altai mutated'] == 'True' ]

    genes_=list(set( agegenedf_['Gene symbol'].tolist() ))
    genes=make_options(genes_)

    return genes
     

@dashapp.callback(
    Output(component_id='opt-drugnames', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-drugnames', 'data'),
    Input('natural-only', 'value')
    )
def update_drug(session_id, drugnames, natural_only): #, 
    print('drug functions is called')
    print('update_drug is called')
    drugdf=read_drug(cache=cache)
    drugdf_=drugdf

    if drugnames:
        drugdf_ = drugdf.loc[ drugdf['Drug Name'].isin(drugnames) ]

        if len(natural_only) > 0 and natural_only[0] == 'disable':
            drugdf_ = drugdf_.loc[ drugdf_['Natural source'] == 'True' ]
    
    elif len(natural_only) > 0 and natural_only[0] == 'disable':
        drugdf_ = drugdf_.loc[ drugdf_['Natural source'] == 'True' ]
    
    drugs_=list(set( drugdf_['Drug Name'].tolist() ))
    drugs=make_options(drugs_)
    return drugs

################################################################################

@dashapp.callback(
    Output('my-output','children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('opt-genenames', 'value'),
    State('opt-drugnames', 'value'),
    State('altaimut-only', 'value'),
    State('natural-only', 'value'),
    State('drug-target-gene', 'value'),
)

def update_output(session_id, n_clicks, genenames, drugnames, altai_only, natural_only, drugtarget_gene):

    ageingdf=read_agegene(cache=cache)
    ageingdf_table=make_table(ageingdf, id='all-agegenes-geneTab')

    drugdf=read_drug(cache=cache)
    drugdf_table=make_table(drugdf, id='all-drugs-drugTab')
    drugdf_genenames = drugdf['Target Symbol'].tolist()

    agedistdf=read_agedist(cache=cache)
    agedistdf_table=make_table(agedistdf, id='all-agedist-mutTab')

    readme_content = '''

**Neanderthal Age App**

The Neanderthal Age App integrates genetic, pharmaceutical, and mutational data from diverse databases, offering a comprehensive view across three tabs:

**Gene Tab**: Displays selected aging-related genes.  
**Drug-Target Tab**: Shows drug-target interactions.  
**Mutation Tab**: Presents gene mutations across different age distributions.

**Detailed Information**

**Gene Tab**  
By default, this tab showcases 4005 aging-related genes sourced from five prominent databases. Original references are provided for traceability:
- AM: [Digital Ageing Atlas](https://ageing-map.org/)
- GA: [GenAge: The Ageing Gene Database](https://genomics.senescence.info/genes/index.html)
- CA: [CellAge: The Database of Cell Senescence Genes](https://genomics.senescence.info/cells/)
- LM: [LongevityMap: Human Longevity Genetic Variants](https://genomics.senescence.info/longevity/)
- BM: [Biomart](https://www.ensembl.org/info/data/biomart/index.html)

Columns include:
- Gene symbol (searchable)
- Ensembl gene ID
- Altai Neanderthal genome mutation status
- Source databases

**Drug-Target Tab**  
This tab defaults to displaying 14,232 drug-target interactions involving 3344 unique drugs and 1352 target genes. Data are aggregated from:
- [DGIdb: The Drug Gene Interaction Database](https://www.dgidb.org/)
- [OpenTargets Platform](https://platform.opentargets.org/)
- [Therapeutic Target Database: TTD](https://idrblab.net/ttd/)

Columns include:
- Identification of natural compounds sourced from [ChEMBL](https://www.ebi.ac.uk/chembl/web_components/explore/compounds/)
- Mutation status of targeted genes in the Altai Neanderthal genome
- Identification of aging-related genes (within the 4005 aging genes)
- Additional columns are listed if data from [DrugAge: The Database of Aging-related Drugs](https://genomics.senescence.info/drugs/) is available, including species tested, significance of results, average lifespan change, maximum lifespan change (positive for increased lifespan, negative for decreased lifespan), and PubMed ID.

**Mutation Tab**  
By default, this tab presents 18,558 unique gene mutations across various age distributions. The data represent 242,495 mutations from 10,323 patients, analyzed from [SomamutDB](https://vijglab.einsteinmed.edu/SomaMutDB/).

Notes:
- Only includes mutations highly and moderately affecting gene function, assessed using [VEP: Ensembl Variant Effect Predictor](https://www.ensembl.org/info/docs/tools/vep/index.html).
- Gene mutations are presented as counts per 1000 individuals.

**Usage**  
Filters can be combined to select genes and drugs, showcasing gene-drug interactions and gene mutation age distributions based on your preferences.
                                                   
'''
    readme = dcc.Markdown(readme_content, style={"width":"90%", "margin":"10px"})

    minwidth=['All ageing genes']

    gene_bol = False #1x
    gene_altai_bol = False #2 x
    gene_altai_drug_bol = False #3 
    gene_altai_drug_natural_bol = False #4
    gene_altai_natural_bol = False #5
    gene_altai_drugtarget_bol= False #6
    gene_drug_bol = False #7
    gene_drug_natural_bol = False  #8
    gene_natural_bol = False #9
    gene_drugtarget_bol = False #10
    altai_bol = False #11
    altai_drug_bol = False #12
    altai_drug_natural_bol = False #13
    altai_natural_bol = False #14
    drug_bol = False #15
    drug_natural_bol = False #16
    natural_bol = False #17
    drugtarget_bol = False #18
    altai_drugtarget_bol = False #19

    gene_altai_genenames = []
    altai_genenames = []
    altai_drugname_genenames = []
    altai_drugname_natural_genenames = []
    altai_natural_genenames = []
    drug_genenames = []
    drug_natural_genenames = []
    natural_genenames = []
    

    if genenames: #1. gene_bol
        df_gene_geneTab = ageingdf.loc[ ageingdf['Gene symbol'].isin(genenames) ]
        df_gene_geneTab_table = make_table(df_gene_geneTab, 'entry-gene-geneTab')

        df_gene_drugTab = drugdf.loc[ drugdf['Target Symbol'].isin(genenames) ]
        df_gene_drugTab_table = make_table(df_gene_drugTab, 'entry-gene-drugTab')
        df_gene_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(genenames)]
        df_gene_mutTab_table = make_table(df_gene_mutTab, 'entry-gene-mutTab')

        if len(altai_only) > 0 and altai_only[0] == 'disable': # 2. gene_altai_bol
            df_gene_altai_geneTab = df_gene_geneTab.loc[ df_gene_geneTab['Altai mutated'] == 'True' ]
            df_gene_altai_geneTab_table = make_table(df_gene_altai_geneTab, 'entry-gene-altai-geneTab')

            gene_altai_genenames = df_gene_altai_geneTab['Gene symbol'].tolist()
            df_gene_altai_drugTab = drugdf.loc[ drugdf['Target Symbol'].isin(gene_altai_genenames) ]
            df_gene_altai_drugTab_table = make_table(df_gene_altai_drugTab, 'entry-gene-altai-drugTab')
            df_gene_altai_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_altai_genenames)]
            df_gene_altai_mutTab_table = make_table(df_gene_altai_mutTab, 'entry-gene-altai-mutTab')

            if drugnames: # 3. gene_altai_drug_bol

                df_gene_altai_drugname_drugTab = df_gene_altai_drugTab.loc[ df_gene_altai_drugTab['Drug Name'].isin(drugnames) ]
                df_gene_altai_drugname_drugTab_table = make_table(df_gene_altai_drugname_drugTab, 'entry-gene-altai-drugname-drugTab')

                gene_altai_drug_genenames=df_gene_altai_drugname_drugTab['Target Symbol'].tolist()
                df_gene_altai_drugname_geneTab = df_gene_altai_geneTab.loc[ df_gene_altai_geneTab['Gene symbol'].isin(gene_altai_drug_genenames) ]
                df_gene_altai_drugname_geneTab_table = make_table(df_gene_altai_drugname_geneTab, 'entry_gene_altai_drugname_geneTab')
                df_gene_altai_drugname_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_altai_drug_genenames)]
                df_gene_altai_drugname_mutTab_table = make_table(df_gene_altai_drugname_mutTab, 'entry-gene-altai-drugname_mutTab')

                if len(natural_only) > 0 and natural_only[0] == 'disable': # 4. gene_altai_drug_natural_bol
                    print('\n\ngene entered: ', genenames, 'drug entered: ', drugnames, ' altai_only, natural_only enabled\n\n') 
                    df_gene_altai_drugname_natural_drugTab = df_gene_altai_drugname_drugTab.loc[ df_gene_altai_drugname_drugTab['Natural source'] == 'True' ]
                    df_gene_altai_drugname_natural_drugTab_table = make_table(df_gene_altai_drugname_natural_drugTab, 'entry-gene-altai-drugname-natural-drugTab')

                    gene_altai_drugname_natural_genenames = df_gene_altai_drugname_natural_drugTab['Target Symbol'].tolist()
                    df_gene_altai_drugname_natural_geneTab = df_gene_geneTab.loc[df_gene_geneTab['Gene symbol'].isin(gene_altai_drugname_natural_genenames)]
                    df_gene_altai_drugname_natural_geneTab_table = make_table(df_gene_altai_drugname_natural_geneTab, 'entry-gene-altai-drugname-natural-geneTab')
                    df_gene_altai_drugname_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_altai_drugname_natural_genenames)]
                    df_gene_altai_drugname_natural_mutTab_table = make_table(df_gene_altai_drugname_natural_mutTab, 'entry-gene-altai-drugname-natural-mutTab')
                    
                    gene_altai_drug_natural_bol = True

                else:
                    print('\n\ngene entered: ', genenames, 'drug entered: ', drugnames, ' altai_only enabled\n\n') 
                    gene_altai_drug_bol = True

                    
            elif len(natural_only) > 0 and natural_only[0] == 'disable': #7. gene_altai_natural_bol
                print('\n\ngene entered: ', genenames, ' altai_only and natural_only selected\n\n') 

                df_gene_altai_natural_drugTab = df_gene_altai_drugTab.loc[ df_gene_altai_drugTab['Natural source'] == 'True' ]
                df_gene_altai_natural_drugTab_table = make_table(df_gene_altai_natural_drugTab, 'entry-gene-altai-natural-drugTab')

                gene_altai_natural_genenames = df_gene_altai_natural_drugTab['Target Symbol'].tolist()
                df_gene_altai_natural_geneTab = df_gene_altai_geneTab.loc[ df_gene_altai_geneTab['Gene symbol'].isin(gene_altai_natural_genenames) ]
                df_gene_altai_natural_geneTab_table = make_table(df_gene_altai_natural_geneTab, 'entry-gene-altai-natural-geneTab')
                df_gene_altai_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_altai_natural_genenames) ]
                df_gene_altai_natural_mutTab_table = make_table(df_gene_altai_natural_mutTab, 'entry-gene-altai-natural-mutTab')

                gene_altai_natural_bol = True
                
            elif len(drugtarget_gene) > 0 and drugtarget_gene[0] == 'disable': # gene_altai_drugtarget_bol
                print('\n\ngene entered: ', genenames, 'altai_only and drug_targeted_gene are enabled\n\n')
                df_gene_altai_drugtarget_geneTab = df_gene_altai_geneTab.loc[df_gene_altai_geneTab['Gene symbol'].isin(drugdf_genenames) ]
                df_gene_altai_drutarget_geneTab_table = make_table(df_gene_altai_drugtarget_geneTab, 'entry-gene-altai-drugtarget-geneTab')
                gene_altai_drugtarget_genenames = df_gene_altai_drugtarget_geneTab['Gene symbol'].tolist()
                df_gene_altai_drugtarget_drugTab = drugdf.loc[drugdf['Target Symbol'].isin(gene_altai_drugtarget_genenames) ]
                df_gene_altai_drugtarget_drugTab_table = make_table(df_gene_altai_drugtarget_drugTab, 'entry-gene-altai-drugtarget-drugTab')

                df_gene_altai_drugtarget_mutTab = agedistdf.loc[agedistdf['Gene symbol'].isin(gene_altai_drugtarget_genenames) ]
                df_gene_altai_drugtarget_mutTab_table = make_table(df_gene_altai_drugtarget_mutTab, 'entry-gene-altai-drugtarget-mutTab')

                gene_altai_drugtarget_bol = True

            else:
                print('\n\ngene entered: ', genenames, ' altai_only enabled\n\n')
                gene_altai_bol = True

       
        elif drugnames: # 9. gene_drug_bol
            df_gene_drugname_drugTab = df_gene_drugTab.loc[ df_gene_drugTab['Drug Name'].isin(drugnames) ]
            df_gene_drugname_drugTab_table = make_table(df_gene_drugname_drugTab, 'entry-gene-drugname-drugTab')

            gene_drugname_genenames = df_gene_drugname_drugTab['Target Symbol'].tolist()
            df_gene_drugname_geneTab = df_gene_geneTab.loc[ df_gene_geneTab['Gene symbol'].isin(gene_drugname_genenames)]
            df_gene_drugname_geneTab_table = make_table(df_gene_drugname_geneTab, 'entry-gene-drugname-geneTab')
            df_gene_drugname_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_drugname_genenames)]
            df_gene_drugname_mutTab_table = make_table(df_gene_drugname_mutTab, 'entry-gene-drugname-mutTab')

            if len(natural_only) > 0 and natural_only[0] == 'disable': # 10. gene_drug_natural_bol
                print('\n\ngene entered: ', genenames, 'drug entered: ', drugnames, 'natural_only enabled\n\n') 
                df_gene_drugname_natural_drugTab = df_gene_drugname_drugTab.loc[ df_gene_drugname_drugTab['Natural source'] == 'True' ]
                df_gene_drugname_natural_drugTab_table = make_table( df_gene_drugname_natural_drugTab, 'entry-gene-drugname-natural-drugTab')

                gene_drugname_natural_genenames = df_gene_drugname_natural_drugTab['Target Symbol'].tolist()
                df_gene_drugname_natural_geneTab = df_gene_geneTab.loc[ df_gene_geneTab['Gene symbol'].isin(gene_drugname_natural_genenames) ]
                df_gene_drugname_natural_geneTab_table = make_table( df_gene_drugname_natural_geneTab, 'entry-gene-drugname-natural-geneTab')
                df_gene_drugname_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_drugname_natural_genenames) ]
                df_gene_drugname_natural_mutTab_table = make_table( df_gene_drugname_natural_mutTab, 'entry-gene-drugname-natural-mutTab')

                gene_drug_natural_bol = True

            else:
                print('\n\ngene entered: ', genenames, 'drug entered: ', drugnames, '\n\n')  
                gene_drug_bol = True

        elif len(natural_only) > 0 and natural_only[0] == 'disable': # 13. gene_natural_bol
            print('\n\ngene entered: ', genenames, 'natural_only is enabled\n\n')   
            df_gene_nautural_drugTab = df_gene_drugTab.loc[ df_gene_drugTab['Natural source'] == 'True' ]
            df_gene_natural_drugTab_table = make_table( df_gene_nautural_drugTab, 'entry-gene-natural-drugTab')

            gene_nautural_genenames = df_gene_nautural_drugTab['Target Symbol'].tolist()
            df_gene_nautural_geneTab = df_gene_geneTab.loc[ df_gene_geneTab['Gene symbol'].isin(gene_nautural_genenames) ]
            df_gene_natural_geneTab_table = make_table( df_gene_nautural_geneTab, 'entry-gene-natural-geneTab')
            df_gene_nautural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(gene_nautural_genenames) ]
            df_gene_natural_mutTab_table = make_table( df_gene_nautural_mutTab, 'entry-gene-natural-mutTab')

            gene_natural_bol = True
        
        elif len(drugtarget_gene) > 0 and drugtarget_gene[0] == 'disable': # 15. gene_drugtarget_bol
            print('\n\ngene entered: ', genenames, 'drugtarget_gene enabled\n\n') 
            

            df_gene_drugtarget_geneTab = df_gene_geneTab.loc[df_gene_geneTab['Gene symbol'].isin(drugdf_genenames)]
            df_gene_drugtarget_geneTab_table = make_table(df_gene_drugtarget_geneTab, 'entry-gene-drugtarget-geneTab')

            gene_drugtarget_genenames = df_gene_drugtarget_geneTab['Gene symbol'].tolist()
            df_gene_drugtarget_drugTab = drugdf.loc[drugdf['Target Symbol'].isin(gene_drugtarget_genenames)]
            df_gene_drugtarget_drugTab_table = make_table(df_gene_drugtarget_drugTab, 'entry-gene-drugtarget-drugTab')
            df_gene_drugtarget_mutTab = agedistdf.loc[agedistdf['Gene symbol'].isin(gene_drugtarget_genenames)]
            df_gene_drugtarget_mutTab_table = make_table(df_gene_drugtarget_mutTab, 'entry-gene-drugtarget-mutTab')
            gene_drugtarget_bol = True
        else: 
            print('\n\ngene entered: ', genenames, '\n\n') 
            gene_bol = True

    elif len(altai_only) > 0 and altai_only[0] == 'disable': #16. altai_bol
        df_altai_geneTab= ageingdf.loc[ ageingdf['Altai mutated'] == 'True' ]
        altai_genenames = df_altai_geneTab['Gene symbol'].tolist()
        df_altai_geneTab_table = make_table(df_altai_geneTab, 'entry-altai-geneTab')

        df_altai_drugTab = drugdf.loc[ drugdf['Target Symbol'].isin(altai_genenames) ]
        df_altai_drugTab_table = make_table(df_altai_drugTab, 'entry-altai-drugTab')
        df_altai_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(altai_genenames) ]
        df_altai_mutTab_table = make_table(df_altai_mutTab, 'entry-altai-mutTab')

        if drugnames: #17. altai_drug_bol
            df_altai_drugname_drugTab = df_altai_drugTab.loc[ df_altai_drugTab['Drug Name'].isin(drugnames) ]
            df_altai_drugname_drugTab_table = make_table(df_altai_drugname_drugTab, 'entry-altai-drugname-drugTab')

            altai_drugname_genenames = df_altai_drugname_drugTab['Target Symbol'].tolist()
            df_altai_drugname_geneTab = df_altai_geneTab.loc[ df_altai_geneTab['Gene symbol'].isin(altai_drugname_genenames) ]
            df_altai_drugname_geneTab_table = make_table(df_altai_drugname_geneTab, 'entry-altai-drugname-geneTab')
            df_altai_drugname_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(altai_drugname_genenames) ]
            df_altai_drugname_mutTab_table = make_table(df_altai_drugname_mutTab, 'entry-altai-drugname-mutTab')
        
            if len(natural_only) > 0 and natural_only[0] == 'disable': #18. altai_drug_natural_bol
                print('altai_only, drug and natural_only enabled')   
                df_altai_drugname_natural_drugTab = df_altai_drugname_drugTab.loc[ df_altai_drugname_drugTab['Natural source'] == 'True' ]
                df_altai_drugname_natural_drugTab_table = make_table(df_altai_drugname_natural_drugTab, 'entry-altai-drugname-natural-drugTab')

                altai_drugname_natural_genenames = df_altai_drugname_natural_drugTab['Target Symbol'].tolist()
                df_altai_drugname_natural_geneTab = df_altai_geneTab.loc[ df_altai_geneTab['Gene symbol'].isin(altai_drugname_natural_genenames) ]
                df_altai_drugname_natural_geneTab_table = make_table(df_altai_drugname_natural_geneTab, 'entry-altai-drugname-natural-geneTab')
                df_altai_drugname_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(altai_drugname_natural_genenames) ]
                df_altai_drugname_natural_mutTab_table = make_table(df_altai_drugname_natural_mutTab, 'entry-altai-drugname-natural-mutTab')

                altai_drug_natural_bol = True
            else:
                print('altai_only and drug enabled') 
                altai_drug_bol = True

        elif len(natural_only) > 0 and natural_only[0] == 'disable': #21. altai_natural_bol
            print('altai_only and natural_bol are enabled') 
            df_altai_natural_drugTab = df_altai_drugTab.loc[ df_altai_drugTab['Natural source'] == 'True' ]
            df_altai_natural_drugTab_table = make_table(df_altai_natural_drugTab, 'entry-altai-natural-drugTab')

            altai_natural_genenames = df_altai_natural_drugTab['Target Symbol'].tolist()
            df_altai_natural_geneTab = df_altai_geneTab.loc[ df_altai_geneTab['Gene symbol'].isin(altai_natural_genenames) ]
            df_altai_natural_geneTab_table = make_table(df_altai_natural_geneTab, 'entry-altai-natural-geneTab')
            df_altai_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(altai_natural_genenames) ]
            df_altai_natural_mutTab_table = make_table(df_altai_natural_mutTab, 'entry-altai-natural-mutTab')

            altai_natural_bol = True

        elif len(drugtarget_gene) > 0 and drugtarget_gene[0] == 'disable': # 30. altai_drugtarget_bol
            print('altaimut_only, drugtarget_gene enabled\n\n') 
            df_altai_drugtarget_drugTab = drugdf.loc[ drugdf['Target Symbol'].isin(altai_genenames) ]
            df_altai_drugtarget_drugTab_table = make_table(df_altai_drugtarget_drugTab, 'entry-altai-drugtarget-drugTab')

            altai_drugtarget_genenames = df_altai_drugtarget_drugTab['Target Symbol'].tolist()
            df_altai_drugtarget_geneTab = df_altai_geneTab.loc[ df_altai_geneTab['Gene symbol'].isin(altai_drugtarget_genenames) ]
            df_altai_drugtarget_geneTab_table = make_table(df_altai_drugtarget_geneTab, 'entry-altai-drugtarget-geneTab')
            df_altai_drugtarget_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(altai_drugtarget_genenames) ]
            df_altai_drugtarget_mutTab_table = make_table(df_altai_drugtarget_mutTab, 'entry-altai-drugtarget-mutTab')

            altai_drugtarget_bol = True

        else:
            print('\n\naltai_only enabled\n\n')  
            altai_bol = True

    elif drugnames: #23. drug_bol
        df_drug_drugTab = drugdf.loc[ drugdf['Drug Name'].isin(drugnames) ]
        df_drug_drugTab_table = make_table(df_drug_drugTab, 'entry-drug-drugTab')

        drug_genenames = df_drug_drugTab['Target Symbol'].tolist()
        df_drug_geneTab = ageingdf.loc[ ageingdf['Gene symbol'].isin(drug_genenames) ]
        df_drug_geneTab_table = make_table(df_drug_geneTab, 'entry-drug-geneTab')
        df_drug_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(drug_genenames) ]
        df_drug_mutTab_table = make_table(df_drug_mutTab, 'entry-drug-mutTab')

        if len(natural_only) > 0 and natural_only[0] == 'disable': #24. drug_natural_bol
            print('drug entered: ', drugnames, ' natural_only enabled') 
            df_drug_natural_drugTab= df_drug_drugTab.loc[ df_drug_drugTab['Natural source'] == 'True' ]
            df_drug_natural_drugTab_table = make_table(df_drug_natural_drugTab, 'entry-drug-natural-drugTab')

            drug_natural_genenames = df_drug_natural_drugTab['Target Symbol'].tolist()
            df_drug_natural_geneTab = ageingdf.loc[ ageingdf['Gene symbol'].isin(drug_natural_genenames) ]
            df_drug_natural_geneTab_table = make_table(df_drug_natural_geneTab, 'entry-drug-natural-geneTab')
            df_drug_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(drug_natural_genenames) ]
            df_drug_natural_mutTab_table = make_table(df_drug_natural_mutTab, 'entry-drug-natural-mutTab')

            drug_natural_bol = True   

        else:
            print('drug entered: ', drugnames)  
            drug_bol = True
            
    elif len(natural_only) > 0 and natural_only[0] == 'disable': #27 natural_bol
        print('natural_only enabled')  

        df_natural_drugTab= drugdf.loc[ drugdf ['Natural source'] == 'True' ]
        df_natural_drugTba_table = make_table(df_natural_drugTab, 'entry-natrual-drugTab')

        natural_genenames = df_natural_drugTab['Target Symbol'].tolist()       
        df_natural_geneTab = ageingdf.loc[ ageingdf['Gene symbol'].isin(natural_genenames)]
        df_natural_geneTab_table = make_table(df_natural_geneTab, 'entry-natural-geneTab')
        df_natural_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(natural_genenames)]
        df_natural_mutTab_table = make_table(df_natural_mutTab, 'entry-natural-mutTab')

        
        print('natural_bol enabled')  
        natural_bol = True

    elif len(drugtarget_gene) > 0 and drugtarget_gene[0] == 'disable': # 29. drugtarget_bol
            print('\n\ndrugtarget_gene enabled\n\n') 
            drugtarget_bol = True

            df_drugtarget_geneTab = ageingdf.loc[ ageingdf['Gene symbol'].isin(drugdf_genenames) ]
            df_drugtarget_geneTab_table = make_table(df_drugtarget_geneTab, 'entry-drugtarget-geneTab')
            df_drugtarget_mutTab = agedistdf.loc[ agedistdf['Gene symbol'].isin(drugdf_genenames) ]
            df_drugtarget_mutTab_table = make_table(df_drugtarget_mutTab, 'entry-drugtarget-mutTab')


    else:
        pass
    
        ####################################################################################################################################


    
    if gene_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_geneTab_table ], label='Selected ageing genes', id='entry-gene-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugTab_table ], label='Drugs targeted selected ageing genes', id='entry-gene-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])

    elif gene_altai_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_altai_geneTab_table ], label='Selected altai mutated ageing genes', id='entry-gene-altai-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugTab_table ], label='Drugs targeted selected altai mutated ageing genes', id='entry-gene-altai-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-altai-mutTab', style={'margin-top':'0%'}),                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])
            
    elif gene_altai_drug_bol: 
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_altai_drugname_geneTab_table ], label='Selected altai mutated ageing genes targeted by selected drugs', id='entry_gene_altai_drugname_geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugname_drugTab_table ], label='Selected drugs targeted altai mutated ageing genes', id='entry-gene-altai-drugname-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugname_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-altai-drugname_mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])
        
    elif gene_altai_drug_natural_bol:
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_altai_drugname_natural_geneTab_table ], label='Selected altai mutated ageing genes targeted by selected natural drugs', id='entry-gene-altai-drugname-natural-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugname_natural_drugTab_table ], label='Selected natural drug targeted altai mutated ageing genes', id='entry-gene-altai-drugname-natural-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugname_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-altai-drugname-natural-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})

                ])

    elif gene_altai_natural_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_altai_natural_geneTab_table ], label='Selected altai mutated ageing genes', id='entry-gene-altai-natural-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_natural_drugTab_table ], label='Selected natural drug targeted altai mutated ageing genes', id='entry-gene-altai-natural-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-altai-natural-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])

    elif gene_altai_drugtarget_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_altai_drutarget_geneTab_table ], label='Targetable selected altai mutated ageing genes', id='entry-gene-altai-drugtarget-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugtarget_drugTab_table ], label='Selected natural drug targeted altai mutated ageing genes', id='entry-gene-altai-drugtarget-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_altai_drugtarget_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-altai-drugtarget-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])
    elif gene_drug_bol:
        print('gene entered: ', genenames, 'drug entered: ', drugnames)
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_drugname_geneTab_table ], label='Selected drugs targeted selected ageing genes', id='entry-gene-drugname-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugname_drugTab_table ], label='Selected drugs targeted selected genes', id='entry-gene-drugname-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugname_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-drugname-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])
    
        
    elif gene_drug_natural_bol:
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_drugname_natural_geneTab_table ], label='Selected ageing genes', id='entry-gene-drugname-natural-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugname_natural_drugTab_table ], label='Selected natural drug targeted ageing genes', id='entry-gene-drugname-natural-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugname_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-drugname-natural-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})

                ])

           
    elif gene_natural_bol:
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_natural_geneTab_table ], label='Natural drugs targeted selected ageing genes', id='entry-gene-natural-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_natural_drugTab_table ], label='Selected natural drugs targeted selected genes', id='entry-gene-natural-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-natural-mutTab', style={'margin-top':'0%'}),
                    dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])
    elif gene_drugtarget_bol:
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
                [ 
                    dcc.Tab([ df_gene_drugtarget_geneTab_table ], label='Targetable selected ageing genes', id='entry-gene-drugtarget-geneTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugtarget_drugTab_table ], label='Selected drugs targeted selected genes', id='entry-gene-drugtarget-drugTab', style={'margin-top':'0%'}),
                    dcc.Tab([ df_gene_drugtarget_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-gene-drugtarget-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
                ])
    
    elif altai_bol:
        print('altai_only enabled')
        minwidth=['Selected gene\'s mutation age distribution']
        
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_altai_geneTab_table ], label='All altai mutated genes', id='entry-altai-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugTab_table ], label='Drugs targeted altai mutated ageing genes', id='entry-altai-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-altai-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
        
    elif altai_drug_bol:
        print('altai_only enabled', 'drug entered: ', drugnames)
        minwidth=['Selected gene\'s mutation age distribution']
        
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_altai_drugname_geneTab_table ], label='Selected drugs target altai mutated ageing genes', id='entry-altai-drugname-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugname_drugTab_table ], label='Selected drugs', id='entry-altai-drugname-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugname_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-altai-drugname-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ],  
            mobile_breakpoint=0,
            style={'height':'50px','margin-top':'0px','margin-botom':'0px', 'width':'100%','overflow-x':'auto', 'minWidth':minwidth} 
            )
    
    elif altai_drug_natural_bol:
        print('altai_only enabled', 'natural_only enabled', 'drug entered: ', drugnames)
        minwidth=['Selected gene\'s mutation age distribution']
        
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_altai_drugname_natural_geneTab_table ], label='Selected natural drugs target altai mutated ageing genes', id='entry-altai-drugname-natural-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugname_natural_drugTab_table ], label='Selected natural drugs', id='entry-altai-drugname-natural-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugname_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-altai-drugname-natural-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
        
    elif altai_natural_bol:
        print('altai_only enabled', 'natural_only enabled')
        minwidth=['Selected gene\'s mutation age distribution']
        
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_altai_natural_geneTab_table ], label='Selected altai mutated genes', id='entry-altai-natural-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_natural_drugTab_table ], label='Altai mutated genes -> natural drug', id='entry-altai-natural-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-altai-natural-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])

    elif drug_natural_bol:
        print('drug entered: ', drugnames, ' natural_only enabled') 
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_drug_natural_geneTab_table ], label='Natural drug targeted genes', id='entry-drug-natural-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_drug_natural_drugTab_table ], label='Selected natural drug targets', id='entry-drug-natural-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_drug_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-drug-natural-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
    elif drug_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_drug_geneTab_table ], label='Selected drug targeted ageing genes', id='entry-drug-geneTab'),
                dcc.Tab([ df_drug_drugTab_table ], label='Selected drugs', id='entry-drug-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_drug_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-drug-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
   

        
    elif natural_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_natural_geneTab_table ], label='Selected genes', id='entry-natural-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_natural_drugTba_table ], label='Natural drug targets', id='entry-natural-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_natural_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-natural-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
        

    elif altai_drugtarget_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_altai_drugtarget_geneTab_table ], label='Targetable altai mutated ageing genes', id='entry-altai-drugtarget-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugtarget_drugTab_table ], label='Targetable altai mutated ageing gene targets', id='entry-altai-drugtarget-drugTab', style={'margin-top':'0%'}),
                dcc.Tab([ df_altai_drugtarget_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-altai-drugtarget-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
       
    elif drugtarget_bol:
        minwidth=['Selected gene\'s mutation age distribution']
        out=dcc.Tabs( 
            [ 
                dcc.Tab([ df_drugtarget_geneTab_table ], label='Targetable ageing genes', id='entry-drugtarget-geneTab', style={'margin-top':'0%'}),
                dcc.Tab([ drugdf_table ], label='All drug targets', id='all-drugs', style={'margin-top':'0%'}),
                dcc.Tab([ df_drugtarget_mutTab_table ], label='Selected gene\'s mutation age distribution', id='entry-drugtarget-mutTab', style={'margin-top':'0%'}),
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'})
            ])
       



    else:
        print('All-data')
        minwidth=['Selected gene\'s mutation age distribution']

        out=dcc.Tabs( 
            [   
                dcc.Tab([ readme ], label='README', id='readme-content', style={'margin-top':'0%'}),
                dcc.Tab([ ageingdf_table ], label='All ageing genes', id='all-agegenes', style={'margin-top':'0%'}),
                dcc.Tab([ drugdf_table ], label='Drug targets', id='all-drugs', style={'margin-top':'0%'}),
                dcc.Tab([ agedistdf_table ], label='Gene mutation age distribution', id='all-agedist-mutTab', style={'margin-top':'0%'})
            ])
        
    return out

######################################################################################


@dashapp.callback(
        Output('navbar-collapse', 'is_open'),
        [Input('navbar-toggler', 'n_clicks')],
        [State('navbar-collapse', 'is_open')])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

