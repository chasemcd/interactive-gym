import setuptools

setuptools.setup(
    name="interactive-gym",
    version="0.0.1",
    description="A platform for running interactive experiments in the browser with standard simulation environments.",
    author="Chase McDonald",
    author_email="chasemcd@andrew.cmu.edu",
    packages=setuptools.find_packages(),
    install_requires=[
        "eventlet==0.38.2",
        "Flask==3.1.0",
        "Flask_SocketIO==5.3.6",
        "flatten_dict==0.4.2",
        "gymnasium==0.29.1",
        "msgpack_python==0.5.6",
        "numpy==2.2.1",
        "onnxruntime==1.16.3",
        "pandas==2.2.3",
        "redis==5.0.7",
        "scipy==1.14.1",
        "setuptools==68.2.2",
    ],
)
