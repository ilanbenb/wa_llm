# CHANGELOG

<!-- version list -->

## v1.4.4 (2026-03-09)

### Bug Fixes

- **deps**: Update python non-major dependencies
  ([#116](https://github.com/ilanbenb/wa_llm/pull/116),
  [`174d4bf`](https://github.com/ilanbenb/wa_llm/commit/174d4bff58fbe1c9724cf6ccb21ef4485db135ab))

### Chores

- **deps**: Update docker/build-push-action action to v7
  ([#117](https://github.com/ilanbenb/wa_llm/pull/117),
  [`3874d2d`](https://github.com/ilanbenb/wa_llm/commit/3874d2ddd49f3d878b38c9c61682c883ca172855))


## v1.4.3 (2026-03-03)

### Bug Fixes

- **deps**: Update python non-major dependencies
  ([#114](https://github.com/ilanbenb/wa_llm/pull/114),
  [`2ef2996`](https://github.com/ilanbenb/wa_llm/commit/2ef29961e50b3699a419bdb2e3d48d7c8b79b1ae))

### Build System

- Update postgres docker tag to v17 ([#111](https://github.com/ilanbenb/wa_llm/pull/111),
  [`dd73062`](https://github.com/ilanbenb/wa_llm/commit/dd730620c03f64515a7eb44d5b97215d6157981d))

### Chores

- **deps**: Lock file maintenance ([#115](https://github.com/ilanbenb/wa_llm/pull/115),
  [`33c8db3`](https://github.com/ilanbenb/wa_llm/commit/33c8db3d382aef11a5fa2239e65e94c5a577107f))

- **deps**: Lock file maintenance ([#113](https://github.com/ilanbenb/wa_llm/pull/113),
  [`d30307a`](https://github.com/ilanbenb/wa_llm/commit/d30307a4f5537c23b3322e27feba3734e7bbea6c))

- **deps**: Lock file maintenance ([#112](https://github.com/ilanbenb/wa_llm/pull/112),
  [`ea97e13`](https://github.com/ilanbenb/wa_llm/commit/ea97e135578ec1edd575c91c62804cb1f57deabe))

- **deps**: Update postgres docker tag to v18 ([#111](https://github.com/ilanbenb/wa_llm/pull/111),
  [`dd73062`](https://github.com/ilanbenb/wa_llm/commit/dd730620c03f64515a7eb44d5b97215d6157981d))


## v1.4.2 (2026-03-02)

### Bug Fixes

- **deps**: Update python non-major dependencies
  ([#110](https://github.com/ilanbenb/wa_llm/pull/110),
  [`3c666a0`](https://github.com/ilanbenb/wa_llm/commit/3c666a0f49b0c5ecb8abfea01f96f0ea907873fd))

### Chores

- **deps**: Lock file maintenance ([#108](https://github.com/ilanbenb/wa_llm/pull/108),
  [`2192c56`](https://github.com/ilanbenb/wa_llm/commit/2192c561adcb3ad6883b550caf6ca44989261db2))

- **deps**: Update aldinokemal2104/go-whatsapp-web-multidevice docker tag to v8.3.2
  ([#109](https://github.com/ilanbenb/wa_llm/pull/109),
  [`09c8691`](https://github.com/ilanbenb/wa_llm/commit/09c86917835d407ace395c91be0e6ba443ca3a5e))

- **deps**: Update python non-major dependencies
  ([#107](https://github.com/ilanbenb/wa_llm/pull/107),
  [`4dd179b`](https://github.com/ilanbenb/wa_llm/commit/4dd179b4b9ea74fbfb569225e6441129cd4bdc60))


## v1.4.1 (2026-02-23)

### Bug Fixes

- **deps**: Update python non-major dependencies
  ([#103](https://github.com/ilanbenb/wa_llm/pull/103),
  [`e4d73cf`](https://github.com/ilanbenb/wa_llm/commit/e4d73cfbd844670b6a8379ec5287ca2ddc007d32))

### Chores

- Migrate to renvate. Better support for uv ([#101](https://github.com/ilanbenb/wa_llm/pull/101),
  [`959b446`](https://github.com/ilanbenb/wa_llm/commit/959b446af90c80145f0e8861520cc44a1d257ea0))

- Update logfire ([#99](https://github.com/ilanbenb/wa_llm/pull/99),
  [`24c5014`](https://github.com/ilanbenb/wa_llm/commit/24c5014ca11014533f2624c444e9cb64016f09de))

- **deps**: Update aldinokemal2104/go-whatsapp-web-multidevice docker tag to v8.3.1
  ([#104](https://github.com/ilanbenb/wa_llm/pull/104),
  [`7f5132b`](https://github.com/ilanbenb/wa_llm/commit/7f5132b2f0d056dae4920df70efabc73586b7dff))


## v1.4.0 (2026-02-22)

### Features

- Upgrade to sonnet 4.6 ([#91](https://github.com/ilanbenb/wa_llm/pull/91),
  [`f8285b5`](https://github.com/ilanbenb/wa_llm/commit/f8285b50586cff6030544a695e5342be84c3c0b1))


## v1.3.0 (2026-02-09)

### Build System

- Use external sdk gowa ([#62](https://github.com/ilanbenb/wa_llm/pull/62),
  [`aad5885`](https://github.com/ilanbenb/wa_llm/commit/aad58855ce07204ca7a288a7a3b07199bca868ee))

### Features

- Gather groups when number is added to a new group as well on startup to avoid manual restarts when
  being added to new groups ([#72](https://github.com/ilanbenb/wa_llm/pull/72),
  [`491317d`](https://github.com/ilanbenb/wa_llm/commit/491317da1e72332704ce4fe52d7e7ce85506e4c8))


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
