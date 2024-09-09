"""
    Create combined for building VF
"""
import os
import shutil
import subprocess

SOURCES_PATH = './sources'
VF_OUTPATH = 'fonts/ttf-vf'
OTF_OUTPATH = 'fonts/otf'
TTF_OUTPATH = 'fonts/ttf'


def getFiles(path, extensions):
    """Walks down all directories starting at *path* looking for files
    ending with *extension*.
    Args:
        path: string of a path
    Returns:
        list
    """

    return [os.sep.join((dir, file)) for (dir, dirs, files)
            in os.walk(path) for file in files if
            file.split(".")[-1] in extensions]


if __name__ == "__main__":
    description = """
    Prepares the sources of a designspace for building a variable font.
    """

    print("Building variable fonts")

    desginspacePaths = getFiles(SOURCES_PATH, ['designspace'])

    for dspacePath in desginspacePaths:
        subprocess.run(["fontmake",
                        "-m", dspacePath,
                        "-o", "variable",
                        "--output-dir", VF_OUTPATH,
                        ])

        subprocess.run(["fontmake",
                        "-m", dspacePath,
                        "-o", "otf",
                        "--output-dir", OTF_OUTPATH,
                        ])

        subprocess.run(["fontmake",
                        "-m", dspacePath,
                        "-o", "ttf",
                        "--output-dir", TTF_OUTPATH,
                        ])
