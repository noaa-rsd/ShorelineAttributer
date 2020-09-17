import json
from pathlib import Path
import arcpy
 

proj_path = Path(r'C:\Users\Nick.Forfinski-Sarko\Documents\ArcGIS\Projects\ShorelineAttributor')

arcpy.env.workspace = str(proj_path)

domName = "Material4"
gdb = "ShorelineAttributor.gdb"
inFeatures = "Montgomery.gdb/Water/Distribmains"
inField = "Material"
 
app5_json_path = Path(r'C:\Users\Nick.Forfinski-Sarko\source\repos\ShorelineAttributer\Appendix5Attributes.json')

with open(app5_json_path) as j:
    shp_atts = json.load(j)

line_atts = shp_atts['INTERIM']['LINES']

for att, att_data in line_atts.items():
    print('=' * 25)
    print(att)
    print(att_data)

    arcpy.CreateDomain_management(gdb, att, 'description', 'TEXT', 'CODED')

    for i, val in enumerate(att_data['TYPE']['Domain']):        
        arcpy.AddCodedValueToDomain_management(gdb, att, i, val)
    
#arcpy.AssignDomainToField_management(inFeatures, inField, domName)