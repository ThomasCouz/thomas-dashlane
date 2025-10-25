from setuptools import setup, find_packages

setup(
    name="packages_dashlane",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "run_logistic_regression_model=scripts.eda.logistic_regression_model:main",
        ],
    },
)
