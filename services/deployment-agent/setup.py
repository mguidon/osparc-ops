import io
import re
import sys
from fnmatch import fnmatch
from itertools import chain
from os import walk
from os.path import join
from pathlib import Path

from setuptools import find_packages, setup

_CDIR = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent

if sys.version_info < (3, 6):
    raise RuntimeError("Requires >=3.6, got %s. Did you forget to activate virtualenv?" % sys.version_info)

def list_datafiles_at(*locations):
    def _listdir(root, wildcard='*'):
        """ Recursively list all files under 'root' whose names fit a given wildcard.

        Returns (dirname, files) pair per level. 
        See https://docs.python.org/2/distutils/setupscript.html#installing-additional-files
        """
        for dirname, _, names in walk(root):
            yield dirname, tuple(join(dirname, name) for name in names if fnmatch(name, wildcard))

    return list(chain.from_iterable(_listdir(root) for root in locations))

def read(*names, **kwargs):
    with io.open(join(_CDIR, *names), encoding=kwargs.get('encoding', 'utf8')) as f:
        return f.read()

def list_packages(*parts):
    pkg_names = []
    COMMENT = re.compile(r'^\s*#')
    with io.open(join(_CDIR, *parts)) as f:
        pkg_names = [line.strip() for line in f.readlines() if not COMMENT.match(line)]
    return pkg_names

#####################################################################################
# NOTE see https://packaging.python.org/discussions/install-requires-vs-requirements/


_CONFIG = dict(
    name='simcore-service-deployment-agent',
    version='0.1.0',
    description='Agent that automatically deploy services in a swarm',
    # FIXME: 'Real Name' (github_name) !!
    author='Sylvain Anderegg',
    python_requires='>=3.6',
    packages=find_packages(where='src'),
    package_dir={
        '': 'src',
    },
    include_package_data=True,
    install_requires= list_packages("requirements", "base.txt"),
    tests_require=list_packages("tests", "requirements.txt"),
    extras_require= {
        'test': list_packages("tests", "requirements.txt")
    },
    setup_requires=['pytest-runner'],
    package_data={
        '': [
            'config/*.yaml',
            'oas3/v0/*.yaml',
            'oas3/v0/components/schemas/*.yaml'
            ],
    },
    entry_points={
        'console_scripts': [
            'simcore-service-deployment-agent = simcore_service_deployment_agent.cli:main',
        ],
    },
)


def main():
    """ Execute the setup commands.

    """
    setup(**_CONFIG)
    return 0 # syccessful termination

if __name__ == "__main__":
    raise SystemExit(main())
