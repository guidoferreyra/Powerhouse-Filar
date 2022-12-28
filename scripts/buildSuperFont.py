"""
    Create combined for building VF
"""
import os
import shutil
import argparse
from fontTools.designspaceLib import (DesignSpaceDocument, RuleDescriptor, AxisDescriptor, AxisLabelDescriptor, VariableFontDescriptor, RangeAxisSubsetDescriptor)
from fontParts.world import OpenFont
import subprocess


OUT_PATH = 'fonts/ttf-vf'    
ROOT = './temp'

sourcesData = [
        {   
            'name': 'Proportional',
            'designspace': 'sources/PowerhouseFilar.designspace', 
            'min': 0, 'max': 0.999, 'value': 0, 'elidable': True,
        },
        {   
            'name': 'Octo',
            'designspace': 'sources/PowerhouseFilarOcto.designspace', 
            'min': 1, 'max': 1.999, 'value': 1, 'elidable': False
        },
        {   
            'name': 'Quarto',
            'designspace': 'sources/PowerhouseFilarQuarto.designspace', 
            'min': 2, 'max': 2.999, 'value': 2, 'elidable': False
        },
        {   
            'name': 'Trio',
            'designspace': 'sources/PowerhouseFilarTrio.designspace', 
            'min': 3, 'max': 3.999, 'value': 3, 'elidable': False
        },
        {   
            'name': 'Mono',
            'designspace': 'sources/PowerhouseFilarMono.designspace',
            'min': 4, 'max': 5, 'value': 4, 'elidable': False
        }
    ]

def copyGlyphs(originUFO, destinationUFO, suffix):
    addedGlyphs = []
    for glyph in originUFO:
        if glyph.width != destinationUFO[glyph.name].width:
            newGlyph = glyph.copy()
            newGlyphName = glyph.name + suffix
            newGlyph.name = newGlyphName
            newGlyph.unicodes = ""
            for component in newGlyph.getComponents():
                if originUFO[component.baseGlyph].width != destinationUFO[component.baseGlyph].width:
                    component.baseGlyph = component.baseGlyph + suffix

            destinationUFO.insertGlyph(newGlyph)
            addedGlyphs.append(newGlyphName)
    
    return(destinationUFO, addedGlyphs)

def copyFiles(designspacePath, outRoot):
    """
    Copies the supplied designspace and all of it's sources to *outRoot*
    This updates the source paths in the the designspace file.
    *designspacePath* is a `string` of the path to a designspace file
    *outRoot* is a `string` of the root directory to copy files to
    """

    ignore = shutil.ignore_patterns(".git", ".git*")

    os.mkdir(outRoot)

    newDesignspacePath = os.path.join(outRoot, os.path.split(designspacePath)[1])

    shutil.copy(designspacePath, newDesignspacePath)

    ds = DesignSpaceDocument.fromfile(designspacePath)
    sources = [source.path for source in ds.sources]
    paths = {}
    for fontPath in sources:
        f = os.path.split(fontPath)[1]
        newPath = os.path.join(outRoot, f)
        paths[f] = newPath
        shutil.copytree(fontPath, newPath, ignore=ignore)

    ds = DesignSpaceDocument.fromfile(newDesignspacePath)
    for source in ds.sources:
        source.path = paths[os.path.split(source.path)[1]]
    ds.write(newDesignspacePath)

    return newDesignspacePath

