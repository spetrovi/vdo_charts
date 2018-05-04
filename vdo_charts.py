from random import randint
import numpy as np
from html import *
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.stats import linregress
import json
import os


def create_button(name):
    button = read_file('templates/button.js')
    button = str(name + "_button").join(button.split("XXX_ID_XXX"))
    button = str(name + '''.yAxis[0].update({ type: types[type] });''').join(
        button.split("XXX_chart_button_XXX"))
    return button


def read_file(name):
    f = open(name, 'r')
    str_ = f.read()
    f.close()
    return str_

# compute speed from difference in logic blocks between intervals
# logic blocks are 4k blocks
def speed(logic_blocks_used, interval=60):
    speed = []
    for i, item in enumerate(logic_blocks_used):
        if i > 0:
            speed.append((item - logic_blocks_used[i-1])/1024*4/interval)
        else:
            speed.append(item/1024*4/interval)
    return speed

# cumulative average speed
def rolling_avg_speed(speed):
    rolling_avg_speed = []
    for i in range(1,len(speed)):
        rolling_avg_speed.append(round(np.average(speed[:i]),2))
    return rolling_avg_speed

# curve smoothing and interpolation
# window size must be odd 
def smooth_curve(y, offset, window_size = 101, poly_order = 3):
    bins_xx = [x for x in range(offset, len(y)+offset)]

    #create normalised x axis
    xx = np.linspace(min(bins_xx),max(bins_xx), 600)

    # interpolate + smooth
    itp = interp1d(bins_xx, y)
    yy_sg = savgol_filter(itp(xx), window_size, poly_order)

    yy_sg = map(lambda x: round(x, 2), yy_sg)
    
    return list(xx), list(yy_sg)
    
# computed space saving for given interval
# logic_blocks is number of stored logical blocks (4k blocks)
# k blocks is number of 1K-blocks (physical)
def space_saving(logic_blocks, k_blocks, interval):
    saved = []
    for i in range(len(logic_blocks)):
        if i % interval == 0:
            logic_blocks_diff = (logic_blocks[i] - logic_blocks[i-interval])*4
            k_blocks_diff = float(k_blocks[i] - k_blocks[i-interval])
            if logic_blocks_diff != 0:
                saved.append(round(1-(k_blocks_diff/logic_blocks_diff), 2))
            else:
                saved.append(round(1-(k_blocks_diff/1), 2))
    return saved
        
