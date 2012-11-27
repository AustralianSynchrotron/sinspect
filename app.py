import os
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
import numpy as np
from enable.api import Component, ComponentEditor
from traits.api import Str, Bool, Enum, List, HasTraits, Instance, Button, \
    HTML, on_trait_change
from traitsui.api import View, Group, HGroup, VGroup, HSplit, \
    Item, UItem, TreeEditor, TreeNode
from pyface.api import ImageResource
from fixes import fix_background_color
from chaco.api import OverlayPlotContainer, Plot, ArrayPlotData, \
    add_default_axes, add_default_grids, create_line_plot, Legend, PlotAxis
from chaco.tools.api import PanTool, ZoomTool, DragZoom, LegendTool
from ui_helpers import get_file_from_dialog
import specs

# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()
APP_WIDTH = 800
title = "SinSPECt"
app_icon = os.path.join('resources','app_icon.ico')

# Traited versions of SPECS xml file classes - used by TreeEditor widget

class SPECSRegion(HasTraits):
    '''
    The traited SPECSRegion contains a specs.SPECSRegion object
    '''
    name   = Str('<unknown>')
    title  = Str
    region = Instance(specs.SPECSRegion)
    selection = Instance('SelectorPanel')   # A string argument here allows a forward reference

    def __init__(self, name, region, **traits):
        super(SPECSRegion, self).__init__(**traits) # HasTraits.__init__(self, **traits)
        self.name = name
        self.region = region
        # Add a reference to the specs.SPECSRegion object in case we want access to its
        # Traited SPECSRegion owner
        self.region.owner = self
        self.selection = SelectorPanel(self)
        # Instantiation of the SelectorPanel creates self.selection.counts == False
        # Setting it True now triggers a trait change event which is what we desire to turn the plot on
        self.selection.counts = True


class SPECSGroup(HasTraits):
    name = Str('<unknown>')
    specs_regions = List(SPECSRegion)


class SpecsFile(HasTraits):
    name = Str('<unknown>')
    specs_groups = List(SPECSGroup)

    def open(self, filename):
        s = specs.SPECS(filename)
        self.name = filename
        for group in s.groups:
            specs_group = SPECSGroup(name=group.name, specs_regions=[])
            for region in group.regions:
                specs_group.specs_regions.append(SPECSRegion(name=region.name, region=region))
            self.specs_groups.append(specs_group)
        return self


class TreePanel(HasTraits):
    specs_file = Instance(SpecsFile)
    file_path = Str(None)
    most_recent_path = Str('')
#    # When a selection is made this gets a reference to the selected tree node instance
#    node_selection = Instance(HasTraits)

    # Button group above tree area
    bt_open_file = Button("Open file...")
    bt_export_file = Button("Export...")

    def _bt_open_file_changed(self):
        file_path = get_file_from_dialog()
        if file_path is not None:
            self.most_recent_path = os.path.dirname(file_path)
            self.file_path = file_path

    def _file_path_changed(self, new):
        """
        When the file dialog box is closed with a file selection, open that file
        """
        self.name = self.file_path
        self.specs_file = SpecsFile().open(self.file_path)

    def bt_export_file_changed(self):
