from setuptools import setup, find_packages

def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='PyDataCore',
    version='1.0.0',
    author='Guillaume Train',
    author_email='g.train@live.fr',
    description='A data library for handling temporal, frequency signals, and data pools.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/GuillaumeTrain/PyDataCore',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    install_requires=parse_requirements('requirements.txt'),
    package_data={
        '': ['requirements.txt', 'README.md'],
    },
)
