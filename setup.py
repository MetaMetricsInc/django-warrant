import os

from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)

version = '0.1.0'

README="""Django library that uses the warrant python utility library to provide authentication via AWS Cognito."""

setup(
    name='django-warrant',
    version=version,
    description=README,
    long_description=README,
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 1.10',
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
    install_requires=[str(ir.req) for ir in install_reqs],
    include_package_data=True,
    zip_safe=True,

)