# generate html document with charts
class Report:
    def __init__(self, dest, filename):
        self.dest = dest
        self.vdostats_parsed = json.loads(read_file(filename))
        
        # compute additional values here
        self.vdostats_parsed['speed'] = speed(self.vdostats_parsed['logical blocks used'])
        self.vdostats_parsed['computed space saving'] = space_saving(self.vdostats_parsed['logical blocks used'], self.vdostats_parsed['1K-blocks used'], 10)
        self.vdostats_parsed['rolling avg speed'] = rolling_avg_speed(self.vdostats_parsed['speed'])
        self.vdostats_parsed['physical data blocks used'] = map(lambda x, y: x-y, self.vdostats_parsed['data blocks used'], self.vdostats_parsed['overhead blocks used'])

        # create and add plots here
        self.plots = []
        self.plots.append(self.generate_vdo_plot(display=['logical blocks used', 'physical data blocks used'], ylabel='volume [GiB]', title='Evolution of VDO volume'))
        self.plots.append(self.generate_vdo_plot(display=['saving percent'], ylabel='physical space saving [%]', title='Progression of space saving'))
        self.plots.append(self.generate_vdo_plot(display=['rolling avg speed'], ylabel='speed [MiB/s]', title='Rolling average speed'))
        self.plots.append(self.generate_vdo_plot(display=['computed space saving'], ylabel='physical space saving [%]', title='Space saving of data written in last 10min', offset=3, interval=6))
        self.plots.append(self.generate_vdo_plot(display=['speed'], ylabel='speed [MiB/s]', title='speed', smooth=True))
        self.report = self.make_report()

    def save(self):
        f = open(self.dest + '/index.html', 'w+')
        f.write(str(self.report))
        f.close()

    # create and save plots as js source
    
    # display: properties to display
    # ylabel: label the Y axis
    # title: title for this chart
    # offset: remove first X values
    # smooth: interpolate and smooth curve
    # interval: give interval working interval to correct X axis ticks
    def generate_vdo_plot(self, display, ylabel, title, offset=30, smooth=False, interval=60):
        self.data = self.vdostats_parsed
        template = read_file('templates/vdo_template.js')
        line_template = read_file('templates/line_template.js')

        # ID is name of chart in js source and html document
        ID = 'vdostats_' + str(randint(0, 1000))
        template_cur = ID.join(template.split('XXX_NAME_XXX'))
        template_cur = title.join(
            template_cur.split('XXX_TITLE_XXX'))
    


        # x axis
        x_axis = [x for x in range(offset, len(self.data[display[0]]))]
        
        # y axis
        for key, y in self.data.items():
            if key in display:
                
                # clip values
                y = y [offset:]

                # name line
                line = line_template
                line = key.join(line.split('XXX_NAME_XXX'))

                # convert units, create actual curve
                if y[-1] > (1024*1024) and key != 'speed':
                    y_curve = map(lambda x: round(float(x)/(1024*1024)*4, 2), y)
                elif y[-1] < 1:
                    y_curve = map(lambda x: round(x*100, 2), y)
                else:
                    y_curve = y

                if smooth:
                    x_axis, y_curve = smooth_curve(y_curve, offset)

                # paste line to template
                line_cur = str(y_curve).join(line.split('XXX_DATA_XXX'))
                template_cur = (
                    line_cur+'XXX_LINE_XXX').join(template_cur.split('XXX_LINE_XXX'))
                
                
        template_cur = ''.join(template_cur.split('XXX_LINE_XXX'))
        
        # ticks for chart
        ticks = map(lambda x: round(float(x)/interval, 2), x_axis)

        template_cur = str(ticks).join(template_cur.split('XXX_BINS_XXX'))
        template_cur = ylabel.join(template_cur.split('XXX_YLABEL_XXX'))




        try:
            f = open(self.dest + '/' + ID+'.js', 'w')
        except IOError as e:
            if not os.path.isdir("report"):
                os.mkdir("report")
                f = open(self.dest + '/' + ID + '.js', 'w')
            else:
                raise e
        f.write(template_cur)
        f.close()

        return ID


    # create html document
    def make_report(self):
        r = HTML()
        r.html
        r.head
        r.title('vdostats')
        r.script('', type='text/javascript',
                 src='http://code.jquery.com/jquery-1.9.1.js')
        r += '</head>'
        r.body
        r.script('', src="http://code.highcharts.com/highcharts.js")
        r.script('', src="http://code.highcharts.com/highcharts-more.js")
        r.script('', src="http://code.highcharts.com/modules/exporting.js")
        r.script(
            '', src="//rawgithub.com/phpepe/highcharts-regression/master/highcharts-regression.js")
        r.script('', src="https://code.highcharts.com/highcharts-3d.js")
        r.link(rel="stylesheet", type="text/css", href="stylesheet.css")
        r.br
        r.font(size='3')
        r.style
        r += '''table {
	    width:20%;
	    }
	    table, th, td{
	    border: 1px solid black;
	    border-collapse: collapse;
	    font-size: 14px;
	    }
	    th, td{
	    padding: 5px;
	    text-align: left;
	    }
	    table#t01 tr:nth-child(even) {
	    background-color: #eee;
	    }
	    table#t01 tr:nth-child(odd) {
	    background-color:#fff;
	    }
	    table#t01 th	{
	    background-color: white;
	    color: black;
	    })\n</style>'''

        r.dt
        r.strong('vdostats')
        r.br
        r.br
        
        # include js source
        for plot in self.plots:
            r.script('', type='text/javascript',
                     src=plot + '.js')

        # place charts
        table = r.table
        tr = table.tr

        for i, plot in enumerate(self.plots):
            tr.td.div(id=plot, align='left')
            if i % 2 == 1:
                tr = table.tr
        return r


r = Report('report', 'vdostats_parsed_jirka.json')
r.save()
