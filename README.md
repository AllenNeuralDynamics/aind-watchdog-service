# aind-watchdog-service

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?logo=codecov)
![Python](https://img.shields.io/badge/python->=3.7-blue?logo=python)

# Summary

With aind-watchdog-service, you can configure a directory for the app to watch, where manifest files (or beacon files) are dropped containing src files from an acquisition labeled by modality. The program is meant to be configured with a web-hook URL to send messages to a Teams channel when data staging is complete and data transfer has been triggered through [aind-data-transfer-service](https://github.com/AllenNeuralDynamics/aind-data-transfer-service). Pipeline capsule ids can be added if triggering pipelines is necessary post-acquisition.

# Usage
* Create a watch_config file as json or yaml and store it's location in an environment variable called WATCH_CONFIG
    * Review src/aind-watchdog-service/models/watch_config.py for configuration parameters
    * watch_config.yml must include:
        * flag_dir (where watchdog observer should be looking for beacon files)
        * webhook_url (to receive Teams notifications)
        * run_script (bool - should be set to False if planning on staging data on VAST)

* Beacon or manifest file must contain the word "manifest" in the file name and the parameters according to the configurations set in aind-watchdog-service/models/job_config.py using either VastTransferConfig or RunScriptConfig for VAST transfer or custom script instructions, respectively. 
    * yaml only (for now)
    * To run a job that stages data on VAST, view the a template manifest under \tests\resources\manifest.yml
        * for configuration parameters reference VastTransferConfig under src\aind_watchdog_service\models\job_configs.py
    * Run a custom script
        * To run a custom script that requires a differnt procedure than staging data directly on VAST, view the template manifest under \tests\resources\manifest_run_script.yml
        * see src\aind_watchdog_service\models\job_configs.py

# Configure Task Scheduler to boot aind-watchdog-service


# Installation
To use the software, in the root directory, run
```bash
pip install -e .
```

To develop the code, run
```bash
pip install -e .[dev]
```

## Contributing

### Linters and testing

There are several libraries used to run linters, check documentation, and run tests.

- Please test your changes using the **coverage** library, which will run the tests and log a coverage report:

```bash
coverage run -m unittest discover && coverage report
```

- Use **interrogate** to check that modules, methods, etc. have been documented thoroughly:

```bash
interrogate .
```

- Use **flake8** to check that code is up to standards (no unused imports, etc.):
```bash
flake8 .
```

- Use **black** to automatically format the code into PEP standards:
```bash
black .
```

- Use **isort** to automatically sort import statements:
```bash
isort .
```

### Pull requests

For internal members, please create a branch. For external members, please fork the repository and open a pull request from the fork. We'll primarily use [Angular](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit) style for commit messages. Roughly, they should follow the pattern:
```text
<type>(<scope>): <short summary>
```

where scope (optional) describes the packages affected by the code changes and type (mandatory) is one of:

- **build**: Changes that affect build tools or external dependencies (example scopes: pyproject.toml, setup.py)
- **ci**: Changes to our CI configuration files and scripts (examples: .github/workflows/ci.yml)
- **docs**: Documentation only changes
- **feat**: A new feature
- **fix**: A bugfix
- **perf**: A code change that improves performance
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests or correcting existing tests

### Semantic Release

The table below, from [semantic release](https://github.com/semantic-release/semantic-release), shows which commit message gets you which release type when `semantic-release` runs (using the default configuration):

| Commit message                                                                                                                                                                                   | Release type                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `fix(pencil): stop graphite breaking when too much pressure applied`                                                                                                                             | ~~Patch~~ Fix Release, Default release                                                                          |
| `feat(pencil): add 'graphiteWidth' option`                                                                                                                                                       | ~~Minor~~ Feature Release                                                                                       |
| `perf(pencil): remove graphiteWidth option`<br><br>`BREAKING CHANGE: The graphiteWidth option has been removed.`<br>`The default graphite width of 10mm is always used for performance reasons.` | ~~Major~~ Breaking Release <br /> (Note that the `BREAKING CHANGE: ` token must be in the footer of the commit) |

### Documentation
To generate the rst files source files for documentation, run
```bash
sphinx-apidoc -o doc_template/source/ src 
```
Then to create the documentation HTML files, run
```bash
sphinx-build -b html doc_template/source/ doc_template/build/html
```
More info on sphinx installation can be found [here](https://www.sphinx-doc.org/en/master/usage/installation.html).
