import os
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
import numpy as np
from enable.api import ComponentEditor
from traits.api import Str, Bool, Enum, List, Dict, Any, \
    HasTraits, Instance, Button, on_trait_change
from traitsui.api import View, Group, HGroup, VGroup, HSplit, \
    Item, UItem, TreeEditor, TreeNode, TreeNodeObject, Menu
from traitsui.key_bindings import KeyBinding, KeyBindings
from pyface.api import ImageResource, DirectoryDialog, OK
from fixes import fix_background_color
from chaco.api import Plot, ArrayPlotData, PlotAxis, \
    add_default_axes, add_default_grids
from chaco.tools.api import PanTool, ZoomTool
from chaco.tools.tool_states import PanState
from ui_helpers import get_file_from_dialog
import specs


# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()
APP_WIDTH = 800
title = "SinSPECt"
app_icon = os.path.join('resources','app_icon.ico')

# SPECSRegion, SPECSGroup and SpecsFile are Traited versions of SPECS xml file classes
# that represent nodes in the TreeEditor widget

class SPECSRegion(HasTraits):
    ''' The traited SPECSRegion contains a specs.SPECSRegion object and
    represents a Region node in the TreeEditor
    '''
    name   = Str('<unknown>')
    region = Instance(specs.SPECSRegion)    # The reference to the contained region object
    selection = Instance('SelectorPanel')   # A string argument here allows a forward reference

    def __init__(self, name, region, **traits):
        super(SPECSRegion, self).__init__(**traits) # HasTraits.__init__(self, **traits)
        self.name = name
        self.region = region
        # Add a reference to the specs.SPECSRegion object in case we want access to its
        # Traited SPECSRegion owner
        self.region.owner = self
        self.selection = SelectorPanel(self)
        # Instantiation of the SelectorPanel creates it with self.selection.counts==False
        # Setting self.selection.counts=True now triggers a trait change event which
        # triggers creation of the related plot series
        # self.selection.counts = True

    def get_x_axis(self):
        ''' Return x-axis data based on the scan_mode metadata '''
        r = self.region
        if r.scan_mode == 'FixedAnalyzerTransmission':
            xs = r.binding_axis
        elif r.scan_mode == 'ConstantFinalState':
            xs = r.excitation_axis
        else:
            xs = r.kinetic_axis
        return xs


class SPECSGroup(HasTraits):
    ''' A group node in the TreeEditor '''
    name = Str('<unknown>')
    specs_regions = List(SPECSRegion)   # container for the subordinate regions


class SpecsFile(HasTraits):
    ''' The file node in the TreeEditor '''
    name = Str('<unknown>')
    specs_groups = List(SPECSGroup)     # container for the subordinate groups

    def _uniquify_names(self, names):
        ''' names is a list of strings. This generator function ensures all strings in
        the names list are unique by appending -n to the name if it is repeated, where n
        is an incrementing number. e.g. if names is ['a', 'b', 'c', 'a', 'b', 'a'] this
        yields ['a', 'b', 'c', 'a-1', 'b-1', 'a-2']
        '''
        freqs = {}
        for name in names:
            freqs[name] = freqs.get(name, 0) + 1
            if freqs[name] > 1:
                yield '{}-{}'.format(name, freqs[name]-1)
            else:
                yield name

    def open(self, filename):
        ''' Create all objects corresponding to the tree '''
        s = specs.SPECS(filename)
        self.name = filename
        group_names = [g.name for g in s.groups]
        uniquify_group_gen = self._uniquify_names(group_names)
        for group in s.groups:
            specs_group = SPECSGroup(name=uniquify_group_gen.next(), specs_regions=[])
            region_names = [r.name for r in group.regions]
            uniquify_region_gen = self._uniquify_names(region_names)
            for region in group.regions:
                specs_group.specs_regions.append(SPECSRegion(name=uniquify_region_gen.next(), region=region))
            self.specs_groups.append(specs_group)
        return self


class TreePanel(HasTraits):
    specs_file = Instance(SpecsFile)
    file_path = Str(None)
    most_recent_path = Str('')
    node_selection = Any()
