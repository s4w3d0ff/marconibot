from setuptools import setup
from marconi import __version__
setup(name='marconi',
      version=__version__,
      description='Poloniex API trader for Python 3',
      url='https://github.com/s4w3d0ff/marconibot',
      author='s4w3d0ff',
      license='GPL v3',
      packages=['marconi', 'marconi.tools'],
      install_requires=[
          'numpy',
          'scikit-learn',
          'bokeh',
          'cherrypy',
          'beautifulsoup4',
          'pymongo',
          'pandas',
          'websocket-client',
          'poloniex'
      ],
      dependency_links=[
          "git+https://git@github.com/s4w3d0ff/python-poloniex.git"
      ],
      zip_safe=False)
