from setuptools import setup, find_packages


def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='PyDataCore',  # Nom du package
    version='1.0.0',  # Version de ta bibliothèque
    author='Guillaume Train',  # Auteur
    author_email='g.train@live.fr',  # Email de l'auteur
    description='A data library for handling temporal, frequency signals, and data pools.',
    long_description=open('README.md').read(),  # Longue description du projet
    long_description_content_type='text/markdown',
    url='https://github.com/GuillaumeTrain/PyDataCore',  # Lien vers ton repo GitHub
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,  # Inclut des fichiers de données dans la distribution
    classifiers=[  # Catégories de la bibliothèque
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',  # Version minimum de Python
    install_requires=parse_requirements('requirements.txt'),
)
