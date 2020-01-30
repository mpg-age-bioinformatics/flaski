from setuptools import find_packages, setup

setup(
    name='flaski',
    version='0.1.0',
    packages=["flaski"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
    ],
)