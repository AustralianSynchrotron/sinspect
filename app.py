import os
from traits.api import HasTraits, Instance, Str, List
from traitsui.api import View, Group, UItem, TreeEditor, TreeNode, VSplit, \
           HGroup
from pyface.api import ImageResource
from traitsui.menu import Action
from fixes import fix_background_color
from chaco.api import OverlayPlotContainer
import specs

# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()


size = (1200, 700)
title = "SinSPECt"
app_icon = os.path.join('resources','app_icon.ico')


# Traited versions of SPECS xml file classes - used by TreeEditor widget

class SPECSRegion(HasTraits):
    name   = Str('<unknown>')
    title  = Str
    region = Instance(specs.SPECSRegion)

class SPECSGroup(HasTraits):
    name = Str('<unknown>')
    specs_regions = List(SPECSRegion)

class SpecsFile(HasTraits):
    name = Str('<unknown>')
    specs_groups = List(SPECSGroup)

    def __init__(self, s, name):
        self.name = name
        for group in s.groups:
            specs_group = SPECSGroup(name=group.name, specs_regions=[])
            for region in group.regions:
                specs_group.specs_regions.append(SPECSRegion(name=region.name, region=region))
            self.specs_groups.append(specs_group)

class Owner(HasTraits):
    name = Str('<unknown>')
    specs_file = Instance(SpecsFile)


# View for objects that aren't edited
no_view = View()

# View used for region in tree editor
region_view = View(
    VSplit(
        HGroup( '3', 'name' ),
        id = 'vsplit' ),
    id = 'treeeditor.region_view',
    dock = 'vertical' )

# Tree editor
tree_editor = TreeEditor(
    nodes = [
        TreeNode( node_for  = [SpecsFile],
                  auto_open = True,
                  children  = 'specs_groups',
                  label     = 'name',
                  view      = View( Group('name',
                                   orientation='vertical',
                                   show_left=True )),
                  add       = [SPECSGroup],
                  icon_path = 'resources',
                  icon_open = 'file.ico',
                ),

        TreeNode( node_for  = [SPECSGroup],
                  auto_open = True,
                  children  = 'specs_regions',
                  label     = 'name',
                  view      = View( Group('name',
                                   orientation='vertical',
                                   show_left=True )),
                  add       = [SPECSRegion],
                  icon_path = 'resources',
                  icon_open = 'group.ico',
                ),

        TreeNode( node_for  = [SPECSRegion],
                  auto_open = True,
                  label     = 'name',
                  view      = region_view,
                  icon_path = 'resources',
                  icon_item = 'region.ico',
                )
    ],
)

# The main view
view = View(
           Group(
               UItem(
                    name = 'specs_file',
                    editor = tree_editor,
                    resizable = True ),
                orientation = 'vertical',
                show_labels = True,
                show_left = True, ),
            title = title,
            icon = ImageResource(app_icon),
            id = 'app.main_view',
            dock = 'horizontal',
            drop_class = HasTraits,
#            buttons = [ 'OK', 'Cancel' ],
            resizable = True,
            width = .3,
            height = .3 )


filename = os.path.join('..', 'test_data', 'Test.xml')
s = specs.SPECS(filename)
owner = Owner(name=filename, specs_file=SpecsFile(s, name=filename))


#class MainApp(HasTraits):
#    container = Instance(OverlayPlotContainer)
#    s = specs.SPECS(os.path.join('..', 'test_data', 'Test.xml'))
#    print 'hello'


_info_text = \
"""
Plot region usage:
Left drag = Zoom a selection of the plot
Right drag = Pan the plot
Right click = Undo zoom
Esc = Reset zoom/pan
Mousewheel = Zoom in/out

Please send bug reports and suggestions to
sinspect@synchrotron.org.au

Software authors:
Gary Ruben, Victorian eResearch Strategic Initiative (VeRSI), gruben@versi.edu.au
Kane O'Donnell, Australian Synchrotron
http://www.versi.edu.au

Software home:
http://www.synchrotron.org.au/sinspect
Software source:
http://github.com/AustralianSynchrotron/sinspect

Recognition of NeCTAR funding:
The Australian Synchrotron is proud to be in partnership with the National eResearch Collaboration Tools and
Resources (NeCTAR) project to develop eResearch Tools for the synchrotron research community. This will enable our
scientific users to have instant access to the results of data during the course of their experiment which will
facilitate better decision making and also provide the opportunity for ongoing data analysis via remote access.

Copyright (c) 2012, Australian Synchrotron Company Ltd
All rights reserved.
"""


if __name__ == "__main__":
    owner.configure_traits(view=view)
