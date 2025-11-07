Contributing
============

Contributions are welcome from the community. Questions can be asked on the
[issues page][1]. Before creating a new issue, please take a moment to search
and make sure a similar issue does not already exist. If one does exist, you
can comment (most simply even with just a `:+1:`) to show your support for that
issue.

If you have direct contributions you would like considered for incorporation
into the project you can [fork this repository][2] and
[submit a pull request][3] for review. 

[1]: https://github.com/DOI-USGS/pycap-dss
[2]: https://help.github.com/articles/fork-a-repo/
[3]: https://help.github.com/articles/about-pull-requests/


Try to add tests to the test directory.  Make sure they
run locally by running (from a shell in the main directory)

~~~
    pytest pycap\tests\
~~~


Use docstrings.  Documentation can be added to the
source directory in `rst` files.  To have sphinx
pull in docstrings, add a `rst` file for the
module to the source/api directory 
and an entry to `index.rst` in 
the docs/source/api directory.

In `index.rst`

~~~
    .. toctree::
       pycap.name_of_module-no_py_extension
~~~


The module `rst` file looks like

~~~
    Module name
    -----------

    Long description if desired....  the automodule commands pull in the docstrings.

    .. automodule:: modulename
          :members:
          :show-inheritance:
~~~
