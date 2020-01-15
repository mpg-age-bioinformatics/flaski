from flask import Flask, render_template, request
from bokeh.embed import components
from app import app

from app.plots.figures.bokeh import create_figure

@app.route('/bokeh', methods=['GET', 'POST'])
def bokeh():
    plots = []
    # Create the plot
    plot = create_figure()
    # Embed plot into HTML via Flask Render
    script, div = components(plot)
    plots.append(components(plot))
    return render_template("/iris_index1.html", the_script=script, the_div=div)