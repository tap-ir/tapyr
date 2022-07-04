from setuptools import setup, find_packages

setup(
    name='tapyr',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'' : 'src'},
    url='https://github.com/tap-ir/tapyr',
    license='AGPLv3.0',
    author='Solal Jacob',
    author_email='tapir42@protonmail.com',
    description='Python binding for TAPIR',
    install_requires=[
        "requests~=2.27.1"
    ]
)
