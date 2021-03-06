from setuptools import setup, find_packages

try:
    from pypandoc import convert
    def read_markdown(file: str) -> str:
        return convert(file, "rst")
except ImportError:
    def read_markdown(file: str) -> str:
        return open(file, "r").read()


setup(name="github2gitlab",
      version="0.4.0",
      description="Webhook to sync Github repos to internal Gitlab repos",
      url="https://github.com/wtsi-hgi/github-to-gitlab-hook",
      author="Elizabeth Weatherill",
      author_email="elizabeth.weatherill@sanger.ac.uk",
      license="GNU General Public License",
      packages=find_packages(exclude=["test"]),
      install_requires=open("requirements.txt", "r").readlines(),
      entry_points={
          "console_scripts": [
              "github2gitlab=github2gitlab.entrypoint:main"
          ]
      },
      zip_safe=True)
