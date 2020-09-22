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

for gtype in shp_atts['INTERIM']:
    atts = shp_atts['INTERIM'][gtype]

    for ftype, att_data in atts.items():
        print('=' * 25)
        print(f'Feature: {ftype}')
        print(att_data)

        for att, values in att_data.items():
            print('-' * 5)
            print(f'Attribute: {att}')
            print(json.dumps(values, indent=2))

            name = '_'.join(('INTERIM', gtype, ftype, att))
            desc = 'description'
            print(name)
            print(type(name))

            if values['DomainType'] == 'coded':
                arcpy.CreateDomain_management(gdb, name, desc, 'TEXT', 'CODED')
                print(f'created domain for {name}')
                for i, code in enumerate(values['Domain']):
                    print(i, code)
                    arcpy.AddCodedValueToDomain_management(gdb, name, i, code)
                    print(f'Added {code} to attribute domain "{name}"')
                    att_count =+ 1
            #elif values['DomainType'] == 'range':
            #    arcpy.SetValueForRangeDomain_management(gdb, name, min, max)



for gtype in shp_atts['FINAL']:
    att_data = shp_atts['FINAL'][gtype]

    for att, values in att_data.items():
        print('-' * 5)
        print(f'Attribute: {att}')
        print(json.dumps(values, indent=2))

        name = '_'.join(('FINAL', gtype, att))
        desc = 'description'
        print(name)
        print(type(name))

        if values['DomainType'] == 'coded':
            arcpy.CreateDomain_management(gdb, name, desc, 'TEXT', 'CODED')
            print(f'created domain for {name}')
            for i, code in enumerate(values['Domain']):
                print(i, code)
                arcpy.AddCodedValueToDomain_management(gdb, name, i, code)
                print(f'Added {code} to attribute domain "{name}"')
                att_count =+ 1
        elif values['DomainType'] == 'range' and att == 'SRC_DATE':
            pass
            #arcpy.SetValueForRangeDomain_management(gdb, name, min, max)
        elif values['DomainType'] == 'range' and att != 'SRC_DATE':
            desc = values['Definition']
            dtype = values['DataType']
            min = values['Domain'][0]
            max = values['Domain'][1]
            arcpy.CreateDomain_management(gdb, name, desc, dtype, "RANGE")
            arcpy.SetValueForRangeDomain_management(gdb, name, min, max)




#arcpy.AssignDomainToField_management(inFeatures, inField, domName)