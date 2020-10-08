import os
from collections import OrderedDict
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import arcpy
import arcpy.cartography as CA
from datetime import datetime
from shapely.geometry import Polygon, MultiLineString
from shapely import wkb

from Schema import Schema


class ShorelineTile():

    def __init__(self, params, schema):
        self.set_params(params)
        self.schema = schema
        self.path = None
        self.srs = None
        self.gdf = None
        self.numeric_nodata = -1
        self.lut_gdf = self.get_ccoast_lut()
        arcpy.AddMessage(self.lut_gdf)
        #self.Simplification_Tolerance from self.set_params
        #self.Smoothing_Threshold from self.set_params

    def set_params(self, params):
        for i, p in enumerate(params):
            self.__dict__[p.name] = p.value

    def populate_gdf(self, shp):
        self.path = shp.parent / (arcpy.ValidateTableName(shp.stem) + '.shp')
        self.srs = arcpy.Describe(str(shp)).spatialReference
        self.gdf = gpd.read_file(str(shp))

    def export(self, out_path):
        shp_schema = {
            'properties': OrderedDict([
                ('DATA_SOURC', 'str:1'), 
                ('FEATURE', 'int:5'), 
                ('EXTRACT_TE', 'str:1'), 
                ('RESOLUTION', 'int:5'), 
                ('CLASS', 'str:32'), 
                ('ATTRIBUTE', 'str:50'), 
                ('INFORM', 'str:50'), 
                ('HOR_ACC', 'float:6.4'), 
                ('SRC_DATE', 'str:8'), 
                ('SOURCE_ID', 'str:8'), 
                ('EXT_METH', 'str:1')]),
            'geometry': 'LineString'}
        arcpy.AddMessage(self.gdf)
        arcpy.AddMessage(self.gdf.columns)
        self.gdf = self.gdf.reset_index(drop=True)
        self.gdf.to_file(out_path, driver='ESRI Shapefile', schema=shp_schema)

    def get_ccoast_lut(c):
        cwd = os.path.dirname(os.path.realpath(__file__))
        os.chdir(cwd)
        lut_path = Path(r'.\ccoast_lut - sow15.xlsx')
        return pd.read_excel(lut_path)

    def get_ccoast_code(self, attr, val):
        return self.lut_gdf.loc[self.lut_gdf[attr] == val, 'CODE'].iloc[0]

    def get_ccoast_class(self, attr, val):
        return self.lut_gdf.loc[self.lut_gdf[attr] == val, 'CLASS'].iloc[0]

    def apply_attributes(self):
        dtype_mapping = {'TEXT': 'string', 
                         'SHORT': 'Int64',
                         'FLOAT': 'float',
                         'DATE': 'string'}

        cols = ['geometry'] + self.schema.atypes['tile']
        self.gdf = self.gdf.reindex(columns=cols)

        dtypes = {}
        arcpy.AddMessage(self.__dict__)
        for attr in self.schema.atypes['tile']:
            val = self.__dict__[attr]
            arcpy.AddMessage(f'populating attribute {attr}: {val}')
            scheme_dtype = self.schema.__dict__[attr]['DataType']
            dtypes[attr] = dtype_mapping[scheme_dtype]
            if val:
                if attr == 'ATTRIBUTE':
                    self.gdf[attr] = val
                    self.gdf['FEATURE'] = self.get_ccoast_code(attr, val)
                    self.gdf['CLASS'] = self.get_ccoast_class(attr, val) 
                elif attr == 'SRC_DATE':  # dtype is datetime64 (can't be)
                    self.gdf[attr] = datetime.strftime(self.__dict__[attr], '%Y%m%d')
                elif attr == 'EXTRACT_TE':
                    self.gdf[attr] = val.split(':')[0]
                elif attr == 'DATA_SOURC':
                    self.gdf[attr] = val.split(':')[0]
                elif attr == 'EXT_METH':
                    self.gdf[attr] = val.split(':')[0]                
                else:
                    self.gdf[attr] = val
            elif attr == 'RESOLUTION' or attr == 'HOR_ACC':
                self.gdf[attr] = self.numeric_nodata

        arcpy.AddMessage(dtypes)
        df = self.gdf.astype(dtypes)
        self.gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=self.gdf.crs)

    def simplify(self):
        geom = self.gdf.geometry.simplify(tolerance=self.Simplification_Tolerance,
                                          preserve_topology=False)
        self.gdf['geometry'] = geom

    def smooth_esri(self):
        self.gdf = self.gdf.drop(columns=['ID'])
        arcpy.AddMessage(self.gdf)
        geom_bytearray = bytearray(MultiLineString(list(self.gdf.geometry)).wkb)
        arc_geom = arcpy.FromWKB(geom_bytearray, self.srs)
        smoothed_geom = CA.SmoothLine(arc_geom, arcpy.Geometry(), "PAEK", 
                                      self.Smoothing_Threshold)
        geom_wkb = bytes(smoothed_geom[0].WKB)
        geom = [wkb.loads(geom_wkb)]
        self.gdf = gpd.GeoDataFrame(geometry=geom, crs=self.gdf.crs).explode()

    def get_tile_extents(self):
        bounds = self.gdf.geometry.bounds
        minx = bounds['minx'].min()
        miny = bounds['miny'].min()
        maxx = bounds['maxx'].max()
        maxy = bounds['maxy'].max()
        poly_coords = [(minx, miny), (minx, maxy), 
                       (maxx, maxy), (maxx, miny)]
        return Polygon(poly_coords)


def set_env_vars(env_name):
    user_dir = os.path.expanduser('~')
    path_parts = ('AppData', 'Local', 
                  'Continuum', 'anaconda3')
    conda_dir = Path(user_dir).joinpath(*path_parts)
    env_dir = conda_dir / 'envs' / env_name
    share_dir = env_dir / 'Library' / 'share'
    script_path = conda_dir / 'Scripts'
    gdal_data_path = share_dir / 'gdal'
    proj_lib_path = share_dir

    if script_path.name not in os.environ['PATH']:
        os.environ['PATH'] += os.pathsep + str(script_path)
    os.environ['GDAL_DATA'] = str(gdal_data_path)
    os.environ['PROJ_LIB'] = str(proj_lib_path)


if __name__ == '__main__':

    set_env_vars('shore_att')
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    schema_path = Path(r'.\Appendix5Attributes.json')
    schema = Schema(schema_path)

    tile = ShorelineTile(arcpy.GetParameterInfo(), schema)

    shps = [Path(shp) for shp in tile.shp_paths.exportToString().split(';')]
    num_shps = len(shps)

    for i, shp in enumerate(shps, 1):
        arcpy.AddMessage('{} ({} of {})...'.format(shp.name, i, num_shps))
        tile.populate_gdf(shp)

        arcpy.AddMessage('simplifying...')
        tile.simplify()

        arcpy.AddMessage('smoothing...')
        tile.smooth_esri()

        if not tile.gdf.empty:
            arcpy.AddMessage('applying tile-wide attributes...')
            tile.apply_attributes()

            arcpy.AddMessage('outputing attributed gdf...')
            out_path = Path(tile.out_dir.value) / f'{shp.stem}_ATTRIBUTED_.shp'
            tile.export(str(out_path))
