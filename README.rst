Shoreline Attributer
--------------------

Shoreline Attributer is an ArcPro Python tool that attributes line features according to a subset of the CUSP schema.

Installation
============

Installing Shoreline Attributer consists of 2 main steps:

1. create/configure ArcPro Python environment

2. obtain/load Shoreline Attributer toolbox

1. create/configure ArcPro Python environment
+++++++++++++++++++++++++++++++++++++++++++++

1.1 Clone the default ArcPro Python environment by issueing the following command at an Anaconda prompt:
::

  conda create --clone "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3" --prefix C:\Users\<user>\AppData\Local\Continuum\anaconda3\envs\shore_att
  
1.2 Install the Python package Geopandas

First, uninstall the default gdal package with the following command (at the Anaconda prompt):
::  

  conda uninstall gdal
  
Second, install the Geopandas package with the following command (at the Anaconda prompt):
::

  conda install geopandas
  
1.3 Configure ArcPro Python environment

Point ArcPro to the newly created CUSP Ruler Python environment, as shown below:

.. image:: ./support/installation.png