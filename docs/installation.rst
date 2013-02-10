.. _installation_root:

***************
Installation
***************

SinSPECt is written in `Python <http://python.org>`_ (2.7 at the time of writing) and has several module dependencies that require installation. For Windows, Linux and Mac users the easiest way to install these dependencies is to install one of the `Enthought Python Distributions <http://www.enthought.com/products/epd.php>`_. The `EPDFree <http://www.enthought.com/products/epd_free.php>`_ distribution contains all the modules on which SinSPECt depends. A typical user can just download and install EPDFree then download and unpack SinSPECt and run it immediately.

Some users might prefer alternatives to EPDFree. For example Academic or Commercial users may prefer to use one of Enthought's other distributions. Other popular Python distributions include `Python(x,y) <http://code.google.com/p/pythonxy/>`_, `WinPython <http://code.google.com/p/winpython/>`_ and ActiveState's `ActivePython <http://www.activestate.com/activepython/downloads>`_, all of which will require installation of at least some of the following dependencies:

.. _python_package_dependencies:

Python package dependencies
---------------------------------

SinSPECt depends on the following Python modules being installed in the Python environment

* `numpy <http://numpy.scipy.org/>`_
* `traits <http://code.enthought.com/projects/traits/>`_ [part of the Enthought Tool Suite (ETS) package]
* `traitsui <http://code.enthought.com/projects/traits_ui/>`_ (part of ETS)
* `chaco <http://code.enthought.com/projects/chaco/>`_ (part of ETS)
* `pyface <http://code.enthought.com/projects/traits_gui/>`_ (part of ETS)
* `wxPython <http://wxpython.org/>`_

Those wishing to build the documentation from source will also need `Sphinx <http://sphinx.pocoo.org/>`_.
For those familiar with installing Python packages, the dependencies can be found in the `central repository of Python modules <http://pypi.python.org/pypi>`_. For Microsoft Windows users, Christoph Gohlke (C.G.) maintains a useful `repository of Windows installers <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ for many modules. Linux users can typically find the dependencies using their package manager (e.g. synaptic or yum). Mac users should visit the individual sites linked above for instructions.

.. _example1:

Example 1. Windows installation using Enthought Python Distribution (recommended)
---------------------------------------------------------------------------------

#. Visit the `SinSPECt download page <http://www.synchrotron.org.au/sinspect>`_ and follow the instructions to obtain the EPD Free Python installer and the SinSPECt installer files for Windows. You may wish to visit the `Enthought website <http://www.enthought.com/products/epd.php>`_, directly, and choose one of Enthought's other Python distributions. Note, `EPD Free <http://www.enthought.com/products/epd_free.php>`_ satisfies the dependencies listed above.
#. Run the epd_free-\*.msi installer to install EPD Free.
#. Verify that Python is running correctly.
   e.g. for Windows 7, click on ``Start Menu|All Programs|Accessories|Command Prompt``.
   At the ``>`` prompt type ``python -c "print 'hello world'"`` noting single and double quotes.
   Verify that ``hello world`` is displayed.
#. Running the SinSPECt installer will install SinSPECt and create a start menu entry.

Example 2. Windows installation using Python(x,y) (optional)
------------------------------------------------------------

#. Visit the `Python(x,y) <http://code.google.com/p/pythonxy/>`_ `downloads page <http://code.google.com/p/pythonxy/wiki/Downloads>`_ and install a distribution.
#. Verify that Python is running correctly (see :ref:`example1`).
#. Visit the `SinSPECt download page <http://www.synchrotron.org.au/sinspect>`_ and follow the instructions to obtain the SinSPECt setup file.
#. Running the installer will install SinSPECt and create a start menu entry.

Example 3. Windows installation on a system with Python already installed (experienced)
---------------------------------------------------------------------------------------

Note: untested.

#. Check the :ref:`package dependency list<python_package_dependencies>` above.
#. The easiest way here is to use the packages provided by `Python(x,y) <http://code.google.com/p/pythonxy/wiki/StandardPlugins>`_ and/or `Christoph Gohlke <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_. Install the required dependency, taking care to choose packages for Python 2.7 and to choose the 32 or 64 bit package version that matches your Python version.
   Install in turn ``numpy`` (if in doubt choose the numpy-MKL-... version), ``scipy``,
   ``matplotlib``, ``wxPython``, and finally ``ETS``.

Example 4. Linux installation using Enthought Python Distribution (recommended)
-------------------------------------------------------------------------------

#. Visit the `SinSPECt download page <http://www.synchrotron.org.au/sinspect>`_ and follow the instructions to obtain the EPD Free Python installer and the SinSPECt .zip package for Linux. You may wish to visit the `Enthought website <http://www.enthought.com/products/epd.php>`_, directly, and choose one of Enthought's other Python distributions. Note, `EPD Free <http://www.enthought.com/products/epd_free.php>`_ satisfies the dependencies listed above.
#. Run the epd_free-\*.sh shell script to install EPD Free.
#. Verify that Python is running correctly.
   e.g. for Ubuntu, open a terminal.
   At the ``$`` prompt type ``python -c "print 'hello world'"`` noting single and double quotes.
   Verify that ``hello world`` is displayed.
#. The main SinSPECt application file is ``app.py`` in the directory into which SinSPECt was unpacked.
#. SinSPECt can be started by running ``./start_sinspect.sh`` or ``./app.py``. To do this,
   at the ``$`` prompt type ``chmod 777 start_sinspect.sh app.py`` followed by, for example, ``./start_sinspect.sh``

Example 5. Linux installation using synaptic (experienced)
----------------------------------------------------------

Note: untested.

This description is for Ubuntu Linux. yum packaged names in Fedora Linux flavours should have similar names.

#. First, verify that Python2.7 is running correctly.
   e.g. for Ubuntu, open a terminal.
   At the ``$`` prompt type ``python -c "import sys; print sys.version"``.
   Verify that a string displays identifying a 2.7 branch version of Python.
#. Using synaptic or ``apt-get install <package>`` install the following packages: ``python-numpy``, ``python-scipy``, ``python-matplotlib``, ``python-traits``, ``python-traitsui``, ``python-chaco``, ``python-pyface``, ``python-wxgtk2.8``
#. Visit the `SinSPECt download page <http://www.synchrotron.org.au/sinspect>`_ and follow the instructions to obtain the package.
#. The main application file is ``app.py`` in the directory into which SinSPECt was unpacked.
#. SinSPECt can be started by running ``./start_sinspect.sh`` or ``./app.py``. To do this,
   at the ``$`` prompt type ``chmod 777 start_sinspect.sh app.py`` followed by, for example, ``./start_sinspect.sh``

Example 6. Mac OSX installation (recommended)
---------------------------------------------

#. Visit the `SinSPECt download page <http://www.synchrotron.org.au/sinspect>`_ and follow the instructions to obtain the EPD Free Python installer and the SinSPECt .zip package for Mac OSX. You may wish to visit the `Enthought website <http://www.enthought.com/products/epd.php>`_, directly, and choose one of Enthought's other Python distributions. Note, `EPD Free <http://www.enthought.com/products/epd_free.php>`_ satisfies the dependencies listed above.
#. Run the epd_free-\*.dmg installer to install EPD Free.
#. Move the .zip package to the Applications folder.
#. Double click the Application .zip package to unpack it the first time.
#. Now you can double click the package to start SinSPECt.
