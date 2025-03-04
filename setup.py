from setuptools import setup, find_packages

setup(
    name="train_ticket_monitor",
    version="1.0.0",
    description="12306车票查询监控工具",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    py_modules=["train_ticket_monitor"],
    install_requires=[
        "requests>=2.25.0",
        "prettytable>=2.0.0",
        "pyyaml>=5.4.0",
        "urllib3>=1.26.0",
    ],
    entry_points={
        "console_scripts": [
            "train-monitor=train_ticket_monitor:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 