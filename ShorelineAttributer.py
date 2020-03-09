import os
import pandas as pd
import geopandas as gpd
from pathlib import Path
import arcpy
import arcpy.cartography as CA
from datetime import datetime
from shapely.geometry import Polygon, MultiLineString
from shapely import wkt, wkb

from Schema import Schema


class ShorelineTile():

    def __init__(self, params, schema):
        self.set_params(params)
        self.schema = schema
        self.path = None
        self.srs = None
        self.gdf = None
        self.simp_tolerance = 0.25
        self.smooth_threshold = 5

    def set_params(self, params):
        for i, p in enumerate(params):
            self.__dict__[p.name] = p.value

    def populate_gdf(self, shp):
        self.path = shp.parent / (arcpy.ValidateTableName(shp.stem) + '.shp')
        self.srs = arcpy.Describe(str(shp)).spatialReference
        self.gdf = gpd.read_file(str(shp))

    def export(self, out_path):
        self.gdf.to_file(out_path, driver='ESRI Shapefile')

    def apply_tile_attributes(self):
        for attr in self.schema.atypes['tile']:
            if attr != 'SRC_DATE':
                self.gdf[attr] = self.__dict__[attr]
            elif attr == 'SRC_DATE':  # dytpe is datetime64 (can't be)
                self.gdf[attr] = datetime.strftime(self.__dict__[attr], '%Y%m%d')

    def apply_state_region_attributes(self, state_regions):
        if state_regions.shape[0] == 1:
            self.gdf['ATTRIBUTE'] = None
            self.gdf['FIPS_ALPHA'] = state_regions.iloc[0]['STATE_FIPS']
            self.gdf['NOAA_Regio'] = state_regions.iloc[0]['NOAA_Regio']
        elif state_regions.shape[0] > 1:
            shoreline_gdfs = []
            for i, state_region in state_regions.iterrows():
                arcpy.AddMessage('get shoreline intersecting state_region...')
                sindex = self.gdf.sindex
                intersect_idx = list(sindex.intersection(state_region.geometry.bounds))
                possible_shoreline = self.gdf.iloc[intersect_idx]

                arcpy.AddMessage('clip intersecting shoreline with region...')
                multilinestring = MultiLineString(list(possible_shoreline.geometry))
                shoreline = multilinestring.intersection(state_region.geometry)
                shoreline = gpd.GeoDataFrame(geometry=[shoreline], crs=self.gdf.crs)
                cols_to_drop = ['level_0', 'level_1']
                shoreline = shoreline.explode().reset_index().drop(cols_to_drop, axis=1)

                arcpy.AddMessage('attribute state_region shoreline...')
                shoreline['ATTRIBUTE'] = None
                shoreline['FIPS_ALPHA'] = state_region['STATE_FIPS']
                shoreline['NOAA_Regio'] = state_region['NOAA_Regio']

                shoreline_gdfs.append(shoreline)

            df = pd.concat(shoreline_gdfs, ignore_index=True)
            self.gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=self.gdf.crs)

    def simplify(self):
        self.gdf['geometry'] = self.gdf.geometry.simplify(tolerance=self.simp_tolerance,
                                                          preserve_topology=False)

    def smooth_esri(self):
        geom_bytearray = bytearray(MultiLineString(list(self.gdf.geometry)).wkb)
        arc_geom = arcpy.FromWKB(geom_bytearray, self.srs)
        smoothed_geom = CA.SmoothLine(arc_geom, arcpy.Geometry(), "PAEK", self.smooth_threshold)
        geom_wkb = bytes(smoothed_geom[0].WKB)
        self.gdf = gpd.GeoDataFrame(geometry=[wkb.loads(geom_wkb)], crs=self.gdf.crs).explode()

    def get_overlapping_state_regions(self, state_regions):
        sindex = state_regions.to_crs(self.gdf.crs).sindex
        extents = self.get_tile_extents()
        region_states_idx = list(sindex.intersection(extents.bounds))
        return state_regions.iloc[region_states_idx]

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

    schema_path = Path(r'.\shoreline_schema.json')
    schema = Schema(schema_path)

    slt = ShorelineTile(arcpy.GetParameterInfo(), schema)

    state_regions_path = Path(r'.\support\state_regions.shp')
    state_regions = gpd.read_file(str(state_regions_path))

    shps = [Path(shp) for shp in slt.shp_paths.exportToString().split(';')]
    num_shps = len(shps)

    for i, shp in enumerate(shps, 1):
        arcpy.AddMessage('{} ({} of {})...'.format(shp.name, i, num_shps))
        slt.populate_gdf(shp)

        arcpy.AddMessage('simplifying...')
        slt.simplify()

        arcpy.AddMessage('smoothing...')
        slt.smooth_esri()

        if not slt.gdf.empty:
            arcpy.AddMessage('determining overlapping state NOAA regions...')
            tile_state_regions = slt.get_overlapping_state_regions(state_regions)

            arcpy.AddMessage('applying state-region attributes...')
            slt.apply_state_region_attributes(tile_state_regions)

            arcpy.AddMessage('applying tile-wide attributes...')
            slt.apply_tile_attributes()

            arcpy.AddMessage('outputing attributed gdf...')
            out_path = Path(slt.out_dir.value) / '{}_ATTRIBUTED_.shp'.format(shp.stem)
            slt.export(str(out_path))
