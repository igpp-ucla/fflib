import setuptools

with open('version.txt', 'r') as fh:
	versionNum = fh.read()

setuptools.setup(
    name="fflib",
    version=versionNum,
    author='UCLA/IGPP',
    author_email="",
    description='Python Flat File Utility Library',
    url="git@https://github.com/igpp-ucla/fflib.git",
    install_requires=['numpy>=1.15.0'],
    packages=['fflib'],
    python_requires='>=3.6',
    include_package_data=True,
	entry_points={
		'console_scripts': [
			'fflist=fflib.ff_util:fflist',
			'ff2csv=fflib.ff_util:ff2csv',
		],
	},
)