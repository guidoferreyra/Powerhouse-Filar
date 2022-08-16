"""
    Create combined for building VF
"""
import os
import shutil
import argparse
from fontTools.designspaceLib import (DesignSpaceDocument, RuleDescriptor, AxisDescriptor)
from fontParts.world import OpenFont
import subprocess


def prepSources(designspacePath, otherSourcesData):
    baseDesingspace = DesignSpaceDocument.fromfile(designspacePath)

    # Make a dictionary with the base fonts to modify later
    baseUFOs = {}
    for source in baseDesingspace.sources:
        baseUFOs[source.location['Weight']] = OpenFont(source.path)
    
    # Change UFO Metadata
    for key, baseUfo in baseUFOs.items():
        baseUfo.info.familyName = f"{baseUfo.info.familyName}"

    # Add UNIT Axis to designspace
    axisMinValue = min([data['min'] for data in otherSourcesData])
    axisMaxValue = max([data['max'] for data in otherSourcesData])

    unitAxis = AxisDescriptor(tag='UNIT', name="Unitisation", maximum=axisMaxValue, minimum=0, default=0)
    baseDesingspace.addAxis(unitAxis)


    for otherSourceData in otherSourcesData:
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
            # add Glyph
            for glyph in otherSourceUFO:
                if glyph.width != baseFont[glyph.name]:
                    newGlyphName = glyph.name + "." + otherSourceName
                    glyphToAdd = glyph.copy()
                    glyphToAdd.unicode = None
                    baseFont.insertGlyph(glyphToAdd, name=newGlyphName)
                    
                    if (glyph.name, newGlyphName) not in ruleSubstitutions:
                        ruleSubstitutions.append((glyph.name, newGlyphName))
                    
            baseFont.save()


        rule = RuleDescriptor(name=otherSourceName, conditionSets=[
            [{'name': 'Unitisation', 'minimum': otherSourceMinCondition, 'maximum': otherSourceMaxCondition}, {'name': 'Weight', 'minimum': 400, 'maximum': 700}]
        ])
        for sub in ruleSubstitutions:
            rule.subs.append(sub)
        baseDesingspace.rules.append(rule)
        
    baseDesingspace.write(designspacePath)

    
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


if __name__ == "__main__":
    description = """
    Prepares the sources of a designspace for building a variable font.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("designspacePath",
                        help="The path to a designspace file")
    parser.add_argument("-v", "--version",
                        help="Version to set in files")
    args = parser.parse_args()

    designspacePath = args.designspacePath

    outPath = 'fonts/ttf-vf'    
    root = './temp'

    if os.path.exists(root):
        shutil.rmtree(root)

    print("Copying files")
    ds = DesignSpaceDocument.fromfile(designspacePath)
    
    # Copy BASE UFO and designspace
    tempDesignspacePath = copyFiles(designspacePath, root)

    
    print("Preparing sources")
    otherSourcesData = [ 
        {   
            'name': 'octo', 'min': 1, 'max': 1.999, 'designspace': 'sources/PWHSGothicOcto.designspace'
        },
        {   
            'name': 'quarto', 'min': 2, 'max': 2.999, 'designspace': 'sources/PWHSGothicTrio.designspace'
        },
        {   
            'name': 'trio', 'min': 3, 'max': 3.999, 'designspace': 'sources/PWHSGothicTrio.designspace'
        },
        {   
            'name': 'mono', 'min': 4, 'max': 5, 'designspace': 'sources/PWHSGothicMono.designspace'
        }
    ]
    prepSources(tempDesignspacePath, otherSourcesData)

    
    print("Building variable font")
    subprocess.run(["fontmake", 
                    "-m", tempDesignspacePath,
                    "-o", "variable",
                    "--output-dir", outPath, 
                    ])


