import os

from setuptools import setup, find_packages



def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


version = '0.1.1'

README="""Django library that uses the warrant python utility library to provide authentication via AWS Cognito."""

setup(
    name='django-warrant',
    version=version,
    description=README,
    long_description=README,
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='aws,cognito,api,gateway,django',
    author='MetaMetrics',
    author_email='engineering@lexile.com',
    packages=find_packages(exclude=('cdu',)),
    url='https://github.com/MetaMetricsInc/django-warrant',
    license='GNU GPL V3',
    install_requires=parse_requirements('requirements.txt'),
    include_package_data=True,
    zip_safe=True,

)