#        file_path = get_file_from_dialog()
#        if file_path is not None:
#            self.most_recent_path = os.path.dirname(file_path)
#            self.file_path = file_path
#        dlg = FileDialog(title='Choose file', action='save', wildcard=txt_wildcard)
#        if dlg.open() == OK:
#            return dlg.paths[0]
        pass

    def _has_data(self):
        return self.file_path is not None

    def _group_select(self):
        print 'gs', self.name

    def _region_select(self):
        # Update SelectorPanel
        main_app.selector_panel = self.selection
        print 'rs', self.name

    def _group_dclick(self):
        '''
        Double-clicking a node cycles through selection states of subordinate regions
        all-on -> last-selection -> all-off -> all-on -> ...
        '''
        print 'dg', self.name

    def _region_dclick(self):
        '''
        Double-clicking a node cycles through selection states of subordinate channels
        all-on -> last-selection -> all-off -> all-on -> ...
        '''
        print 'dr', self.name, self.region.owner.name

    # View for objects that aren't edited
    no_view = View()

    # Tree editor
    tree_editor = TreeEditor(
        nodes = [
            TreeNode( node_for  = [SpecsFile],
                      auto_open = True,
                      children  = 'specs_groups',
                      label     = 'name',
                      view      = no_view,
                      add       = [SPECSGroup],
#                      on_dclick = _bt_open_file_changed,
                      icon_path = 'resources',
                      icon_open = 'file.ico',
                      icon_group = 'file.ico',
                    ),

            TreeNode( node_for  = [SPECSGroup],
                      auto_open = True,
                      children  = 'specs_regions',
                      label     = 'name',
                      view      = no_view,
                      add       = [SPECSRegion],
                      on_select = _group_select,
                      on_dclick = _group_dclick,
                      icon_path = 'resources',
                      icon_open = 'group.ico',
                    ),

            TreeNode( node_for  = [SPECSRegion],
                      auto_open = True,
                      label     = 'name',
                      view      = no_view,
                      on_select = _region_select,
                      on_dclick = _region_dclick,
                      icon_path = 'resources',
                      icon_item = 'region.ico',
                    )
        ],
        editable = False,           # suppress the editor pane as we are using the separate Chaco pane for this
#        selected = 'node_selection',
    )

    # The tree view
    traits_view =   View(
                        UItem('bt_open_file'),
                        UItem('bt_export_file', enabled_when='object._has_data()'),
                        UItem(
                            name = 'specs_file',
                            editor = tree_editor,
                        ),
                    )


class PlotPanel(HasTraits):
    '''
    Based largely on the Chaco Overlapping plots demo
    '''
    plot_data = Instance(ArrayPlotData)
    plot = Instance(Plot)

    def __init__(self, **traits):
        super(PlotPanel, self).__init__(**traits)   # HasTraits.__init__(self, **traits)
        self.plot_data = ArrayPlotData()
        self.plot = Plot(self.plot_data)
        self.plot.value_range.low = 0               # fix y-axis min to 0
        self.plot.index_axis = PlotAxis(self.plot, orientation='bottom', title='Energy [eV]')
        self.plot.y_axis = PlotAxis(self.plot, orientation='left', title='Intensity [Counts]')
        self.first = True

    def add_plot(self, name, xs, ys, **lineplot_args):
        self.plot_data.set_data(name+'_xs', xs)
        self.plot_data.set_data(name+'_ys', ys)
        self.plot.plot((name+'_xs', name+'_ys'), name=name, type='line', **lineplot_args)

#TODO: if we remove the first instance via remove() the mapper and tools are also removed
#      so I may have to add a transparent 1st plot series that never gets removed

#        if self.first:
#            self.value_mapper, self.index_mapper, self.legend = self._setup_plot_tools(plot)
#            self.first = False
#        self._setup_mapper(plot, self.value_mapper, self.index_mapper)

#        self.legend.plots = self.plots
        self.plot.request_redraw()

    def remove_plot(self, name):
        self.plot_data.del_data(name+'_xs')
        self.plot_data.del_data(name+'_ys')
        self.plot.delplot(name)
        self.plot.request_redraw()

    def _setup_plot_tools(self, plot):
        """Sets up the background, and several tools on a plot"""
        # Make a white background with grids and axes
#        plot.bgcolor = 'white'
        plot.bgcolor='transparent'
        add_default_grids(plot)
        add_default_axes(plot)

        # Allow white space around plot
        plot.index_range.tight_bounds = False
        plot.index_range.refresh()
        plot.value_range.tight_bounds = False
        plot.value_range.refresh()

        # The PanTool allows panning around the plot
        plot.tools.append(PanTool(plot))

        # The ZoomTool tool is stateful and allows drawing a zoom
        # box to select a zoom region.
        zoom = ZoomTool(plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)

        # Add a legend in the upper right corner, and make it relocatable
        legend = Legend(component=plot, padding=10, align="ur")
        legend.tools.append(LegendTool(legend, drag_button="right"))
        plot.overlays.append(legend)

        return plot.value_mapper, plot.index_mapper, legend

    def _setup_mapper(self, plot, value_mapper, index_mapper):
        """Sets up a mapper for given plot"""
        plot.value_mapper = value_mapper
        value_mapper.range.add(plot.value)
        plot.index_mapper = index_mapper
        index_mapper.range.add(plot.index)

