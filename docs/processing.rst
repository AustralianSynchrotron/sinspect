.. |degree| unicode:: U+00B0   .. degree trimming surrounding whitespace
    :ltrim:

.. _processing_root:

Processing
**********

This page describes the processing that SinSPECt performs.

Exported data
=============
Regions selected for export are saved as .xy files.
.xy files are ASCII files containing two optional header lines followed by columnar numerical data. Fields are TAB separated by default, allowing the file to be imported into MS Excel easily, e.g. by drag-and-drop.
Both header lines start with the # comment character. The first line contains text representations of some region-specific metadata fields and indicates whether the data is single- or double-normalised, as described below. An example is::

 #"Analyzer mode:FixedAnalyzerTransmission, Dwell time:0.1, Pass energy:5.0, Lens mode:MediumArea:1.5kV, Excitation energy:700.0"

The second line contains column headings for the numeric data. An example is::

 #"Binding Axis" "Counts 1+2+3+4+5+6+7+8+9" "Channel 1 counts" "Channel 2 counts" "Channel 3 counts" "Channel 4 counts" "Channel 5 counts" "Channel 6 counts" "Channel 7 counts" "Channel 8 counts" "Channel 9 counts" "Extended channel 1" "Extended channel 2" "Extended channel 3" "Extended channel 4" "Extended channel 5" "Extended channel 6" "Extended channel 7" "Extended channel 8" "Extended channel 9"

An example of a row of numeric data is::

 110 711 116 91 157 36 74 85 102 41 9 0 21298 75412 0 11253 0 0 56360 0

which contains the following from left-to-right: x-value, counts, 9-channeltron-channels, 9-extended-channels. Occasionally regions in the .xml file may contain no channel data or no extended channel data. In these cases, the data is zero-filled with the correct number of entries to match the number of x-values. By default, exported region data reflects the value read from the .xml file exactly. The counts value is determined by summing those channeltron channels with corresponding checked checkboxes. Unchecking a checkbox removes that channel from the sum. The contributing channels are reflected by the header of second column; e.g., "Counts 1+2+3+4+5+6+7+8+9" above indicates all channels were summed to get the values in this column. Data may also be normalised as described below under normalisation and double normalisation.

.. note:: SinSPECt exports raw Channeltron Channel Counts, not counts per second. If you want to convert to counts per second in your analysis, you will need to divide exported counts values by the Dwell time.

Data normalisation
==================
SinSPECt operates in one of three modes: 1. No processing, 2. Single normalisation, 3. Double normalisation.

No processing
-------------
In this mode all displayed plots and exported data correspond to the raw channeltron and extended-channel data.

.. note:: Enabling No processing mode

    This mode is enabled when the drop-down selector in the "Normalisation by chosen I0" GUI group is disabled or set to "None" and when the double-normalisation mode is disabled, indicated by the toolbar 'X' button being greyed-out.

Single Normalisation
--------------------
In Single-normalisation mode, all displayed and exported data is divided by the data in the selected extended channel :math:`\textbf{e}_r` (the data in the selected extended channel is left unnormalised).

.. note:: Enabling Single Normalisation mode

    The "Normalisation by chosen I0" GUI group contains a drop-down selector labelled "ref:" which selects the extended channel that all y-data values will be divided by. The selector is enabled whenever an .xml SPECS data file is loaded and whenever the double-normalisation mode is not enabled. If the selector is set to "None", all normalisation is disabled: plots and exported data will correspond to the raw data. If the selector is set to a value 1-9, normalisation is enabled.

.. warning::

    It is possible to set the reference channel :math:`\textbf{e}_r` to an extended channel that may contain zeros in some regions, resulting in divide-by-zero errors. In this case, the plot window will be blank and errors will be produced for exported regions that cause errors. If any errors occurred during export, a notification is displayed, the filenames of affected .xy data files are prepended with the text *ERRORS_*, and a header line indicating the error is written to the file.

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
--------------------
In Double-normalisation mode, all displayed and exported data is divided first by the extended channel specified for that region then further by the ratio of the two channels specified in a reference region (the data in the selected extended channel is left unnormalised).

.. note:: Enabling Double Normalisation mode

    Clicking the bookmark toolbar button enables double normalisation and sets the currently selected region as the reference region :math:`R` . The text *(ref)* appears in the label alongside the reference region in the tree editor to indicate this. Clicking the 'X' button adjacent to the bookmark clears double normalisation mode.
    When double normalisation is enabled, drop-down selectors appear to the right of the selection panel checkboxes. These enable setting of the extended channels used to compute the double-normalised results.
    For all regions other than the reference region, the group contains one drop-down selector. This allows selection of the extended channel :math:`\textbf{e}_r` (see description below).
    For the reference region, the selector panel contains two drop-down selectors that allow setting of the values :math:`s` and :math:`\textbf{e}^R_r` (see description below).

.. warning::

    It is possible to set the reference extended channel in the current reion :math:`\textbf{e}_r` or that of the reference region :math:`\textbf{e}^R_r` to a channel that may contain zeros in some regions, or whose x-axis ranges differ. In both cases, the plot window will be blank and errors will be produced for exported regions that cause these error types. If any errors occurred during export, a notification is displayed, the filenames of affected .xy data files are prepended with the text *ERRORS_*, and a header line indicating the error is written to the file.


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

As for the single normalisation case, we choose not to normalise the reference extended counts channel data to be identically 1, i.e. the exported values are simply

.. math:: \textbf{e}''_i = \textbf{e}_i, i = r.

In order to enable the normalisation procedure to be undone if desired, a column is appended that contains the :math:`M^R/\textbf{e}^R_r` values, allowing reversal of the processing with access to only the exported data file.