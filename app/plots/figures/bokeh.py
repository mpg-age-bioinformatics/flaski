import pandas as pd
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.sampledata.iris import flowers

# Load the Iris Data Set
#iris_df = pd.read_csv("iris.data", 
#    names=["Sepal Length", "Sepal Width", "Petal Length", "Petal Width", "Species"])
#feature_names = iris_df.columns[0:-1].values.tolist()

# Create the main plot
def create_figure():
    # colormap = {'setosa': 'red', 'versicolor': 'green', 'virginica': 'blue'}
    # colors = [colormap[x] for x in flowers['species']]

    # p = figure(title = "Iris Morphology")
    # p.xaxis.axis_label = 'Petal Length'
    # p.yaxis.axis_label = 'Petal Width'

    # source = ColumnDataSource( data=dict(
    # petal_length=list(flowers["petal_length"]),
    # petal_width=list(flowers["petal_width"]),
    # colors=colors ))

    # TOOLTIPS = [
    # ("index", "$index"),
    # ("petal_length", "$petal_length"),
    # ("petal_width", "$petal_width")]

    # print(source)


    # p.circle( "petal_length", "petal_width", color="colors", fill_alpha=0.2, size=10, source=source, tooltips=TOOLTIPS )

    source = ColumnDataSource(data=dict(
    x=[1, 2, 3, 4, 5],
    y=[2, 5, 8, 2, 7],
    desc=['A', 'b', 'C', 'd', 'E'],
    ))

    TOOLTIPS = [
        ("index", "$index"),
        ("(x,y)", "($x, $y)"),
        ("desc", "@desc"),
    ]

    p = figure(plot_width=400, plot_height=400, tooltips=TOOLTIPS,
            title="Mouse over the dots")

    p.circle('x', 'y', size=20, source=source)


    return p