#    def _plot_default(self):
#        return PlotPanel(padding=40, fill_padding=True,
#                                     bgcolor="white", use_backbuffer=True)

    traits_view =   View(
                        UItem(
                            'plot',
                            editor=ComponentEditor(),
                            show_label=False
                        ),
                        resizable=True,
                    )


class SelectorPanel(HasTraits):
    '''
    A panel of checkboxes reflecting the channels within the specs region used for
    toggling plot visibility and flagging for export.
    What is really needed here is a dynamic view that creates a checkbox for each
    Bool trait in the region object. However, dynamic views seem extremely tricky, so
    I'll just reflect the state of the region object's traits in the checkboxes here.
    '''
    name = Str('<unknown>')
    region = Instance(SPECSRegion)

    '''
    GR - see TraitsUI documentation Example 5b
    http://docs.enthought.com/traitsui/traitsui_user_manual/advanced_view.html
    Instead of just defining a default view here, build it using
    def default_traits_view(self):
    '''

    def __init__(self, region=None, **traits):
        super(SelectorPanel, self).__init__(**traits)   # HasTraits.__init__(self, **traits)
        if region is None:      # This will be the case on the first call
            return
        self.region = region

        # create global counts indicator
        self.add_trait('counts', Bool)

        # create channel indicators
        channel_counts_len = region.region.channel_counts.shape[1]
        for i in range(channel_counts_len):
            self.add_trait('channel_counts_{}'.format(i+1), Bool)
        # use self._instance_traits() to list these traits

        # create extended channel indicators
        extended_channels_len = region.region.extended_channels.shape[1]
        for i in range(extended_channels_len):
            self.add_trait('extended_channels_{}'.format(i+1), Bool)

    def _counts_changed(self, trait, old, new):
#        print self.region.name, trait, old, new
        if new:
            self._add_plot(self.region.name, trait)
        else:
            self._remove_plot(self.region.name, trait)

    @on_trait_change('channel_counts_+')
    def _channel_counts_x_changed(self, container, trait, new):
#        print self.region.name, container, trait, new
        if new:
            self._add_plot(self.region.name, trait, self._get_name_num(trait))
        else:
            self._remove_plot(self.region.name, trait)

    @on_trait_change('extended_channels_+')
    def _extended_channels_changed(self, container, trait, new):
#        print self.region.name, container, trait, new
        if new:
            self._add_plot(self.region.name, trait, self._get_name_num(trait))
        else:
            self._remove_plot(self.region.name, trait)

    def _name_plot(self, region_name, series_name):
        ''' Make a unique name based on the region_name and series_name parts
        which together are assumed to form a unique pair
        '''
        return '{}_{}'.format(region_name, series_name)

    def _get_name_body(self, series_name):
        ''' Get first part of name.
        '''
        return '_'.join(series_name.split('_')[:2])

    def _get_name_num(self, series_name):
        ''' Get last part of name.
        '''
        return int(series_name.split('_')[-1])

#    def _get_y_axis(self, region, index=None, extended=False):
#        r = region.region
#        if index is not None:
#            if extended:
#            else:
    def _get_x_axis(self, region):
        r = region.region
        if r.scan_mode == 'FixedAnalyzerTransmission':
            xs = r.binding_axis
        elif r.scan_mode == 'ConstantFinalState':
            xs = r.excitation_axis
        else:
            xs = r.kinetic_axis
        return xs

    def _add_plot(self, region_name, series_name, column=None):
        ''' Call plot widget to create it. '''
        name = self._name_plot(region_name, series_name)
        xs = self._get_x_axis(self.region)
        if series_name == 'counts':
            ys = self.region.region.__getattribute__(series_name)
        else:
            # Get 'first_second' part of the name 'first_second_n' which will either be
            # 'channel_counts' or 'extended_channels'. Then use this to retrieve the
            # matching array from the specs.SPECSRegion object.
            series_name = self._get_name_body(series_name)
            ys = self.region.region.__getattribute__(series_name)[:,column-1]

        line_attributes = { \
            'counts'            : {'color':'black', 'width':2.0},
            'channel_counts'    : {'color':'blue' , 'width':1.5},
            'extended_channels' : {'color':'red'  , 'width':1.5},
            }[series_name]
        plot_panel.add_plot(name, xs, ys, **line_attributes)

    def _remove_plot(self, region_name, series_name):
        '''
        Call plot widget to remove it and delete the reference here.
        '''
        name = self._name_plot(region_name, series_name)
        plot_panel.remove_plot(name)

    def default_traits_view(self):
        '''
        Called to create the selection view to be shown in the selection panel.
        This is also the default View called when the GUI is first initialised with a
        "None" SelectorPanel.
        https://mail.enthought.com/pipermail/enthought-dev/2012-May/031008.html
        '''
        trait_dict = self._instance_traits()
