import json
from pathlib import Path
import arcpy
 

proj_path = Path(r'C:\Users\Nick.Forfinski-Sarko\Documents\ArcGIS\Projects\ShorelineAttributor')
arcpy.env.workspace = str(proj_path)
gdb = "ShorelineAttributor.gdb"
app5_json_path = Path(r'C:\Users\Nick.Forfinski-Sarko\source\repos\ShorelineAttributer\Appendix5Attributes.json')

with open(app5_json_path) as j:
    shp_atts = json.load(j)

#for gtype in shp_atts['INTERIM']:
#    atts = shp_atts['INTERIM'][gtype]

#    for ftype, att_data in atts.items():
#        print('=' * 25)
#        print(f'Feature: {ftype}')
#        print(att_data)

#        for att, values in att_data.items():
#            print('-' * 5)
#            print(f'Attribute: {att}')
#            print(json.dumps(values, indent=2))

#            name = '_'.join(('INTERIM', gtype, ftype, att))
#            desc = 'description'
#            print(name)
#            print(type(name))

#            if values['DomainType'] == 'coded':
#                arcpy.CreateDomain_management(gdb, name, desc, 'TEXT', 'CODED')
#                print(f'created domain for {name}')
#                for i, code in enumerate(values['Domain']):
#                    print(i, code)
#                    arcpy.AddCodedValueToDomain_management(gdb, name, i, code)
#                    print(f'Added {code} to attribute domain "{name}"')
#                    att_count =+ 1
#            #elif values['DomainType'] == 'range':
#            #    arcpy.SetValueForRangeDomain_management(gdb, name, min, max)



att_data = shp_atts['FINAL']['LINES']

for att, values in att_data.items():
    print('-' * 5)
    print(f'Attribute: {att}')
    print(json.dumps(values, indent=2))
    desc = values['Definition']
    dtype = values['DataType']

    if values['DomainType'] == 'coded':
        arcpy.CreateDomain_management(gdb, att, desc, dtype, 'CODED')
        print(f'created domain for {att}')
        for i, code in enumerate(values['Domain']):
            print(i, code)
            arcpy.AddCodedValueToDomain_management(gdb, att, i, code)
            print(f'Added {code} to attribute domain "{att}"')
            att_count =+ 1
    elif values['DomainType'] == 'range' and att == 'SRC_DATE':
        pass
        #arcpy.SetValueForRangeDomain_management(gdb, att, min, max)


    elif values['DomainType'] == 'range' and att != 'SRC_DATE':
        min = values['Domain'][0]
        max = values['Domain'][1]
        arcpy.CreateDomain_management(gdb, att, desc, dtype, 'RANGE')
        arcpy.SetValueForRangeDomain_management(gdb, att, min, max)


domName = "Material4"
inFeatures = "Montgomery.gdb/Water/Distribmains"
inField = "Material"
#arcpy.AssignDomainToField_management(inFeatures, inField, domName)

domains = arcpy.da.ListDomains(gdb)

for domain in domains:
    print('-' * 5)
    print(f'Domain name: {domain.name}')
    if domain.domainType == 'CodedValue':
        print(list(domain.codedValues.values()))
    #    coded_values = domain.codedValues
    #    for val, desc in coded_values.items():
    #        print(f'{val} : {desc}')
    #elif domain.domainType == 'Range':
    #    print(f'Min: {domain.range[0]}')
    #    print(f'Max: {domain.range[1]}')