#    # When a selection is made this gets a reference to the selected tree node instance
#    node_selection = Instance(HasTraits)

    # Buttons in the widget group above the tree area
    bt_open_file = Button("Open file...")
    bt_export_file = Button("Export...")
    cb_header = Bool(True)
    delimiter = Enum('tab','space','comma')('tab')

    def _bt_open_file_changed(self):
        ''' Event handler
        Called when user clicks the Open file... button
        '''
        file_path = get_file_from_dialog()
        if file_path is not None:
            self.most_recent_path = os.path.dirname(file_path)
            self.file_path = file_path

    def _file_path_changed(self, new):
        ''' Trait event handler
        When the file dialog box is closed with a file selection, open that file
        '''
        plot_panel.remove_all_plots()

        self.name = self.file_path
        self.specs_file = SpecsFile().open(self.file_path)

    def _bt_export_file_changed(self):
        ''' Event handler
        Called when the user clicks the Export... button
        '''
        dlg = DirectoryDialog(default_path=self.most_recent_path)
        if dlg.open() == OK:
            self.most_recent_path = dlg.path

            # Export all regions in all groups
            for g in self.specs_file.specs_groups:
                dir_created_for_this_group = False
                for r in g.specs_regions:
                    # make file region.name+'.xy' in directory g.name
                    print g.name, r.name
                    # Column data contains the following in left-to-right order:
                    # x-axis, counts, channel_counts_n and extended_channels_n

                    # x-axis
                    a = [r.get_x_axis()]
                    h = {'FixedAnalyzerTransmission':'"Binding Axis"',
                         'ConstantFinalState'       :'"Excitation Axis"',
                        }.get(r.region.scan_mode,    '"Kinetic Axis"')
                    delimiter = {'space':' ', 'comma':',', 'tab':'\t'}[self.delimiter]
                    any_checked = False

                    if r.selection.counts:
                        # counts
                        a.append(r.region.counts)
                        h += '{}Counts'.format(delimiter)
                        any_checked = True

                        # channel_counts_n
                        for name in sorted(r.selection._instance_traits()):
                            if 'channel_counts_' in name:
                                channel_num = get_name_num(name)
                                a.append(r.region.channel_counts[:,channel_num-1])
                                h += '{}"Channel {} counts"'.format(delimiter, channel_num)

                        # extended_channels_n
                        for name in sorted(r.selection._instance_traits()):
                            if 'extended_channels_' in name:
                                channel_num = get_name_num(name)
                                a.append(r.region.extended_channels[:,channel_num-1])
                                h += '{}"Extended channel {}"'.format(delimiter, channel_num)
                    '''
                    # channel_counts_n
                    for name, enabled in sorted(r.selection.get_trait_states().iteritems()):
                        if enabled and ('channel_counts_' in name):
                            a.append(r.region.channel_counts[:,get_name_num(name)-1])
                            any_checked = True

                    # extended_channels_n
                    for name, enabled in sorted(r.selection.get_trait_states().iteritems()):
                        if enabled and ('extended_channels_' in name):
                            a.append(r.region.extended_channels[:,get_name_num(name)-1])
                            any_checked = True
                    '''

                    # Write it
                    if any_checked:
                        if not dir_created_for_this_group:
                            # Try creating directory if it doesn't exist
                            try:
                                dirname = os.path.join(dlg.path, g.name)
                                os.mkdir(dirname)
                                dir_created_for_this_group = True
                            except OSError:
                                # Something exists already, or it can't be written
                                #TODO: Give a nice message here
                                pass

                        filename = os.path.join(dirname, r.name+'.xy')
                        with open(filename, 'w') as f:
                            if self.cb_header:
                                print >> f, h
                            a = np.array(a).transpose()
                            #TODO: what format and newline character are we using here?
                            np.savetxt(f, a, delimiter=delimiter)

    def _has_data(self):
        return self.file_path is not None

    def _group_select(self):
        print 'gs', self.name

    def _region_select(self):
        # Update SelectorPanel
        main_app.selector_panel = self.selection
        #TODO: call _update_last_selection(self) on anything not in current node_selection
        print main_app.tree_panel.node_selection
        print 'rs', self.name

    def _group_dclick(self):
        '''
        Double-clicking a node cycles through selection states of subordinate regions
        all-on -> last-selection -> all-off -> all-on -> ...
        '''
        region_state = {r.selection.counts for r in self.specs_regions}
        if True in region_state:
            # at least one of the regions is enabled, disable all
            for r in self.specs_regions:
                r.selection.region_cycle(all_off=True)
        else:
            # enable all counts
            for r in self.specs_regions:
                r.selection.region_cycle(counts_only=True)


    def _region_dclick(self):
        '''
        Double-clicking a node cycles through selection states of subordinate channels
        all-on -> last-selection -> all-off -> all-on -> ...
        '''
        for s in tree_panel.node_selection:
            s.icon = 'none'
        tree_panel._cycle_region_key(info=None)


    def _cycle_region_key(self, info):
        for n in self.node_selection:
            n.selection.region_cycle()
            state = n.selection.get_trait_states()
            channel_counts_states = {val for key,val in state.iteritems() if get_name_body(key)=='channel_counts'}
            if True in channel_counts_states and False in channel_counts_states:
                self.set_node_icon('some')
            elif True in channel_counts_states:
                self.set_node_icon('all')
            else:
                self.set_node_icon('none')


    def set_node_icon(self, mode):
        for node in self.node_selection:
            node.icon = mode
        print mode


    def _toggle_key(self, info):
        for n in self.node_selection:
            n.selection.counts = not n.selection.counts

    def _select_key(self, info):
        for n in self.node_selection:
            n.selection.counts = True

    def _deselect_key(self, info):
        for n in self.node_selection:
            n.selection.counts = False


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
                      menu      = Menu(),
