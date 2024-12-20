# Changelog

All notable changes to the CDC Aggregator DocStore will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## 0.7.0 - 2024-12-19

### Added

- Support more Study attributes. (Implements
  [#37](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/37))

  - `Study.distribution_dates.attr_description`
  - `Study.research_instruments`
  - `Study.data_access_desriptions.attr_element_version`
  - `Study.collection_periods.attr_description`

### Changed

- Require Kuha Common 2.6.0 in requirements.txt.
- Require Kuha Document Store 1.6.0 in requirements.txt.
- Require Aggregator Shared Library 0.9.0 in requirements.txt.
- Require Tornado 6.4.2 in requirements.txt.


## 0.6.0 - 2024-09-05

### Added

- Support Python 3.11 & Python 3.12.
- New test environment for tox 'warnings-as-errors' to treat warnings
  as errors in tests. Run this environment in CI with latest python.

### Changed

- Update dependencies in requirements.txt to support Python 3.12:

  - Motor 3.5.1
  - PyMongo 4.8.0
  - Python-dateutil 2.9.0
  - Cerberus 1.3.5
  - Py12fLogging 0.7.0
  - Tornado 6.4.1
  - Kuha Common 2.5.0
  - Kuha Document Store 1.4.0
  - Aggregator Shared Library 0.8.1

- Add new dependency dnspython 2.6.1, which is an indirect dependency
  from PyMongo.
- Update dependencies to latest versions in requirements.txt:

  - ConfigArgParse 1.7


## 0.5.0 - 2024-04-30

### Added

- Support `external_link`, `external_link_role`, `external_link_uri`
  and `external_link_title` attributes in Study.principal_investigator.

### Changed

- Update dependencies:

  - Require CDC Aggregator Shared Library 0.7.0 in setup.py and
    requirements.txt. (Implements
    [#31](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/31))
  - Require Kuha Common 2.4.0 or newer in setup.py and 2.4.0 in
    requirements.txt. (Implements
    [#31](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/31))
  - Require Kuha Document Store 1.3.0 in setup.py and
    requirements.txt. (Implements
    [#31](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/31))


## 0.4.0 - 2023-11-24

### Added

- Support `study._direct_base_url` (Implements
  [#27](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/27))


## 0.3.0 - 2022-11-21

### Added

- Support grant & funding information and identifiers for related
  publications in `studies` collection. (Implements
  [#20](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/20))

### Changed

- Update dependencies:

  - Require CDC Aggregator Shared Library 0.5.0 in setup.py and
    requirements.txt.
  - Require Kuha Common 2.0.0 or newer in setup.py and 2.0.1 in requirements.txt.
  - Require Kuha Document Store 1.1.0 in setup.py and requirements.txt.
  - Require tornado 6.2.0 in requirements.txt.


## 0.2.0 - 2021-12-17
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5779898.svg)](https://doi.org/10.5281/zenodo.5779898)

### Changed

- Implement `CDCAggDatabase._prepare_validation_schema()`, which
  returns the validation schema for Study record.
  (Implements [#14](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/14))
- Require latest commit of Kuha Document Store master
  (Implements [#14](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/14))
- Update dependencies in requirements.txt.

  - ConfigArgParse 1.5.3
  - python-dateutil 2.8.2
  - Motor 2.5.1
  - PyMongo 3.12.0
  - Cerberus 1.3.4
  - Kuha Common to Git commit 8e7de1f16530decc356fee660255b60fcacaea23
  - Kuha Document Store to Git commit 31b277685fd7568032d037db4334cb15da2a28da
  - CDC Aggregator Shared Library 0.2.0

### Added

- Validation and indexing of Study record's `_aggregator_identifier` field to MongoDB.
  (Fixes [#13](https://github.com/cessda/cessda.cdc.aggregator.doc-store/issues/13))


## 0.1.0 - 2021-09-21

### Added

- New codebase for CDC Aggregator DocStore.
- HTTP API in front of a MongoDB cluster.
- RESTful endpoint '/v0/studies/<resource_id>' with support for GET, POST, PUT and DELETE.
- Query endpoint '/v0/query/studies' for SELECT, COUNT and DISTINCT types of DB queries.
- Admin module to ease DB setup.
