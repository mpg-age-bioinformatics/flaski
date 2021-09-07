import plotly.graph_objects as go

def make_figure(df):
    fig = go.Figure( )
    fig.update_layout(  width=600, height=600)
    fig.add_trace(go.Scatter(x=df["x"].tolist(), y=df["y"].tolist() ))
    fig.update_layout(
            title={
                'text': "Demo plotly title",
                'xanchor': 'left',
                'yanchor': 'top' ,
                "font": {"size": 25, "color":"black"  } } )
    return fig