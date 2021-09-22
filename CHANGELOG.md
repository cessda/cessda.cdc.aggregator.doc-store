# Changelog

All notable changes to the CDC Aggregator DocStore will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## 0.1.0 - 2021-09-21

### Added

- New codebase for CDC Aggregator DocStore.
- HTTP API in front of a MongoDB cluster.
- RESTful endpoint '/v0/studies/<resource_id>' with support for GET, POST, PUT and DELETE.
- Query endpoint '/v0/query/studies' for SELECT, COUNT and DISTINCT types of DB queries.
- Admin module to ease DB setup.
