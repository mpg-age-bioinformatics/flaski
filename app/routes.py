from flask import render_template, Flask, Response, request, url_for, redirect
from app import app
from app.model import InputForm

import os
import io
import sys
import random

import matplotlib
matplotlib.use('agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import mpld3

import base64

@app.route("/plot_png", methods=['GET', 'POST'])
def plot_png(num_x_points=50, title="scatter plot"):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f

    """
    form = InputForm(request.form)

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(num_x_points)
    axis.scatter(x_points, [random.randint(1, 30) for x in x_points])
    axis.set_title(title, fontsize=40)
    axis.set_xlabel("x")
    output = io.BytesIO()
    FigureCanvasSVG(fig).print_svg(output)
    response=Response(output.getvalue(), mimetype="image/png")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/scatterplot.svg")
def plot_svg(num_x_points=2):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(num_x_points)
    axis.scatter(x_points, [random.randint(1, 30) for x in x_points])
    axis.set_title("test", fontsize=40)
    axis.set_xlabel("x")
    output = io.BytesIO()
    FigureCanvasSVG(fig).print_svg(output)
    return Response(output.getvalue(), mimetype="image/svg+xml")

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = InputForm(request.form)

    if request.method == 'POST':
        sometext="post"
        title=request.form['title']

        fig = Figure()
        x_points = range(50)
        plt.scatter(x_points, [random.randint(1, 30) for x in x_points])
        plt.title(title, fontsize=40)

        figfile = io.BytesIO()
        plt.savefig(figfile, format='png')
        plt.close()
        figfile.seek(0)  # rewind to beginning of file
        figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')

    else:
        
        title=None
        sometext="get"
        figure_url=None

    return render_template('index.html', figure_url=figure_url, form=form, sometext=sometext, title=title)