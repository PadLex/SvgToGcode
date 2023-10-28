import setuptools

with open("README.md", "r", encoding="utf-8") as file:
    readme = file.read()

setuptools.setup(
    name="svg_to_gcode",
    version="1.5.3",
    author="Padlex",
    author_email="",
    description="The definitive NPM module to construct gcode from svg files.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/inghvar/SvgToGcode",
    packages=setuptools.find_packages(exclude=("testing", "testing.*")),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['svgpathtools==1.6.1']
)
