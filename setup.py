from setuptools import setup


def get_requirements(filename):
    with open(filename) as requirements_file:
        lines = (line.strip() for line in requirements_file)
        return [str(requirement) for requirement in lines if requirement and not requirement.startswith("#")]


setup(name='Conditional',
      version='1.0',
      description='CSH Re-evaluation (MEGA_EVALS RE:RE:LOADED)',
      author='Computer Science House',
      author_email='evals@csh.rit.edu',
      url='http://csh.rit.edu/',
      install_requires=get_requirements('requirements.txt'),
      )
