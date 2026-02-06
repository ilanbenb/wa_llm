# CHANGELOG

<!-- version list -->

## v1.2.0 (2026-02-06)

### Build System

- Add bind mount for sdk-python-gowa directory to Dockerfile
  ([#60](https://github.com/ilanbenb/wa_llm/pull/60),
  [`4e18737`](https://github.com/ilanbenb/wa_llm/commit/4e18737af68c2eddb825a2c6908dd100868b0662))

- Fix docker build ([#60](https://github.com/ilanbenb/wa_llm/pull/60),
  [`4e18737`](https://github.com/ilanbenb/wa_llm/commit/4e18737af68c2eddb825a2c6908dd100868b0662))

### Features

- Introduce `gowa_sdk` with new client, webhooks, and mixins, refactoring existing WhatsApp client
  functionality. ([#60](https://github.com/ilanbenb/wa_llm/pull/60),
  [`4e18737`](https://github.com/ilanbenb/wa_llm/commit/4e18737af68c2eddb825a2c6908dd100868b0662))


## v1.1.0 (2026-02-05)

### Features

- Introduce `gowa_sdk` with new client, webhooks, and mixins, refactoring existing WhatsApp client
  functionality. ([#59](https://github.com/ilanbenb/wa_llm/pull/59),
  [`ac0393f`](https://github.com/ilanbenb/wa_llm/commit/ac0393f1cc2fd9212b3ffde33413addee730bf82))

- Support v8 breaking changes and create a separated python-sdk for GOWA to organize the code
  ([#59](https://github.com/ilanbenb/wa_llm/pull/59),
  [`ac0393f`](https://github.com/ilanbenb/wa_llm/commit/ac0393f1cc2fd9212b3ffde33413addee730bf82))


## v1.0.3 (2025-12-10)

### Bug Fixes

- * avoid dedupe in /kb_qa ([#54](https://github.com/ilanbenb/wa_llm/pull/54),
  [`3b1ee6a`](https://github.com/ilanbenb/wa_llm/commit/3b1ee6aeff29b3522df6afc5da0afb81a2bf9cd3))

- Dedupe messages for kb qa ([#54](https://github.com/ilanbenb/wa_llm/pull/54),
  [`3b1ee6a`](https://github.com/ilanbenb/wa_llm/commit/3b1ee6aeff29b3522df6afc5da0afb81a2bf9cd3))


## v1.0.2 (2025-12-09)

### Bug Fixes

- Call kb_qa works for unmanaged groups as well ([#53](https://github.com/ilanbenb/wa_llm/pull/53),
  [`58e5fef`](https://github.com/ilanbenb/wa_llm/commit/58e5fefe7730a7bec6a4e44b46444592a0bbf9f9))


## v1.0.1 (2025-12-09)

### Bug Fixes

- Don't have to mention number to get /kb_qa ([#52](https://github.com/ilanbenb/wa_llm/pull/52),
  [`623be75`](https://github.com/ilanbenb/wa_llm/commit/623be754149395369fb0c501f4dd8ba74b16764a))

- Fix erorr in hybrid search AmbiguousParameterError. could not determine data type of parameter $2
  ([#52](https://github.com/ilanbenb/wa_llm/pull/52),
  [`623be75`](https://github.com/ilanbenb/wa_llm/commit/623be754149395369fb0c501f4dd8ba74b16764a))

- Stop mention number in kbqa ([#52](https://github.com/ilanbenb/wa_llm/pull/52),
  [`623be75`](https://github.com/ilanbenb/wa_llm/commit/623be754149395369fb0c501f4dd8ba74b16764a))

### Documentation

- Prod-ready-docker-compose ([#51](https://github.com/ilanbenb/wa_llm/pull/51),
  [`3cc8c05`](https://github.com/ilanbenb/wa_llm/commit/3cc8c0541bc70338d85ecb84c62ab8ba14f4942f))


## v1.0.0 (2025-12-08)

- Initial Release