#                      on_dclick = _bt_open_file_changed,
                      rename_me = False,
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
                      menu      = Menu(),
                      rename_me = False,
                      on_select = _group_select,
                      on_dclick = _group_dclick,
                      icon_path = 'resources',
                      icon_open = 'group.ico',
                    ),

            TreeNode( node_for  = [SPECSRegion],
                      auto_open = True,
                      label     = 'name',
                      view      = no_view,
                      menu      = Menu(),
                      rename_me = False,
                      on_select = _region_select,
                      on_dclick = _region_dclick,
                      icon_path = 'resources',
                      icon_item = 'region.ico',
                    )
        ],
        editable = False,           # suppress the editor pane as we are using the separate Chaco pane for this
        selected = 'node_selection',
        selection_mode = 'extended',
    )

    key_bindings = KeyBindings(
        KeyBinding( binding1    = 'Space',
                    binding2    = 't',
                    description = 'Toggle Selection',
                    method_name = '_toggle_key' ),
        KeyBinding( binding1    = '+',
                    binding2    = '=',
                    description = 'Select',
                    method_name = '_select_key' ),
        KeyBinding( binding1    = '-',
                    description = 'Deselect',
                    method_name = '_deselect_key' ),
        KeyBinding( binding1    = 'r',
                    description = 'Cycle region',
                    method_name = '_cycle_region_key' ),
    )

    # The tree view
    traits_view =   View(
                        UItem('bt_open_file'),
                        VGroup(
                            HGroup(
                                Item('cb_header', label='Include header'),
                                Item('delimiter'),
                            ),
                            UItem('bt_export_file'),
                            enabled_when = 'object._has_data()',
                            label = 'Data Export',
                            show_border = True,
                        ),
                        UItem(
                            name = 'specs_file',
                            editor = tree_editor,
                        ),
                        key_bindings = key_bindings,

                    )


class PanToolWithHistory(PanTool):
    def __init__(self, *args, **kwargs):
        self.history_tool = kwargs.get('history_tool', None)
        if 'history_tool' in kwargs:
            del kwargs['history_tool']
        super(PanToolWithHistory, self).__init__(*args, **kwargs)

    def _start_pan(self, event, capture_mouse=False):
        super(PanToolWithHistory, self)._start_pan(event, capture_mouse=False)
        if self.history_tool is not None:
            self._start_pan_xy = self._original_xy
            # Save the current data range center so this movement can be
            # undone later.
            self._prev_state = self.history_tool.data_range_center()

    def _end_pan(self, event):
        super(PanToolWithHistory, self)._end_pan(event)
        if self.history_tool is not None:
            # Only append to the undo history if we have moved a significant
            # amount. This avoids conflicts with the single-click undo
            # function.
            new_xy = np.array((event.x, event.y))
            old_xy = np.array(self._start_pan_xy)
            if any(abs(new_xy - old_xy) > 10):
                next = self.history_tool.data_range_center()
                prev = self._prev_state
                if next != prev:
                    self.history_tool.append_state(PanState(prev, next))


