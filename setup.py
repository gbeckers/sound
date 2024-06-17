import sys
import versioneer
import setuptools

if sys.version_info < (3,6):
    print("Sound requires Python 3.6 or higher please upgrade")
    sys.exit(1)

long_description = \
"""
Sound is a package for python access to file based sound data. Created with 
scientific use in mind. It is in its early stages of development (alpha) stage.

"""

setuptools.setup(
    name='sound',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=['sound', 'sound.tests'],
    package_data={'sound.testsndfiles': ['testsnd_zf.wav']},
    include_package_data=True,
    url='https://github.com/gbeckers/sound',
    license='BSD-3',
    author='Gabriel J.L. Beckers',
    author_email='gabriel@gbeckers.nl',
    description='Fast, out-of-core access to disk-based sound data and '
                'read/write audio files.',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    python_requires='>=3.6',
    install_requires=['soundfile>=0.12', 'darr>=0.5'],  # numpy is a dependency of darr already
    data_files = [("", ["LICENSE"])],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
    ],
    project_urls={  # Optional
        'Source': 'https://github.com/gbeckers/sound',
    }
)