def prepSources(designspacePath, sourcesData):
    designspace = DesignSpaceDocument.fromfile(designspacePath)

    # Make a dictionary with the base fonts to modify later
    baseUFOs = {}
    for source in designspace.sources:
        baseUFOs[source.location['Weight']] = OpenFont(source.path)
    
    # Change UFO Metadata
    for key, baseUfo in baseUFOs.items():
        baseUfo.info.familyName = f"Powerhouse Filar Super VF"

    # ----------------------- Add UNIT Axis to designspace ----------------------- #
    axisMinValue = min([data['min'] for data in sourcesData])
    axisMaxValue = max([data['max'] for data in sourcesData])

    unitAxis = AxisDescriptor(tag='UNIT', name="Unitisation", maximum=axisMaxValue, minimum=0, default=0)
    
    # Add STAT Labels
    for sourceData in sourcesData:
        unitAxis.axisLabels.append(AxisLabelDescriptor(name=sourceData['name'], userMinimum=sourceData['min'], userMaximum=sourceData['max'], userValue=sourceData['value'], elidable=sourceData['elidable']))
    
    # Add UNIT axis at the top of the axes list
    designspace.axes.insert(0, unitAxis)
    # designspace.axes.reverse()

    
    # -------------------------- Add other glyphs to UFO ------------------------- #
    for otherSourceData in sourcesData[1:]:
        otherDspace = DesignSpaceDocument.fromfile(otherSourceData['designspace'])

        otherSourceName = otherSourceData['name']
        otherSourceMinCondition = otherSourceData['min']
        otherSourceMaxCondition = otherSourceData['max']

        # Create substitution rule
        ruleSubstitutions = []
        for otherSource in otherDspace.sources:
            otherSourceUFO = OpenFont(otherSource.path)

            otherSourceWeightLocation = otherSource.location['Weight']
            
            baseFont = baseUFOs[otherSourceWeightLocation]
            
            # Add Glyph
            mergedUFO, addedGlyphs = copyGlyphs(otherSourceUFO, baseFont, "." + otherSourceName.lower())
            
            for addedGlyph in addedGlyphs:
                sub = (addedGlyph.rsplit(".", 1)[0], addedGlyph)
                print (sub)
                if sub not in ruleSubstitutions:
                    ruleSubstitutions.append(sub)
            # for glyph in otherSourceUFO:
            #     if glyph.width != baseFont[glyph.name].width:
            #         newGlyphName = glyph.name + "." + otherSourceName.lower()
            #         glyphToAdd = glyph.copy()
            #         glyphToAdd.unicode = None
            #         baseFont.insertGlyph(glyphToAdd, name=newGlyphName)
                    
            #         if (glyph.name, newGlyphName) not in ruleSubstitutions:
            #             ruleSubstitutions.append((glyph.name, newGlyphName))
            

            mergedUFO.save()
            # baseFont.save()

        # Add feature variatios Rules
        rule = RuleDescriptor(name=otherSourceName, conditionSets=[
            [
                {'name': 'Unitisation', 'minimum': otherSourceMinCondition, 'maximum': otherSourceMaxCondition},
                {'name': 'Weight', 'minimum': 400, 'maximum': 700}
            ]
        ])
        for sub in ruleSubstitutions:
            rule.subs.append(sub)
        designspace.rules.append(rule)


    # ------------------------------- Add instances ------------------------------ #
    designspace.instances = []
    for sourceData in sourcesData:
        otherDspace = DesignSpaceDocument.fromfile(sourceData['designspace'])

        for instance in otherDspace.instances:
            if not sourceData['elidable']:
                instance.styleName = f"{sourceData['name']} {instance.styleName}"
            else:
                instance.styleName = instance.styleName

            instance.designLocation['Unitisation'] = sourceData['value']
            designspace.instances.append(instance)
        

    # ------------------------ Add Variable fonts settings ----------------------- #
    # Remove pre existing variable fonts
    designspace.variableFonts = []
    designspace.variableFonts = [
        VariableFontDescriptor(
            name='Powerhouse Filar Super',
            filename='PowerhouseFilarSuper-VF',
            axisSubsets=[RangeAxisSubsetDescriptor(name='Weight'), RangeAxisSubsetDescriptor(name='Unitisation')]
        )
    ]
    
    # Write dspace changes 
    designspace.write(designspacePath)

    
if __name__ == "__main__":
    description = """
    Prepares the sources of a designspace for building a variable font.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-v", "--version",
                        help="Version to set in files")
    args = parser.parse_args()

    print("Copying files")
    if os.path.exists(ROOT):
        shutil.rmtree(ROOT)
    
    # Copy BASE UFO and designspace
    baseDesignspacePath = sourcesData[0]['designspace']
    tempDesignspacePath = copyFiles(baseDesignspacePath, ROOT)

    
    print("Preparing sources")
    prepSources(tempDesignspacePath, sourcesData)

    
    print("Building variable font")
    subprocess.run(["fontmake", 
                    "-m", tempDesignspacePath,
                    "-o", "variable",
                    "--output-dir", OUT_PATH, 
                    ])

    # shutil.rmtree(ROOT)