#        items = [Item(name) for name in sorted(trait_dict) if name is not 'trait_added']
        items = []
        if 'counts' in trait_dict:
            group1 = HGroup()
            group1.content = []
            group1.content.extend([Item('counts', label='Counts')])
            # channel_counts_x group
            group = HGroup()
            group.content = [Item(name, label=name.split('_')[-1]) for name in sorted(trait_dict) if 'channel_counts_' in name]
            group.show_border = True
            group.label = 'Channel Counts'
            group1.content.append(group)
            # extended_channels_x group
            group = HGroup()
            group.content = [Item(name, label=name.split('_')[-1]) for name in sorted(trait_dict) if 'extended_channels_' in name]
            group.show_border = True
            group.label = 'Extended Channels'
            group1.content.append(group)
            items.append(group1)
        return View(*items)


class MainApp(HasTraits):
    # Left Panel
    tree_panel = Instance(TreePanel)
    selector_panel = Instance(SelectorPanel)
    # Right Panel
    plot_panel = Instance(PlotPanel)

    # The main view
    traits_view =   View(
                        HSplit(
                            Group(
                                UItem('tree_panel', style='custom', width=APP_WIDTH*0.2),
                            ),
                            Group(
                                VGroup(
                                    UItem('selector_panel', style='custom', width=APP_WIDTH*.8),
                                    UItem('plot_panel', style='custom'),
                                ),
                            ),
                        ),
                    title = title,
                    icon = ImageResource(app_icon),
                    id = 'app.main_view',
                    dock = 'horizontal',
                    drop_class = HasTraits,
                    resizable = True,
                    )


_info_html = \
"""
<h5>Plot region usage</h5>
Left drag = Zoom a selection of the plot <br>
Right drag = Pan the plot <br>
Right click = Undo zoom <br>
Esc = Reset zoom/pan <br>
Mousewheel = Zoom in/out <br>

<h5>About the software</h5>

Please send bug reports and suggestions to <br>
sinspect@synchrotron.org.au <br>

Software authors: <br>
Gary Ruben, Victorian eResearch Strategic Initiative (VeRSI), gruben@versi.edu.au <br>
Kane O'Donnell, Australian Synchrotron <br>
http://www.versi.edu.au <br>

Software home: <br>
http://www.synchrotron.org.au/sinspect <br>
Software source: <br>
http://github.com/AustralianSynchrotron/sinspect <br>

Recognition of NeCTAR funding: <br>
The Australian Synchrotron is proud to be in partnership with the National eResearch Collaboration Tools and
Resources (NeCTAR) project to develop eResearch Tools for the synchrotron research community. This will enable our
scientific users to have instant access to the results of data during the course of their experiment which will
facilitate better decision making and also provide the opportunity for ongoing data analysis via remote access.

Copyright (c) 2012, Australian Synchrotron Company Ltd <br>
All rights reserved.
"""


if __name__ == "__main__":
    tree_panel = TreePanel(specs_file=SpecsFile())
    selector_panel = SelectorPanel()
    plot_panel = PlotPanel()
    main_app = MainApp(
        tree_panel=tree_panel,
        selector_panel=selector_panel,
        plot_panel=plot_panel,
        )
    main_app.configure_traits()
