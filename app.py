import os
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
from enable.api import ComponentEditor
from traits.api import Str, Bool, List, Dict, HasTraits, Instance, Callable, Button, \
    HTML, Enum, This, on_trait_change
from traitsui.api import View, Group, HGroup, VGroup, HSplit, VSplit, HFlow, \
    Item, UItem, Label, InstanceEditor, TreeEditor, TreeNode, spring, Handler, \
    CheckListEditor
from pyface.api import ImageResource
from traitsui.menu import Action
from fixes import fix_background_color
from chaco.api import OverlayPlotContainer, Plot, ArrayPlotData
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


class InstanceUItem(UItem):
    """Convenience class for including an Instance in a View"""
    style = Str('custom')
    editor = Instance(InstanceEditor,())


class TreePanel(HasTraits):
    specs_file = Instance(SpecsFile)
    file_path = Str(None)
    most_recent_path = Str('')
#    # When a selection is made this gets a reference to the selected tree node instance
#    node_selection = Instance(HasTraits)

    # Button group above tree area
    bt_open_file = Button("Open file...")

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
                        UItem(
                            name = 'specs_file',
                            editor = tree_editor,
                        ),
                    )


class PlotPanel(HasTraits):
    plot = Instance(OverlayPlotContainer)

    traits_view =   View(
                        UItem(
                            'plot',
                            editor=ComponentEditor(),
                            show_label=False
                        ),
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
    selected_channel_counts = List
    selected_extended_channels = List
    all_selected_channels = List
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
        self.add_trait('channel_counts', Bool)

        # create channel indicators
        channel_counts_len = region.region.channel_counts.shape[1]
        self.selected_channel_counts = range(channel_counts_len)
        for i in range(channel_counts_len):
            self.add_trait('channel_counts_{}'.format(i+1), Bool)
        # use self._instance_traits() to list these traits

        # create extended channel indicators
        extended_channels_len = region.region.extended_channels.shape[1]
        self.selected_extended_channels = range(extended_channels_len)
        for i in range(extended_channels_len):
            self.add_trait('extended_channels_{}'.format(i+1), Bool)

        self.all_selected_channels = self._instance_traits().values()

    def _channel_counts_changed(self, trait, old, new):
        print self.region.name, trait, old, new

    @on_trait_change( 'channel_counts_+' )
    def _channel_counts_x_changed(self, container, trait, new):
        print self.region.name, container, trait, new

    @on_trait_change( 'extended_channels_+' )
    def _extended_channels_changed(self, container, trait, new):
        print self.region.name, container, trait, new

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
        if 'channel_counts' in trait_dict:
            group1 = HGroup()
            group1.content = []
            group1.content.extend([Item('channel_counts', label='Counts')])
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
