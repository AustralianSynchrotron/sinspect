import os
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
import numpy as np
from enable.api import ComponentEditor
from traits.api import Str, Bool, Enum, List, Dict, Any, \
    HasTraits, Instance, Button, on_trait_change
from traitsui.api import View, Group, HGroup, VGroup, HSplit, \
    Item, UItem, TreeEditor, TreeNode, Menu, Action, Handler
from traitsui.key_bindings import KeyBinding, KeyBindings
from pyface.api import ImageResource, DirectoryDialog, OK, GUI
from fixes import fix_background_color
from chaco.api import Plot, ArrayPlotData, PlotAxis, \
    add_default_axes, add_default_grids
from chaco.tools.api import PanTool, ZoomTool
from chaco.tools.tool_states import PanState
from ui_helpers import get_file_from_dialog
import specs
import wx


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
    # This is the labeled name which is relected in the tree label
    label_name = Str('<unknown>')
    # The labeled name will be derived from this. This is also used for any matching, the
    # export filename etc.
    name = Str('<unknown>')
    region = Instance(specs.SPECSRegion)    # The reference to the contained region object
    group = Instance('SPECSGroup')          # A reference to the containing group
    selection = Instance('SelectorPanel')   # A string argument here allows a forward reference

    def __init__(self, name, region, group, **traits):
        ''' name is a string with the name of the region
        region is a specs.SPECSRegion instance
        '''
        super(SPECSRegion, self).__init__(**traits) # HasTraits.__init__(self, **traits)
        self.name = name
        self.label_name = '  {}'.format(name) # initialise label to this
        self.zero_fill_empty_channels(region)
        self.region = region
        self.group = group
        # Add a reference within the specs.SPECSRegion object in case we want access to its
        # Traited SPECSRegion owner
        self.region.owner = self
        self.selection = SelectorPanel(self)
        # Instantiation of the SelectorPanel creates it with self.selection.counts==False
        # Setting self.selection.counts=True now triggers a trait change event which
        # triggers creation of the related plot series
        # self.selection.counts = True

    def zero_fill_empty_channels(self, region):
        ''' Sometimes the underlying specs.SPECSRegion object contains None to
        indicate that no channel data is available. Here we replace any None channels
        with a zero-filled array in the underlying object
        '''
        CHANNELS = 9
        c = region.channel_counts
        if c is None:
            region.channel_counts = np.zeros((region.counts.size, CHANNELS))
        elif c.size == 0:
            # channel is empty. Just change its label for the moment
            self.label_name = '  {} (empty)'.format(self.name)
        c = region.extended_channels
        if c is None:
            region.extended_channels = np.zeros((region.counts.size, CHANNELS))

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

    def update_label(self):
        self.label_name = self._get_label()

    def _get_label(self):
        ''' Return a string with the name taken from the the underlying sepcs.SPECSRegion
        object prepended by an indicator of the checked status as follows:
        counts channels selected:                             *, space, name
        counts channels not selected but others are selected: -, space, name
        no     channels selected:                             space, space, name
        '''
        s = self.selection
        # see whether a region is empty
        if s.region.region.channel_counts.size == 0:
            empty_indicator = ' (empty)'
        else:
            empty_indicator = ''

        # get state of counts checkbox
        counts_state = s.get_trait_states()['counts']
        # Get sets of all the T & F channel_counts and extended_channels states,
        # i.e. end up with a set {}, {T}, {F}, or {T,F}
        channel_counts_states = s.get_channel_counts_states().values()
        if counts_state:
            if False not in channel_counts_states:
                label = '* {}{}'.format(self.name, empty_indicator)
            else:
                label = '+ {}{}'.format(self.name, empty_indicator)
        else:
            label = '  {}{}'.format(self.name, empty_indicator)
        return label


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
            # Get the names from the underlying specs.SPECSRegion objects
            region_names = [r.name for r in group.regions]
            # Force them to be unique
            uniquify_region_gen = self._uniquify_names(region_names)
            # Now create our Traited SPECSRegion objects
            for region in group.regions:
                specs_group.specs_regions.append(SPECSRegion(name=uniquify_region_gen.next(),
                                                        region=region, group=specs_group))
            self.specs_groups.append(specs_group)
        return self


