# vdo_charts
Simple tool for quick ploting from dictionary to highcharts with focus on VDO statistics

You need to provide dictionary with your data (e.g. {X:[1,2,3,4,5], Y:[5,4,3,2,1]}).
You can compute some additional values and add it to the dictionary.
Add plots by adding the ID of your chart to the list 'plots', these IDs will be referenced in the html document.

To generate new charts, use generate_vdo_plot method with these parameters:
* display: properties to display
* ylabel: label the Y axis
* title: title for this chart
* offset: remove first X values
* smooth: interpolate and smooth curve
* interval: give interval working interval to correct X axis ticks
 
 If you use smoothing and your curve happens to be too smooth, lower the poly_order argument

