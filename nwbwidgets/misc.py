import matplotlib.pyplot as plt
import numpy as np
from pynwb.misc import AnnotationSeries
from ipywidgets import widgets, fixed
from matplotlib import cm
from .controllers import make_time_controller, make_trace_controller
from .utils.units import get_spike_times, get_max_spike_time, get_min_spike_time

def show_annotations(annotations: AnnotationSeries, **kwargs):
    fig, ax = plt.subplots()
    ax.eventplot(annotations.timestamps, **kwargs)
    ax.set_xlabel('time (s)')
    return fig





def show_session_raster(units, time_window, units_window, cmap_name='rainbow'):
    num_units = units_window[1] - units_window[0] + 1
    unit_inds = np.arange(units_window[0], units_window[1] + 1)

    reduced_spike_times = [get_spike_times(units, unit, time_window) for unit in unit_inds]

    # create colormap to map the unit's closest electrode to color
    cmap = cm.get_cmap(cmap_name, num_units)
    colors = cmap(unit_inds - min(unit_inds))
    # plot spike times for each unit
    fig, ax = plt.subplots(1, 1)
    ax.figure.set_size_inches(12, 6)
    ax.eventplot(reduced_spike_times, color=colors, lineoffsets=unit_inds)
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Unit #')
    ax.set_xlim(time_window)
    ax.set_ylim(np.array(units_window))

    return fig


def raster_widget(node):
    tmin = get_min_spike_time(node)
    tmax = get_max_spike_time(node)

    time_window_controller = make_time_controller(tmin, tmax)
    unit_controller = make_trace_controller(len(node['spike_times'].data)-1, (0, 100))

    controls = {
        'units': fixed(node),
        'time_window': time_window_controller.children[0],
        'units_window': unit_controller.children[0],
    }

    out_fig = widgets.interactive_output(show_session_raster, controls)

    control_widgets = widgets.HBox(children=(time_window_controller, unit_controller))
    vbox = widgets.VBox(children=[control_widgets, out_fig])
    return vbox


def show_decomposition_series(node, **kwargs):
    # Use Rendering... as a placeholder
    ntabs = 2
    children = [widgets.HTML('Rendering...') for _ in range(ntabs)]

    def on_selected_index(change):
        # Click on Traces Tab
        if change.new == 1 and isinstance(change.owner.children[1], widgets.HTML):
            widget_box = show_decomposition_traces(node)
            children[1] = widget_box
            change.owner.children = children

    field_lay = widgets.Layout(max_height='40px', max_width='500px',
                               min_height='30px', min_width='130px')
    vbox = []
    for key, val in node.fields.items():
        lbl_key = widgets.Label(key+':', layout=field_lay)
        lbl_val = widgets.Label(str(val), layout=field_lay)
        vbox.append(widgets.HBox(children=[lbl_key, lbl_val]))
        #vbox.append(widgets.Text(value=repr(value), description=key, disabled=True))
    children[0] = widgets.VBox(vbox)

    tab_nest = widgets.Tab()
    tab_nest.children = children
    tab_nest.set_title(0, 'Fields')
    tab_nest.set_title(1, 'Traces')
    tab_nest.observe(on_selected_index, names='selected_index')
    return tab_nest


def show_decomposition_traces(node):
    # Produce figure
    def control_plot(x0, x1, ch0, ch1):
        fig, ax = plt.subplots(nrows=nBands, ncols=1, sharex=True, figsize=(14, 7))
        for bd in range(nBands):
            data = node.data[x0:x1, ch0:ch1+1, bd]
            xx = np.arange(x0, x1)
            mu_array = np.mean(data, 0)
            sd_array = np.std(data, 0)
            offset = np.mean(sd_array)*5
            yticks = [i*offset for i in range(ch1+1-ch0)]
            for i in range(ch1+1-ch0):
                ax[bd].plot(xx, data[:, i] - mu_array[i] + yticks[i])
            ax[bd].set_ylabel('Ch #', fontsize=20)
            ax[bd].set_yticks(yticks)
            ax[bd].set_yticklabels([str(i) for i in range(ch0, ch1+1)])
            ax[bd].tick_params(axis='both', which='major', labelsize=16)
        ax[bd].set_xlabel('Time [ms]', fontsize=20)
        return fig

    nSamples = node.data.shape[0]
    nChannels = node.data.shape[1]
    nBands = node.data.shape[2]
    fs = node.rate

    # Controls
    field_lay = widgets.Layout(max_height='40px', max_width='100px',
                               min_height='30px', min_width='70px')
    x0 = widgets.BoundedIntText(value=0, min=0, max=int(1000*nSamples/fs-100),
                                layout=field_lay)
    x1 = widgets.BoundedIntText(value=10000, min=100, max=int(1000*nSamples/fs),
                                layout=field_lay)
    ch0 = widgets.BoundedIntText(value=0, min=0, max=int(nChannels-1), layout=field_lay)
    ch1 = widgets.BoundedIntText(value=10, min=0, max=int(nChannels-1), layout=field_lay)

    controls = {
        'x0': x0,
        'x1': x1,
        'ch0': ch0,
        'ch1': ch1
    }
    out_fig = widgets.interactive_output(control_plot, controls)

    # Assemble layout box
    lbl_x = widgets.Label('Time [ms]:', layout=field_lay)
    lbl_ch = widgets.Label('Ch #:', layout=field_lay)
    lbl_blank = widgets.Label('    ', layout=field_lay)
    hbox0 = widgets.HBox(children=[lbl_x, x0, x1, lbl_blank, lbl_ch, ch0, ch1])
    vbox = widgets.VBox(children=[hbox0, out_fig])
    return vbox