class ClickUndoZoomTool(ZoomTool):
    def __init__(self, component=None, undo_button='right', *args, **kwargs):
        super(ClickUndoZoomTool, self).__init__(component, *args, **kwargs)
        self.undo_button = undo_button
        self._reverting = False
        self.minimum_undo_delta = 3

    def normal_left_down(self, event):
        """ Handles the left mouse button being pressed while the tool is
        in the 'normal' state.

        If the tool is enabled or always on, it starts selecting.
        """
        if self.undo_button == 'left':
            self._undo_screen_start = (event.x, event.y)
        super(ClickUndoZoomTool, self).normal_left_down(event)

    def normal_right_down(self, event):
        """ Handles the right mouse button being pressed while the tool is
        in the 'normal' state.

        If the tool is enabled or always on, it starts selecting.
        """
        if self.undo_button == 'right':
            self._undo_screen_start = (event.x, event.y)
        super(ClickUndoZoomTool, self).normal_right_down(event)

    def normal_left_up(self, event):
        if self.undo_button == 'left':
            if self._mouse_didnt_move(event):
                self.revert_history()

    def normal_right_up(self, event):
        if self.undo_button == 'right':
            if self._mouse_didnt_move(event):
                self.revert_history()

    def selecting_left_up(self, event):
        self.normal_left_up(event)
        super(ClickUndoZoomTool, self).selecting_left_up(event)

    def selecting_right_up(self, event):
        self.normal_right_up(event)
        super(ClickUndoZoomTool, self).selecting_right_up(event)

    def _mouse_didnt_move(self, event):
        start = np.array(self._undo_screen_start)
        end = np.array((event.x, event.y))
        return all(abs(end - start) == 0)

    def clear_undo_history(self):
        self._history_index = 0
        self._history = self._history[:1]

    def revert_history(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._prev_state_pressed()

    def revert_history_all(self):
        self._history_index = 0
        self._reset_state_pressed()

    def _get_mapper_center(self, mapper):
        bounds = mapper.range.low, mapper.range.high
        return bounds[0] + (bounds[1] - bounds[0])/2.

    def data_range_center(self):
        x_center = self._get_mapper_center(self._get_x_mapper())
        y_center = self._get_mapper_center(self._get_y_mapper())
        return x_center, y_center

    def append_state(self, state):
        self._append_state(state, set_index=True)


class PlotPanel(HasTraits):
    ''' The Chaco plot area.
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

        # Now add a transparent 1st plot series that never gets removed
        # since if we remove the first instance via remove() the mapper and tools are also removed
        plot = self.add_plot('tool_plot', [0], [0], bgcolor='white', color='transparent')
        self.value_mapper, self.index_mapper = self._setup_plot_tools(plot)

    def add_plot(self, name, xs, ys, **lineplot_args):
        self.plot_data.set_data(name+'_xs', xs)
        self.plot_data.set_data(name+'_ys', ys)
        self.plot.plot((name+'_xs', name+'_ys'), name=name, type='line', **lineplot_args)

        self.plot.request_redraw()
        return self.plot

    def remove_plot(self, name):
        if name is 'tool_plot':
            # Never remove this one since the chaco tools are attached to it 
            return
        self.plot_data.del_data(name+'_xs')
        self.plot_data.del_data(name+'_ys')
        self.plot.delplot(name)
        self.plot.request_redraw()

    def remove_all_plots(self):
        # Make sure we don't remove 'tool_plot'
        for p in plot_panel.plot.plots.keys():
            plot_panel.remove_plot(p)

    def get_plot(self, name):
        ''' Get a plot reference from the name '''
        return self.plot.plots[name][0]

    def set_plot_attributes(self, name, **attributes):
        try:
            for key, value in attributes.iteritems():
                setattr(self.plot.plots[name][0], key, value)
        except KeyError:
            pass

    def _setup_plot_tools(self, plot):
        ''' Sets up the background, and several tools on a plot '''
        # Make a white background with grids and axes
        plot.bgcolor='transparent'
        add_default_grids(plot)
        add_default_axes(plot)

        # The PanTool allows panning around the plot
        plot.tools.append(PanToolWithHistory(plot, drag_button='right'))

        # The ZoomTool tool is stateful and allows drawing a zoom
        # box to select a zoom region.
        zoom = ClickUndoZoomTool(plot, tool_mode="box", always_on=True)
        plot.overlays.append(zoom)

        return plot.value_mapper, plot.index_mapper

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


#TODO: Look at LineInspector and HighlightTool

#class LineSelectionTool(BaseTool):
#    ''' 
#    From http://enthought-dev.117412.n3.nabble.com/selecting-a-curve-by-clicking-on-it-td3207577.html
#    enthought.enable.base_tool.BaseTool is a subclass of
#    enthought.enable.interactor.Interactor that has a 'component'
#    trait set during __init__
#    '''
#
#    threshold = Float(15.0)  # Threshold in pixels.
#
#    def normal_left_down(self, event):
#        control = event.window.control   # Get the underlying widget.
#        hits = self.component.components_at(event.x, event.y)
#        actions = []
#        for component in hits:
#            # event.x and event.y are relative to event.window
#            # and need to be translated to the component's coordinate
#            # space.
#            offset_x, offset_y = component.container.position
#            x = event.x - offset_x
#            y = event.y - offset_y
#            # As noted in the enthought.chaco.lineplot.LinePlot.hittest
#            # method docs:
#            # "This only checks data points and *not* the actual line
#            # segments connecting them."
#            point = component.hittest((x, y), self.threshold)
#            if point is not None:
#                # Find the label of the component.
#                label = None
#                for candidate, subplots in component.container.plots.iteritems():
#                    if component in subplots:
#                        label = candidate
#                if label is not None:
#                    action = QtGui.QAction(label, None)
#                    @action.triggered.connect
#                    def on_action_triggered(checked, label=label, component=component):
#                        component.edit_traits()
#                    actions.append(action)
#        if len(actions) > 0:
#            menu = QtGui.QMenu(control)
#            for action in actions:
#                menu.addAction(action)
#            menu.exec_(QtGui.QCursor.pos())
#        else:
#            # No actions were created, show no menu.
#            pass 


def get_name_body(series_name):
    ''' Get first part of name
    e.g. get_name_body('foo_bar_baz') returns foo_bar
    '''
    return '_'.join(series_name.split('_')[:2])

def get_name_num(series_name):
    ''' Get last part of name.
    e.g. get_name_num('foo_bar_baz') returns baz
    '''
    return int(series_name.split('_')[-1])


class SelectorPanel(HasTraits):
    '''
    A panel of checkboxes reflecting the channels within the specs region used for
    toggling plot visibility and flagging for export.
    A "better" way to implememnt this would be to create a "dynamic view" that has a
    checkbox for each Bool trait in the region object. However, dynamic views seem
    extremely tricky, so instead I just reflect the state of the region object's traits
    in the checkboxes here.
    See TraitsUI documentation Example 5b
    http://docs.enthought.com/traitsui/traitsui_user_manual/advanced_view.html
    Instead of just defining a default view here, I build it using
    def default_traits_view(self):
    '''
    name = Str('<unknown>')
    region = Instance(SPECSRegion)
    last_selection = Dict   # stores counts and channel traits whenever a checkbox is clicked
    cycle_state = Enum('counts_only', 'all_on', 'all_off')
    plots = {}

    def __init__(self, region=None, **traits):
        super(SelectorPanel, self).__init__(**traits)   # HasTraits.__init__(self, **traits)
        if region is None:      # This will be the case on the first call
            return
        self.region = region

        # create a trait for the counts checkbox
        self.add_trait('counts', Bool)

        # create traits for each channel_counts_n checkbox
        if region.region.channel_counts is not None:
            channel_counts_len = region.region.channel_counts.shape[1]
            for i in range(channel_counts_len):
                self.add_trait('channel_counts_{}'.format(i+1), Bool)
            # use self._instance_traits() to list these traits

        # create traits for each extended_channels_n checkbox
        if region.region.extended_channels is not None:
            extended_channels_len = region.region.extended_channels.shape[1]
            for i in range(extended_channels_len):
                self.add_trait('extended_channels_{}'.format(i+1), Bool)
        # Now we've created all the Bool/checkbox traits default_traits_view() can
        # create a view for them.

        self.cycle_state = 'counts_only'


    def default_traits_view(self):
        '''
        Called to create the selection view to be shown in the selection panel.
        This is also the default View called when the GUI is first initialised with a
        "None" SelectorPanel.
        https://mail.enthought.com/pipermail/enthought-dev/2012-May/031008.html
        '''
        trait_dict = self._instance_traits()
        items = []
        if 'counts' in trait_dict:
            group1 = HGroup()
            group1.content = []
            group1.content.append(Item('counts', label='Counts'))
            # channel_counts_x group
            channel_counts_buttons = [Item(name, label=name.split('_')[-1])
                            for name in sorted(trait_dict) if 'channel_counts_' in name]
            if len(channel_counts_buttons) > 0:
                group = HGroup()
                group.content = channel_counts_buttons
                group.show_border = True
                group.label = 'Channel Counts'
                group1.content.append(group)
            # extended_channels_x group
            extended_channels_buttons = [Item(name, label=name.split('_')[-1])
                            for name in sorted(trait_dict) if 'extended_channels_' in name]
            if len(extended_channels_buttons) > 0:
                group = HGroup()
                group.content = extended_channels_buttons
                group.show_border = True
                group.label = 'Extended Channels'
                group1.content.append(group)
            items.append(group1)
        return View(*items)


    def _counts_changed(self, trait, old, new):
        ''' Trait event handler
        The counts checkbox was toggled
        '''
        if new:
            self._add_plot(self.region.name, trait)
        else:
            self._remove_plot(self.region.name, trait)

    @on_trait_change('channel_counts_+, extended_channels_+')
    def _channel_counts_x_changed(self, container, trait, new):
        ''' Trait event handler
        A channel_counts_n or extended_channels_n checkbox was toggled
        '''
        if new:
            self._add_plot(self.region.name, trait, get_name_num(trait))
        else:
            self._remove_plot(self.region.name, trait)

    def _name_plot(self, region_name, series_name):
        ''' Make a unique name based on the region_name and series_name parts
        which together are assumed to form a unique pair
        '''
        return '{}_{}'.format(region_name, series_name)

    def _add_plot(self, region_name, series_name, column=None):
        ''' Adds a plot to the chaco plot widget. '''
        name = self._name_plot(region_name, series_name)
        xs = self.region.get_x_axis()
        if series_name == 'counts':
            ys = self.region.region.__getattribute__(series_name)
        else:
            # Get 'first_second' part of the name 'first_second_n' which will either be
            # 'channel_counts' or 'extended_channels'. Then use this to retrieve the
            # matching array from the specs.SPECSRegion object.
            series_name = get_name_body(series_name)
            ys = self.region.region.__getattribute__(series_name)[:,column-1]

        line_attributes = { \
            'counts'            : {'color':'black', 'width':2.0},
            'channel_counts'    : {'color':'blue' , 'width':1.5},
            'extended_channels' : {'color':'red'  , 'width':1.5},
            }[series_name]
        plot_panel.add_plot(name, xs, ys, **line_attributes)

    def _remove_plot(self, region_name, series_name):
        ''' Call plot widget to remove it and delete the reference here. '''
        name = self._name_plot(region_name, series_name)
        plot_panel.remove_plot(name)

    def get_trait_states(self):
        ''' Return a dictionary of trait_name:value entries associated with this
        selector panel.
        '''
        # I don't know how to evaluate the trait values directly from _instance_traits()
        # so I use it to get the names then use __getattribute__() to evaluate them.
        return dict([(i, self.__getattribute__(i))
                    for i in self._instance_traits().keys() if i is not 'trait_added'])

    def _update_last_selection(self):
        self.last_selection = dict([(i, self.__getattribute__(i))
                    for i in self._instance_traits().keys() if i is not 'trait_added'])

    def region_cycle(self, all_off=False, counts_only=False):
        ''' Cycle the state of the selected channels
        '''
        if all_off:
            self.trait_set(**dict([(i, False)
                    for i in self._instance_traits().keys() if i is not 'trait_added']))
            self.cycle_state = 'all_off'
            return

        if counts_only:
            self.trait_set(**dict([(i, False)
                    for i in self._instance_traits().keys() if i is not 'trait_added']))
            self.counts = True
            self.cycle_state = 'counts_only'
            return

        if self.cycle_state == 'counts_only':
            self.trait_set(**dict([(i, True)
                    for i in self._instance_traits().keys() if i is not 'trait_added']))
            self.cycle_state = 'all_on'
        elif self.cycle_state == 'all_on':
            self.trait_set(**dict([(i, False)
                    for i in self._instance_traits().keys() if i is not 'trait_added']))
            self.cycle_state = 'all_off'
        else:
            self.counts = True
            self.cycle_state = 'counts_only'


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