class TreePanel(HasTraits):
    specs_file = Instance(SpecsFile)
    file_path = Str(None)
    most_recent_path = Str('')
    # When a selection is made this holds a list of references to selected tree nodes
    node_selection = Any()

    # Buttons in the widget group above the tree area
    bt_open_file = Button('Open file...')
    bt_export_file = Button('Export...')
    #bt_set_as_reference = Button('Set Ref')
    bt_copy_to_selection = Button('Paste Ref:')
    lb_ref = Str('')
    ref = Instance(SPECSRegion)
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
        try:
            GUI.set_busy()                      # set hourglass @UndefinedVariable
            self.specs_file = SpecsFile().open(self.file_path)
        except:
            pass
        GUI.set_busy(False)                     # reset hourglass @UndefinedVariable

    def _bt_export_file_changed(self):
        ''' Event handler
        Called when the user clicks the Export... button
        '''
        myFrame = wx.GetApp().GetTopWindow()
        dlg = DirectoryDialog(default_path=self.most_recent_path, parent=myFrame, style='modal')
        if dlg.open() == OK:
            self.most_recent_path = dlg.path

            # Export all regions in all groups
            for g in self.specs_file.specs_groups:
                dir_created_for_this_group = False
                for r in g.specs_regions:
                    # make file region.name+'.xy' in directory g.name
                    # print g.name, r.name
                    # Column data contains the following in left-to-right order:
                    # x-axis, counts, channel_counts_n and extended_channels_n

                    # x-axis
                    a = [r.get_x_axis()]
                    h = '#'
                    h += {'FixedAnalyzerTransmission':'"Binding Axis"',
                          'ConstantFinalState'       :'"Excitation Axis"',
                         }.get(r.region.scan_mode,    '"Kinetic Axis"')
                    delimiter = {'space':' ', 'comma':',', 'tab':'\t'}[self.delimiter]
                    any_checked = False

                    if r.selection.counts:
                        # counts
                        a.append(r.region.counts)
                        cc_dict = r.selection.get_channel_counts_states()
                        # make a string indicating the channel_counts columns summed to
                        # obtain the counts column  
                        counts_label = '+'.join([str(get_name_num(i))
                                                 for i in sorted(cc_dict) if cc_dict[i]])
                        h += '{}"Counts {}"'.format(delimiter, counts_label)
                        any_checked = True

                        # channel_counts_n
                        for name in sorted(r.selection.get_channel_counts_states()):
                            channel_num = get_name_num(name)
                            a.append(r.region.channel_counts[:,channel_num-1])
                            h += '{}"Channel {} counts"'.format(delimiter, channel_num)

                        # extended_channels_n
                        for name in sorted(r.selection.get_extended_channels_states()):
                            channel_num = get_name_num(name)
                            a.append(r.region.extended_channels[:,channel_num-1])
                            h += '{}"Extended channel {}"'.format(delimiter, channel_num)

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
                                # Maybe give a nice message here
                                pass

                        filename = os.path.join(dirname, r.name+'.xy')
                        with open(filename, 'w') as f:
                            if self.cb_header:
                                print >> f, h
                            a = np.array(a).transpose()
                            np.savetxt(f, a, delimiter=delimiter)
                            print filename, 'written'

    def _has_data(self):
        return self.file_path is not None

    def _reference_set(self):
        return self.lb_ref is not ''

    def _group_select(self):
        # print 'gs', self.name
        pass

    def _bt_copy_to_selection_changed(self):
        if self.ref is not None:
            trait_dict = self.ref.selection.get_trait_states()
            for r in tree_panel.node_selection:
                if isinstance(r, SPECSRegion):
                    # paste all counts, channel_counts_ and extended_channels_ states
                    r.selection.set(**trait_dict)

    def _region_select(self):
        # Update SelectorPanel
        main_app.selector_panel = self.selection

        # Remove current plots from the plot window foreground layer
        plot_panel.remove_all_plots(draw_layer='foreground')
        # Add any checked counts and channels to the plot window foreground layer
        self.selection.plot_checkbox_states()

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
        tree_panel._cycle_region_key()

    def _cycle_region_key(self, info=None):
        for n in self.node_selection:
            n.selection.region_cycle()

    def set_node_icon(self, mode):
        for node in self.node_selection:
            node.icon = mode

    def _toggle_key(self, info):
        for n in self.node_selection:
            if isinstance(n, SPECSRegion):
                n.selection.counts = not n.selection.counts
            elif isinstance(n, SPECSGroup):
                for r in n.specs_regions:
                    r.selection.counts = not r.selection.counts

    def _select_key(self, info):
        for n in self.node_selection:
            n.selection.counts = True

    def _deselect_key(self, info):
        for n in self.node_selection:
            n.selection.counts = False

    class TreeHandler(Handler):
        def _menu_set_as_reference(self, editor, obj):
            ''' Sets the current tree node object as the source for copying state to
            selected tree items.
            '''
            tree_panel.ref = obj
            tree_panel.lb_ref = obj.name

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
                      #on_dclick = _bt_open_file_changed,
                      rename_me = False,
                      icon_path = 'resources',
                      #icon_open = 'file.ico',
                      #icon_group = 'file.ico',
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
                      #icon_open = 'group.ico',
                    ),

            TreeNode( node_for  = [SPECSRegion],
                      auto_open = True,
                      label     = 'label_name',
                      view      = no_view,
                      menu      = Menu(Action(name='Set as reference',
                              action='handler._menu_set_as_reference(editor,object)')),
                      rename_me = False,
                      on_select = _region_select,
                      on_dclick = _region_dclick,
                      icon_path = 'resources',
                      #icon_item = 'region.ico',
                    )
        ],
        editable = False,           # suppress the editor pane as we are using the separate Chaco pane for this
        selected = 'node_selection',
        selection_mode = 'extended',
    )

    key_bindings = KeyBindings(
        KeyBinding( binding1    = 't',
                    description = 'Toggle Selection',
                    method_name = '_toggle_key' ),
        KeyBinding( binding1    = '+',
                    binding2    = '=',
                    description = 'Select',
                    method_name = '_select_key' ),
        KeyBinding( binding1    = '-',
                    description = 'Deselect',
                    method_name = '_deselect_key' ),
        KeyBinding( binding1    = 'Space',
                    binding2    = 'r',
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
                        VGroup(
                            HGroup(
                                UItem('bt_copy_to_selection', enabled_when='object._reference_set()'),
                                UItem('lb_ref', style='readonly'),
                            ),
                            label = 'Selection',
                            show_border = True,
                        ),
                        UItem(
                            name = 'specs_file',
                            editor = tree_editor,
                        ),
                        key_bindings = key_bindings,
                        handler = TreeHandler(),
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
            # Only append to the undo history if we have moved a significant amount. 
            # This avoids conflicts with the single-click undo function.
            new_xy = np.array((event.x, event.y))
            old_xy = np.array(self._start_pan_xy)
            if any(abs(new_xy - old_xy) > 10):
                current = self.history_tool.data_range_center()
                prev = self._prev_state
                if current != prev:
                    self.history_tool.append_state(PanState(prev, current))


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
    LAYERS = ['background', 'foreground', 'highlight']

    def __init__(self, **traits):
        super(PlotPanel, self).__init__(**traits)   # HasTraits.__init__(self, **traits)
        self.plot_data = ArrayPlotData()
        self.plot = Plot(self.plot_data)

        # Extend the plot panel's list of drawing layers
        ndx = self.plot.draw_order.index('plot')
        self.plot.draw_order[ndx:ndx] = self.LAYERS

        self.plot.value_range.low = 0               # fix y-axis min to 0
        self.plot.index_axis = PlotAxis(self.plot, orientation='bottom', title='Energy [eV]')
        self.plot.y_axis = PlotAxis(self.plot, orientation='left', title='Intensity [Counts]')

        # Now add a transparent 1st plot series that never gets removed
        # since if we remove the first instance via remove() the mapper and tools are also removed
        plot = self.add_plot('tool_plot', [0,1], [0,1], bgcolor='white', color='transparent')
        self.value_mapper, self.index_mapper = self._setup_plot_tools(plot)

    def add_plot(self, name, xs, ys, draw_layer='foreground', **lineplot_args):
        name = '_'.join([draw_layer, name])
        self.plot_data.set_data(name+'_xs', xs)
        self.plot_data.set_data(name+'_ys', ys)
        renderer = self.plot.plot((name+'_xs', name+'_ys'), name=name, type='line', **lineplot_args)[0]
        renderer.set(draw_layer=draw_layer)

        self.plot.request_redraw()
        return self.plot

    def remove_plot(self, name, draw_layer='foreground'):
        if name is 'tool_plot':
            # Never remove this one since the chaco tools are attached to it 
            return
        if name.split('_')[0] not in self.LAYERS:
            name = '_'.join([draw_layer, name])
        try:
            self.plot_data.del_data(name+'_xs')
            self.plot_data.del_data(name+'_ys')
            self.plot.delplot(name)
            # Invalidate the datasources as chaco maintains a cache:
            # See http://thread.gmane.org/gmane.comp.python.chaco.user/658/focus=656
            self.plot.datasources.clear()
        except KeyError:
            pass
        self.plot.request_redraw()

    def update_plot_data(self, name, data, x_or_y='y', draw_layer='foreground', **lineplot_args):
        name = '_'.join([draw_layer, name])
        xy_suffix = {'x':'_xs', 'y':'_ys'}[x_or_y]
        self.plot_data.set_data(name+xy_suffix, data)
        self.plot.request_redraw()

    def remove_all_plots(self, draw_layer=None):
        ''' When draw_layer is None, removes all plots from all layers (except 'tool_plot'
        which is never removed). Otherwise, removes all plots from the specified
        draw_layer which is assumed to one of the values in the LAYERS list.
        '''
        for p in plot_panel.plot.plots.keys():
            if (draw_layer is None) or (p.split('_')[0] == draw_layer):
                plot_panel.remove_plot(p)

    def get_plot(self, name, draw_layer=None):
        ''' Get a plot reference from the name '''
        if draw_layer is not None:
            name = '_'.join([draw_layer, name])
        return self.plot.plots[name][0]

    def set_plot_attributes(self, name, draw_layer='foreground', **attributes):
        name = '_'.join([draw_layer, name])
        try:
            for key, value in attributes.iteritems():
                setattr(self.plot.plots[name][0], key, value)
        except KeyError:
            pass

    def _setup_plot_tools(self, plot):
        ''' Sets up the background, and several tools on a plot '''
        # Make a white background with grids and axes
        plot.bgcolor='white'
        add_default_grids(plot)
        add_default_axes(plot)

        # The PanTool allows panning around the plot
        plot.tools.append(PanToolWithHistory(plot, drag_button='right'))

        # The ZoomTool tool is stateful and allows drawing a zoom
        # box to select a zoom region.
        zoom = ClickUndoZoomTool(plot, tool_mode="box", always_on=True)
        plot.overlays.append(zoom)

        return plot.value_mapper, plot.index_mapper

    traits_view =   View(
                        UItem(
                            'plot',
                            editor=ComponentEditor(),
                            show_label=False
                        ),
                        resizable=True,
                    )


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

def is_bool_trait(obj, t):
    ''' Return true iff t evaluates to a bool when accessed as an attribute,
    such as a Bool trait 
    '''
    try:
        return type(obj.__getattribute__(t)) is bool
    except AttributeError:
        return False


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
    global tree_panel
    global selector_panel
    global plot_panel

    name = Str('<unknown>')
    region = Instance(SPECSRegion)
    last_selection = Dict   # stores counts and channel traits whenever a checkbox is clicked
    cycle_state = Enum('channels_on', 'counts_on', 'all_on')
    cycle_channel_counts_state = Enum('all_on', 'all_off')('all_on')
    cycle_extended_channels_state = Enum('all_on', 'all_off')('all_off')
    plots = {}
    bt_cycle_channel_counts = Button('All on/off')
    bt_cycle_extended_channels = Button('All on/off')

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
                self.add_trait('channel_counts_{}'.format(i+1), Bool(True))
            # use self._instance_traits() to list these traits

        # create traits for each extended_channels_n checkbox
        if region.region.extended_channels is not None:
            extended_channels_len = region.region.extended_channels.shape[1]
            for i in range(extended_channels_len):
                self.add_trait('extended_channels_{}'.format(i+1), Bool)
        # Now we've created all the Bool/checkbox traits default_traits_view() can
        # create a view for them.

        self.cycle_state = 'channels_on'

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

            # counts group
            group = HGroup()
            group.content = []
            group.content.append(Item('counts', label='Counts'))
            group.show_border = True
            group1.content.append(group)

            # channel_counts_x group
            channel_counts_buttons = [Item(name, label=name.split('_')[-1])
                            for name in sorted(trait_dict) if 'channel_counts_' in name]
            channel_counts_buttons.append(UItem('bt_cycle_channel_counts'))
            if len(channel_counts_buttons) > 0:
                group = HGroup()
                group.content = channel_counts_buttons
                group.show_border = True
                group.label = 'Channel Counts'
                group1.content.append(group)

            # extended_channels_x group
            extended_channels_buttons = [Item(name, label=name.split('_')[-1])
                            for name in sorted(trait_dict) if 'extended_channels_' in name]
            extended_channels_buttons.append(UItem('bt_cycle_extended_channels'))
            if len(extended_channels_buttons) > 0:
                group = HGroup()
                group.content = extended_channels_buttons
                group.show_border = True
                group.label = 'Extended Channels'
                group1.content.append(group)

            group1.label = self.region.name
            group1.show_border = True
            items.append(group1)
        return View(*items)

    def _counts_changed(self, trait, old, new):
        ''' Trait event handler
        The counts checkbox was toggled
        '''
        if new:
            self._add_plot(self.region, trait)
        else:
            self._remove_plot(self.region, trait)
        self.region.update_label()

    @on_trait_change('channel_counts_+')
    def _channel_counts_x_changed(self, container, trait, new):
        ''' Trait event handler
        A channel_counts_n checkbox was toggled
        '''
        # add or remove the channel counts plot from screen
        if new:
            self._add_plot(self.region, trait, get_name_num(trait))
        else:
            self._remove_plot(self.region, trait)

        # recompute counts
        # channel_counts is an n-column (n=9) x m-row array
        # make a mask corresponding to the checkbox state then sum the corresponding columns
        cc_dict = self.get_channel_counts_states()
        mask = np.array([cc_dict[i] for i in sorted(cc_dict)])
        self.region.region.counts = self.region.region.channel_counts[:,mask].sum(axis=1)

        # update the counts series plot data
        # This is done by toggling the counts plot off and on again if it is currently on
        # I tried this by directly updating the counts y-data which should trigger a chaco
        # update, but there seems to be a bug in chaco that makes updating the 
        # series flaky - it doesn't always update the plot. This way works by triggering
        # the _counts_changed() event
        if self.counts:
            self.counts = False
            self.counts = True
        
        # update the tree label to indicate the selection
        self.region.update_label()

    @on_trait_change('extended_channels_+')
    def _extended_channels_x_changed(self, container, trait, new):
        ''' Trait event handler
        An extended_channels_n checkbox was toggled
        '''
        if new:
            self._add_plot(self.region, trait, get_name_num(trait))
        else:
            self._remove_plot(self.region, trait)
        self.region.update_label()

    def _name_plot(self, region, series_name):
        ''' Make a unique name based on the group_name, region_name and series_name parts
        which together form a unique triple because we enforced uniqueness when reading
        the data
        '''
        return '_'.join([region.group.name, region.name, series_name])

    def _add_plot(self, region, series_name, column=None):
        ''' Adds a plot to the chaco plot widget. '''
        name = self._name_plot(region, series_name)
        xs = self.region.get_x_axis()
        if series_name == 'counts':
            ys = self.region.region.counts
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

    def _remove_plot(self, region, series_name):
        ''' Call plot widget to remove it and delete the reference here. '''
        name = self._name_plot(region, series_name)
        plot_panel.remove_plot(name)

    def plot_checkbox_states(self):
        ''' Add plots to the default (foreground) layer reflecting the checkbox states
        '''
        trait_dict = self.get_trait_states()
        for trait, val in trait_dict.iteritems():
            if val:
                # counts
                if trait=='counts':
                    self._add_plot(self.region, trait)
                else:
                    # channel_counts_+, extended_channels_+
                    self._add_plot(self.region, trait, get_name_num(trait))

    def get_trait_states(self):
        ''' Return a dictionary of all trait_name:value entries with associated
        checkboxes in this selector panel.
        '''
        # I don't know how to evaluate the trait values directly from _instance_traits()
        # so I use it to get the names then use __getattribute__() to evaluate them.
        trait_dict = {i: self.__getattribute__(i)
                      for i in self._instance_traits()
                      if is_bool_trait(self, i)}
        return trait_dict

    def get_channel_counts_states(self):
        ''' Return a dictionary of trait_name:value entries associated with the
        channel_counts_ checkboxes in the selector panel.
        '''
        trait_dict = {i: self.__getattribute__(i)
                      for i in self._instance_traits()
                      if get_name_body(i)=='channel_counts'}
        return trait_dict

    def get_extended_channels_states(self):
        ''' Return a dictionary of trait_name:value entries associated with the
        extended_channels_ checkboxes in the selector panel.
        '''
        trait_dict = {i: self.__getattribute__(i)
                      for i in self._instance_traits()
                      if get_name_body(i)=='extended_channels'}
        return trait_dict

    def region_cycle(self, all_off=False, counts_only=False):
        ''' Cycle the state of the selected channels
        '''
        if all_off:
            self.trait_set(**{i: False for i in self._instance_traits()
                              if is_bool_trait(self, i)})
            self.cycle_state = 'channels_on'
            return

        if counts_only:
            self.trait_set(**{i: True for i in self._instance_traits()
                              if get_name_body(i)=='channel_counts'})
            self.counts = True
            self.cycle_state = 'counts_on'
            return

        if self.cycle_state == 'counts_on':
            self.trait_set(**{i: True for i in self._instance_traits()
                              if is_bool_trait(self, i)})
            self.cycle_state = 'all_on'
        elif self.cycle_state == 'all_on':
            self.trait_set(**{i: False for i in self._instance_traits()
                              if is_bool_trait(self, i)})
            self.trait_set(**{i: True for i in self._instance_traits()
                              if get_name_body(i)=='channel_counts'})
            self.cycle_state = 'channels_on'
        else:                                       # channels_on
            self.trait_set(**{i: True for i in self._instance_traits()
                              if get_name_body(i)=='channel_counts'})
            self.counts = True
            self.cycle_state = 'counts_on'

    def _bt_cycle_channel_counts_changed(self):
        ''' Toggle the state of the counts channels
        '''
        channel_counts_states = self.get_channel_counts_states().values()
        if (False in channel_counts_states) and (True in channel_counts_states):
            self.cycle_channel_counts_state = 'all_off'

        if self.cycle_channel_counts_state == 'all_on':
            self.trait_set(**{i: False for i in self._instance_traits()
                              if get_name_body(i)=='channel_counts'})
            self.cycle_channel_counts_state = 'all_off'
        else:
            self.trait_set(**{i: True for i in self._instance_traits()
                              if get_name_body(i)=='channel_counts'})
            self.cycle_channel_counts_state = 'all_on'

    def _bt_cycle_extended_channels_changed(self):
        ''' Toggle the state of the counts channels
        '''
        extended_channels_states = self.get_extended_channels_states().values()
        if (False in extended_channels_states) and (True in extended_channels_states):
            self.cycle_extended_channels_state = 'all_off'

        if self.cycle_extended_channels_state == 'all_on':
            self.trait_set(**{i: False for i in self._instance_traits()
                              if get_name_body(i)=='extended_channels'})
            self.cycle_extended_channels_state = 'all_off'
        else:
            self.trait_set(**{i: True for i in self._instance_traits()
                              if get_name_body(i)=='extended_channels'})
            self.cycle_extended_channels_state = 'all_on'


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

<h5>Keyboard shortcuts for tree selections</h5>
t        Toggle Selection
+,=      Select
-        Deselect
Space,r  Cycle region',

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
