SinSPECt: A data browser for exploring Soft X-Ray Spectra
=========================================================

SinSPECt (Soft x-ray spectrum inSPECTor)
is a data explorer for Soft X-Ray spectroscopy data stored in the SPECS XML format,
released under the Modified BSD-license.

Features
--------
- Reads SPECS XML format files saved from SpecsLab2.
- Graphical exploration of data regions.
- Exports columnar ASCII with choice of delimiter and optional headers.
- Supports normalisation of data to internally available data channels.
- Cross-platform. Runs on Windows/Mac OSX/Linux

Requirements
------------
`SinSPECt`_ is written in Python 2.7 and has a number of dependencies.
We recommend the (free) `Enthought Python Distribution`_ for easy one-click installation of dependencies.
For installation instructions and details of dependencies, see the `documentation`_.

.. _`Enthought Python Distribution`: http://www.enthought.com/products/epd_free.php
.. _`documentation`: http://sinspect.readthedocs.org/en/latest/installation.html
.. _`SinSPECt`: http://www.synchrotron.org.au/sinspect

Run
---
To run, just call python on app.py

    $ python app.py

Version History
---------------
0.6     This version
        Allow reading of SPECSLab files containing Windows-cp1252 special characters
0.5     Fixed file loading to allow no scaling factors in SPECS file
0.4     Skip XPS regions when set to double-normalisation
0.3     Tagged for release to wider userbase
0.2rc2  Tagged version for evaluation by local users
0.2rc1  Tagged version for evaluation by local users
0.1     Initial tagged release for evaluation by beamline scientists