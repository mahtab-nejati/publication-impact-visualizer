from cgitb import text
import io
import base64
import json
from datetime import date
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.models import (HoverTool, FileInput, Slider,
                          RangeSlider, CheckboxGroup,
                          Select, Div,
                          ColumnDataSource,
                          DataTable, TableColumn)
from pandas import options
from processor import process_data

SCRAPER_LINK = 'https://github.com/mahtab-nejati/google-scholar-scraper'
REPO_LINK = 'https://github.com/mahtab-nejati/publication-impact-visualizer'
AUTHORID = ''
AUTHORNAME = ''
DATA = {}
EARLIEST = 1970
LATEST = date.today().year
TIMESPAN = 3
PROPER_YEARS = True
SAMPLE_AUTHORS = {'Choose one': '',
                  'Jimmy Lin': '0EWw1z8AAAAJ',
                  #   'Some Other Guy': 'kukA0LcAAAAJ',  # TODO: Fix name
                  'Geoffrey Hinton': 'JicYPdAAAAAJ',
                  'Yann LeCun': 'WLN3QrAAAAAJ',
                  'Charles L. A. Clarke': 'TkVleDIAAAAJ',
                  'Shane McIntosh': 'FxUqGoUAAAAJ',
                  'Jian Zhao': '5v0elikAAAAJ'}

AUTHOR = []
DOTS = []
LINES = []

header = f"""
    <h1>CS848: The art and science of empirical computer science</h1>
    <h3>The Visualization Project</h3>
    <h4>By Mattie Nejati,
        <span>Code available <a target='code' href='{REPO_LINK}'>on GitHub</a></span>
    </h4>
"""
header = Div(text=header, sizing_mode='stretch_width')

instructions = f"""
    <h2>Instructions:</h2>
    <div>
        <h3>To visualize data from a sample author:</h3>
        <ol>
            <li>Select a sample author form the dropdown.</li>
            <li>Use the sliders and checkbox below to tweak your visualizaiton.</li>
        </ol>
    </div>
    <div>
        <h3>To visualize data from your selected author:</h3>
        <ol>
            <li>Scrape the data for your author of interest using the scraper <a target='scraper' href="{SCRAPER_LINK}">at this link</a>.</li>
            <li>Upload the .json file to the file input field below.</li>
            <li>Use the sliders and checkbox below to tweak your visualizaiton.</li>
        </ol>
    </div>
"""
instructions = Div(text=instructions, sizing_mode='scale_both')


def update_visualization():
    global AUTHORNAME, AUTHOR, DOTS, LINES
    if DATA:
        AUTHORNAME = DATA['name']
    else:
        AUTHORNAME = ''
    AUTHOR, DOTS, LINES = process_data(
        DATA, TIMESPAN, EARLIEST, LATEST, PROPER_YEARS)
    author_source.data = ColumnDataSource.from_df(AUTHOR)
    dots_source.data = ColumnDataSource.from_df(DOTS)
    lines_source.data = ColumnDataSource.from_df(LINES)
    plot.title.text = f'The number of citations after {TIMESPAN} years of publication (C{TIMESPAN}){" (Author: "+AUTHORNAME+")" if AUTHORNAME else ""}'


def visualize_sample(attr, old, new):
    global DATA, AUTHORID
    AUTHORID = SAMPLE_AUTHORS[new]
    if AUTHORID:
        with open(f'./data/{AUTHORID}.json', 'r') as of:
            DATA = json.load(of)
    else:
        DATA = {}
    update_visualization()


def upload_data(attr, old, new):
    decoded = base64.b64decode(new)
    f = io.BytesIO(decoded)
    global DATA, AUTHORID
    DATA = json.load(f)
    AUTHORID = DATA['authorID']
    update_visualization()


def update_range(attr, old, new):
    global EARLIEST, LATEST
    EARLIEST, LATEST = new
    update_visualization()


def update_timespan(attr, old, new):
    global TIMESPAN
    TIMESPAN = new
    update_visualization()
    plot.tools[-1].tooltips = [('Year', '@year'),
                               (f'C{TIMESPAN}', '@citations_in_timespan'),
                               ('Count', '@papers_count'),
                               ('Papers', '@tooltip_text{safe}')]


def update_xticks(attr, old, new):
    global PROPER_YEARS, DOTS, LINES
    PROPER_YEARS = len(new) > 0
    update_visualization()
    plot.xaxis.axis_label = f'Publication Year{"" if PROPER_YEARS else " over Author Career"}'


sample_data_select = Select(title="Select sample data",
                            value='Choose one',
                            options=list(SAMPLE_AUTHORS.keys()))
sample_data_select.on_change('value', visualize_sample)

data_file_title = Div(text="Upload your data file")
data_file_input = FileInput(accept=".json")
data_file_input.on_change('value', upload_data)
data_file = column(data_file_title, data_file_input)


years_range_slider = RangeSlider(title="Papers published between (years)",
                                 start=EARLIEST,
                                 end=LATEST,
                                 step=1,
                                 value=(EARLIEST, LATEST))
years_range_slider.on_change('value_throttled', update_range)

timespan_slider = Slider(start=1, end=20, value=TIMESPAN,
                         step=1, title="Citation timespan (years)")
timespan_slider.on_change('value_throttled', update_timespan)

proper_year_checkbox = CheckboxGroup(
    labels=['X ticks in proper year of publication'], active=[0])
proper_year_checkbox.on_change('active', update_xticks)


inputs = column(row(sample_data_select,
                    data_file),
                years_range_slider,
                timespan_slider,
                proper_year_checkbox)

lines_source = ColumnDataSource()
dots_source = ColumnDataSource()
author_source = ColumnDataSource()


plot = figure(title=f'The number of citations after {TIMESPAN} years of publication (C{TIMESPAN})',
              x_axis_label=f'Publication Year{"" if PROPER_YEARS else " over Author Career"}',
              y_axis_label=f'C{TIMESPAN}',
              sizing_mode='stretch_width',
              tools='box_zoom,pan,wheel_zoom,xwheel_pan,ywheel_pan,reset,save')

plot_lines = plot.vbar(x='view_year',
                       top='max_citations_in_timespan', source=lines_source,
                       bottom=0, width=0, line_alpha=1, fill_alpha=1)

plot_circles = plot.circle(x='view_year',
                           y='citations_in_timespan',
                           source=dots_source,
                           line_alpha=1, line_width=0.5,
                           fill_color="#e56b6f", fill_alpha=0.6, size=10,
                           hover_fill_color="#8e9aaf")

plot.add_tools(HoverTool(tooltips=[('Year', '@year'),
                                   (f'C{TIMESPAN}', '@citations_in_timespan'),
                                   ('Count', '@papers_count'),
                                   ('Papers', '@tooltip_text{safe}')], mode='mouse'))

summary_title = """
    <h2>About Author</h2>
"""
summary_title = Div(text=summary_title, sizing_mode='scale_both')
cols = [TableColumn(field='keys', title='Attribute'),
        TableColumn(field='values', title='Value')]
table = DataTable(source=author_source, columns=cols,
                  index_position=None, header_row=False,
                  autosize_mode='fit_columns', sizing_mode='scale_both')

summary = column(summary_title, table)

# curdoc().theme = 'dark_minimal'
curdoc().title = "CS848 Visualization Project"
curdoc().add_root(
    row(column(children=[header, row([column([instructions, inputs, summary]), plot])], sizing_mode='stretch_width')))
