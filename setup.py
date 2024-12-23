import setuptools

setuptools.setup(
    name="interactive-gym",
    version="0.0.5",
    description="A platform for running interactive experiments in the browser with standard simulation environments.",
    author="Chase McDonald",
    author_email="chasemcd@andrew.cmu.edu",
    packages=setuptools.find_packages(),
    install_requires=[
        "gymnasium",
        "numpy",
    ],
)
