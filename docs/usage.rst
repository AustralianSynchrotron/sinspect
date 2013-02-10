.. |degree| unicode:: U+00B0   .. degree trimming surrounding whitespace
    :ltrim:

.. _usage_root:

Usage
*****

SinSPECt is a tool for browsing SpecsLab2 SPECS .xml files for reviewing and exporting captured data.

Exported data
=============
Regions selected for export are saved as .xy files.
.xy files are ASCII files containing two optional header lines followed by columnar numerical data. Fields are TAB separated by default, allowing the file to be imported into MS Excel easily, e.g. by drag-and-drop.
Both header lines start with the # comment character. The first line contains text representations of some region-specific metadata fields and indicates whether the data is single- or double-normalised, as described below. An example is

 #"Analyzer mode:FixedAnalyzerTransmission, Dwell time:0.1, Pass energy:5.0, Lens mode:MediumArea:1.5kV, Excitation energy:700.0"

The second line contains column headings for the numeric data. An example is

 #"Binding Axis"	"Counts 1+2+3+4+5+6+7+8+9"	"Channel 1 counts"	"Channel 2 counts"	"Channel 3 counts"	"Channel 4 counts"	"Channel 5 counts"	"Channel 6 counts"	"Channel 7 counts"	"Channel 8 counts"	"Channel 9 counts"	"Extended channel 1"	"Extended channel 2"	"Extended channel 3"	"Extended channel 4"	"Extended channel 5"	"Extended channel 6"	"Extended channel 7"	"Extended channel 8"	"Extended channel 9"

An example of a row of numeric data is

 110	711	116	91	157	36	74	85	102	41	9	0	21298	75412	0	11253	0	0	56360	0

which contains the following from left-to-right: x-value, counts, 9-channeltron-channels, 9-extended-channels. Sometime, regions in the .xml file may contain no channel data or no extended channel data. In these cases, the data is zero-filled with the correct number of entries to match the number of x-values. By default, exported region data reflects the value read from the .xml file exactly. The counts value is determined by summing those channeltron channels with corresponding checked checkboxes. Unchecking a checkbox removes that channel from the sum. The contributing channels are reflected by the header of second column; e.g., "Counts 1+2+3+4+5+6+7+8+9" above indicates all channels were summed to get the values in this column. Data may also be normalised as described below under normalisation and double normalisation.

Single Normalisation
====================
Two types of normalisation are supported. Here we discuss single-normalisation.

enabling
--------
The Normalisation GUI group contains a drop-down selector labelled "ref:" which, when enabled, selects the extended channel that all y-data values will be divided by. The selector is enabled whenever an .xml SPECS data file is loaded and whenever the double-normalisation mode is not enabled. If the selector is set to "None", normalisation (aka single-normalisation) is disabled. If the selector is set to a value 1-9, normalisation is enabled.

processing
----------
During preview and export, data is processed as follows.

.. math:: \textbf{C} = \sum_i a_i\textbf{c}_i,

where :math:`\textbf{C}` is the Counts vector, :math:`i=1..9` is an index over the channels, :math:`\textbf{c}_i` is the vector of channel data, :math:`a_i` is 1 if the :math:`i` th channel is enabled or 0 otherwise.
The channels :math:`\textbf{c}_i` and extended channels :math:`\textbf{e}_i` are those values read from the .xml SPECS file.
The normalised Counts :math:`\textbf{C}'` are then

.. math:: \textbf{C}' = \textbf{C}/\textbf{e}_r,
 
where :math:`\textbf{e}_r` is the specified reference extended channel.
In addition to the Counts, the single-normalised channel counts :math:`\textbf{c}'_i` and extended channel counts :math:`\textbf{e}'_i` are determined according to

.. math:: \textbf{c}'_i = \textbf{c}_i/\textbf{e}_r,

and

.. math:: \textbf{e}'_i = \textbf{e}_i/\textbf{e}_r, i \ne r.

Here, the condition :math:`i \ne r` shows that we choose not to normalise the reference extended counts channel data to be identically 1, i.e. the exported values are simply

.. math:: \textbf{e}'_i = \textbf{e}_i, i = r.

This enables the normalisation procedure to be undone if desired, with access to only the exported data file.

Double Normalisation
====================

purpose
-------
The purpose of double-normalisation is ... (say something about why it's needed).

enabling
--------
The Normalisation GUI group contains a label Region: with the hint "(Set from right-click menu)". Double-normalisation is enabled by setting a reference region :math:`R` by right-clicking on a region in the tree editor and selecting "Set normalisation region". The Region: label then indicates the reference region and a [Clear] button appears, enabling the region to be cleared and double-normalisation to be disabled.

When enabled, the drop-down ref: selector in the Normalisation GUI group is disabled and a new GUI group "Dbl nrm ref" is enabled in the Selector panel next to the Extended Channels group. This group contains one or two drop-down selectors that enable setting of the extended channels. The group contains one drop-down selector for all regions other than the reference region. This allows selection of the extended channel :math:`\textbf{e}_r` described below.

For the reference region, the selector panel contains two drop-down selectors that allow setting of the values :math:`s` and :math:`\textbf{e}^R_r` described below.

processing
----------
During preview and export, the double normalised Counts :math:`\textbf{C}''` is

.. math:: \textbf{C}'' = \sum_i a_i\textbf{c}_i/\textbf{e}_r/(M^R/\textbf{e}^R_r),

where :math:`M^R` depends on the drop-down menu selection :math:`s \in \{ \text{Counts}, 1..9 \}` as follows.

.. math:: M^R = \textbf{e}^R_s, \text{ if } s \in 1..9,

or, if :math:`s=\text{Counts}`

.. math:: M^R = \textbf{C}^R = \sum_i a^R_i\textbf{c}^R_i, \text{ if } s=\text{Counts}.

Here :math:`\textbf{e}_r` is the reference extended channel in the current region,
:math:`\textbf{e}^R_r` is the reference extended channel in the reference region :math:`R`.
In addition to the Counts, the double-normalised channel counts :math:`\textbf{c}''_i` and extended channel counts :math:`\textbf{e}''_i` are determined according to

.. math:: \textbf{c}''_i = \textbf{c}_i/\textbf{e}_r/(M^R/\textbf{e}^R_r)

and

.. math:: \textbf{e}''_i = \textbf{e}_i/\textbf{e}_r/(M^R/\textbf{e}^R_r).

Unlike the single normalisation case, we do not bother to distinguish the case where :math:`i=r` since the exported file would not contain all the required data to undo the double normalisation procedure.