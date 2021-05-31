from setuptools import find_packages, setup

setup(
    name='flaski',
    version='2.0.1',
    packages=["flaski"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
    ],
)