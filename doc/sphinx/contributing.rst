Contribution guide
==================

How to make a new release
-------------------------

Releases are made to the Python Packaging Index (PyPI) and can be installed with the Python "pip" tool.
To make a new release follow these steps.


Determine new version number
____________________________

We use the `Semantic Versioning <https://semver.org/>`__ scheme for tsfpga.
Read the **Summary** at the top of that page and decide the new version number accordingly.


Create release notes
____________________

Create a release notes document ``doc/release_notes/X.Y.Z.md`` with a bullet list of changes.


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

Push tag and commit
___________________

.. code-block:: shell

    git push origin --tag vX.Y.Z HEAD:release_branch

This will create two CI pipelines in gitlab.
One for the commit and one for the tag.

.. image:: ci_deploy_pipelines.png

The pipeline for the tag will run an additional job ``pypi_deploy``.

.. image:: ci_deploy_jobs.png

The package is uploaded to https://pypi.org/project/tsfpga/.
So if really want to make sure that everything has worked you can check there and see that your new release is available.


Merge
_____

If everything went well then you can merge your release commit to master.
