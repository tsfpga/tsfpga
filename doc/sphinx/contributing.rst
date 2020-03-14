Contribution guide
==================

Information on how to make contributions to the tsfpga project.



Setting up development environment
----------------------------------

For tsfpga development we have a lot more python dependencies than when simply using the package.
Install further dependencies with:

.. code-block:: shell

    python -m pip install --upgrade --requirement requirements_develop.txt

You also need VUnit installed `somewhere where python can find it <https://vunit.github.io/installing.html>`__.



.. _maintain_changelog:

Maintaining changelog
---------------------

We maintain a changelog according to the `keep a changelog <https://keepachangelog.com/>`__ format.
The unreleased changelog in ``doc/release_notes/unreleased.rst`` shall be updated continuously, not just at release.
Release note files are in the ``rst`` format, inspect older release note files to see the formatting details.



How to build documentation
--------------------------

Documentation is built using the ``tools/build_sphinx_docs.py`` script.
The documentation pages have information about unit test code coverage.
So before building documentation you must run pytest with coverage reports enabled like in CI:

.. code-block:: shell

    python -m pytest -v --cov tsfpga --cov-report xml:generated/pytest_coverage.xml --cov-report html:generated/pytest_coverage_html tsfpga



How to make a new release
-------------------------

Releases are made to the Python Packaging Index (PyPI) and can be installed with the python ``pip`` tool.
To make a new release follow these steps.


Determine new version number
____________________________

We use the `Semantic Versioning <https://semver.org/>`__ scheme for tsfpga.
Read the **Summary** at the top of that page and decide the new version number accordingly.


Create release notes
____________________

Create and ``git add`` a new file ``doc/release_notes/X.Y.Z.rst`` according to your new release version.
Move the contents of ``unreleased.rst`` to your newly created file.
Fill in anything that is missing according to :ref:`Maintaining changelog <maintain_changelog>`.


Update python package version number
____________________________________

Bump the version number in ``tsfpga/about.py``.


Commit and tag
______________

Create a release commit and tag with the new version number (with a "v" in front).

.. code-block:: shell

    git add doc/release_notes/X.Y.Z.md
    git commit -m "Release X.Y.Z"
    git tag vX.Y.Z


Verify
______
Before pushing the tag it is a good idea to run the ``tools/verify_release.py`` script manually.


Push tag and commit
___________________

.. code-block:: shell

    git push origin --tag vX.Y.Z HEAD:release_branch

This will create two CI pipelines in gitlab.
One for the commit and one for the tag.

.. image:: ci_deploy_pipelines.png

The pipeline for the tag will run an additional job ``deploy_pypi``.

.. image:: ci_deploy_jobs.png

The package is uploaded to https://pypi.org/project/tsfpga/.
So if you really want to make sure that everything has worked you can check there and see that your new release is available.


Merge
_____

If everything went well then you can merge your release commit to master.
