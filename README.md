# flyem_restapi: RESTful interface to FlyEM database

flyem_restapi is a web server that allows for RESTful call that can
GET or PUT data in the FlyEM database.  The FlyEM database tracks
information from the production pipeline and interactive training.

## Requirements (tested versions)

* Python 2.x (2.6, 2.7)
* flask (0.9)
* flask-sqlalchemy (0.16)


## Installation

### Installing flyem_restapi

flyem_restapi is a python library and can be installed:

    % python setup.py install

### Installing requirements

You may either install all requirements manually or use the 
[buildem system](http://github.com/janelia-flyem/buildem#readme) to automatically
download, compile, test, and install requirements into a specified buildem
prefix directory.  

```
% cmake -D BUILDEM_DIR=/path/to/platform-specific/build/dir <flyem_restapi directory>
% make
```

You might have to run the above steps twice if this is the first time you are
using the buildem system.

## Usage

Running the flyem_restapi command will launch a web server.  The webserver
will link to a database located in the config.py file.  The webserver
provides an interface that allows for the getting and putting of data using
the json file format.

For examples of how to call the interface, examine sample_commands.txt
