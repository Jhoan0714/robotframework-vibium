# Backlog — robotframework-vibium

Roadmap of improvements organized by milestone (SemVer). It combines community
suggestions (Slack thread) with opportunities identified in the current state of
the project.

Status legend: `[x]` done, `[ ]` pending.

IDs (A2, B1, E3…) are kept as a stable identifier to map each item to its GitHub
issue.

## Milestone overview

| Milestone | Theme | Breaking | Status |
|---|---|---|---|
| v0.2.0 | Foundation (DynamicCore) | No | **Done** (code, tag, GitHub release, PyPI; milestone closed) |
| v0.3.0 | Hardening & tooling | No | **Done** (0.3.0 released; milestone closed) |
| v0.4.0 | API freeze | **Yes** | **Cancelled** — renames shipped in 0.3.0; work moved to 1.0.0 |
| v1.0.0 | Stable core API | No | **In progress** — docs nearly done; CI acceptance + `py.typed` + release remain |
| v1.1.0 | Vibium coverage I | No (additive) | Future — network, capture, downloads |
| v1.2.0 | Vibium coverage II | No (additive) | Future — recording, clock, remaining emulation (#36) |
| v1.x | Extensibility | No (additive) | Future — #37–#39 |

### Suggested next order (1.0)

1. **#24** — enable headless acceptance in CI  
2. **#16** — ship `py.typed`  
3. Polish if time: **#21**, **#23**  
4. **#52** — release 1.0.0  

*(Docs shipped / in this branch: #49 pierce, #55/#26 scope+Pabot, #56 architecture;
#20 tags. API: #54/#72/#75 timeouts, #70 Tap/Highlight, #67 handle-as-target,
#57 nested find.)*

---

## v0.2.0 — Foundation (DynamicCore)

- [x] **A1. Adopt PythonLibCore / DynamicCore** (#5, PR #6 merged)
  Migrated from multiple mixin inheritance to composition with `DynamicCore`
  (Option B): each component stores `self.library` and accesses shared state via
  `self.library._session`. Validated with 190 unit tests and 30 acceptance tests
  in dry-run.
- [x] **REL-0.2.0. Version bump + release** (PR #7, CHANGELOG PR #8)
  Bumped `0.1.1 → 0.2.0` in `pyproject.toml`, `@library(version=...)` and
  `ROBOT_LIBRARY_VERSION`. Tagged and published GitHub release `v0.2.0`;
  published to PyPI as `robotframework-vibium==0.2.0`. Milestone closed.

## v0.3.0 — Hardening & tooling (no public API changes)

- [x] **B1. Pin the Robot Framework version when generating docs** (#9)
- [x] **B2. Run `ruff` and `mypy` in CI** (#10)
- [x] **B3. Update `docs/architecture.md`** (#11)
- [x] **B4. Single source of truth for the version** (#12)
- [x] **E1. Harden `parse_timeout_ms`** (#13)
- [x] **E2. Make `SessionPool.close()` failure-safe** (#14)
- [x] **E3. Escape JS text in `Wait For Text`** (#15)
- [x] **E7. Coverage in CI** (#17)
- [x] **E4. Remove global asyncio monkeypatch** (#25)
- [x] **A3. Rename keywords to a concise convention** (#19) — shipped in 0.3.0
  (without deprecated aliases; see CHANGELOG 0.3.0)

## v0.4.0 — API freeze (cancelled)

Superseded by the direct jump to **1.0.0**. Keyword renames already landed in
0.3.0. Remaining polish and AssertionEngine (#18) move to 1.0.0.

- [x] **A2. AssertionEngine on the getters** (#18) → **v1.0.0**
  (follow-ups in #77 → v1.1.0)
- [x] **C1. Tags on the `@keyword` definitions** (#20) → **v1.0.0**
- [ ] **C2. Tighten loose typing** (#21) → **v1.0.0**
- [x] **C4. Reconcile `Get Element Attr` vs `Get Element Attribute`** (#22) — resolved in 0.3.0 renames
- [ ] **E8. Adopt or remove the `types.py` aliases** (#23) → **v1.0.0**

## v1.0.0 — Stable core API (Vibium ≥ 26.8.21)

Stable Robot keyword API for UI automation. Not full Vibium parity — network,
recording, and Firefox-only extras land in 1.1+.

### Release readiness

- [ ] **C3. Enable acceptance tests in CI** (#24)
  Currently commented out in `on-pull.yml`. Enable headless acceptance
  (`-e no-ci -e firefox`) to guard real wiring regressions.
- [ ] **E6. Ship the `py.typed` marker (PEP 561)** (#16)
  Add `src/rfvibium/py.typed` and include it in the wheel.
- [x] **E5. Concurrency / Pabot** (#26)
  Documented `GLOBAL` scope and process isolation under Development in README.

### Vibium 26.8.21 alignment

- [x] **V1. Bump dependency floor to `vibium>=26.8.21`** (#47)
  `pyproject.toml` requires `vibium>=26.8.21,<26.9`; CHANGELOG updated.
- [x] **V2. Migrate `wait_until` → `wait_for_*`** (#48)
  Page waits and screenshot retry use `wait_for_function` / `wait_for_url` /
  `wait_for_load`. Element `wait_until` for `Wait For Element` unchanged.
- [x] **V3. Document pierce locators (`>>` / `>>>`)** (#49)
  Libdoc + README; pass-through via `page.find()`.
- [x] **V4. Acceptance test for pierce selectors** (#50)
  Headless Shadow DOM coverage in `tests/acceptance/pierce.robot`.
- [x] **V5. `Open Browser` `engine=` / `channel=`** (#53)
  Multi-engine launch; acceptance in `engine.robot` / `multi_browser.robot`.
- [x] **V5b. `Open Browser` launch parity** (#65 launch)
  Optional `url=`, `headless=` (per browser; defaults to library import),
  `headers=` for remote BiDi. Browser listeners (`on_page` / `on_popup`) still open.
- [x] **V6. `timeout=` on element actions** (#54)
  Expose Vibium ``find`` / action timeouts (getters: find only; Mouse/Touch
  page APIs unchanged).
- [x] **V6b. Align timeout parsing with Robot Framework** (#72)
  ``parse_timeout_ms`` uses ``timestr_to_secs``; bare number = **seconds**
  (breaking vs prior bare-ms semantics).
- [x] **V6c. `Set Browser Timeout` with scopes** (#75)
  Library default for locate/actions when ``timeout=`` is omitted;
  ``scope=Global|Suite|Test|Task``; per-call ``timeout=`` still wins.
- [x] **V7. Document 1.0 scope and engine defaults** (#55)
  README Compatibility + `Open Browser` engine/channel docs; Pabot with #26.
- [x] **V8. Align architecture.md and README** (#56)
  Responsibility boundary, package layout, DynamicCore layers, runtime stack.

### Polish (ex-v0.4.0)

- [x] **A2. AssertionEngine on getters** (#18)
  Integrate `robotframework-assertion-engine` into getters with
  `assertion_operator` + `expected_value`; add `Get Element States`.
  **1.0 constraint:** additive only — keep existing `Element Is *` keywords.
  Follow-ups → #77 (v1.1.0).
- [x] **C1. Tags on `@keyword` definitions** (#20)
- [ ] **C2. Tighten loose typing** (#21)
- [ ] **E8. Adopt or remove `types.py` aliases** (#23)

### Core 1:1 wrappers (split from #36)

- [x] **F10. `Mouse Wheel`** (#51)
- [x] **F11. `Keyboard Key` / `Keyboard Type`** (#51)
- [x] **F13. `Set Viewport Size` / `Get Viewport Size`** (#51)
- [x] **F14. `Set Page Content`** (#51)
- [x] **F20. `Set Window` / `Get Window Info`** (#51) — shipped with core wrappers
- [x] **F23. `Clear Storage`** (#51)
- [x] **F22. `Bring To Front`** — already `Switch Page` (#51)
- [x] **F24. Nested `element.find` / `find_all`** (#57, PR #68)
  ``Find Element`` / ``Find Elements`` return handles; use ``scope=${element}``.
  ``Describe Element`` for ``repr``.
- [x] **F25. Element handle as sole target** (#67, PR #69)
  Action/getter keywords (`Click`, `Get Text`, `Hover`, `Fill Text`,
  `Wait For Element`, `Take Screenshot`, `Get Html`, etc.) accept a sole
  Vibium ``Element`` handle without a second ``find``.
- [x] **F12 / F27. Tap, Highlight, Touch Tap** (#70)
  ``Tap`` / ``Highlight`` (element) and ``Touch Tap`` (page coords via
  ``page.touch.tap``).

### Release (#52)

- [ ] **REL-1.0.0. Promote to 1.0.0** (#52)
  Version bump, CHANGELOG, classifier, tag, PyPI, Libdoc, close milestone.

### Exit criteria (REL-1.0.0)

- CI green: `ruff` + `mypy` + `pytest` + headless acceptance (#24)
- `vibium>=26.8.21` published as dependency floor — **met** (#47)
- `py.typed` in wheel (#16)
- Docs and `architecture.md` aligned with 1.0 scope (#55, #56) — **met**
- Zero open issues labeled `breaking-change`

## v1.1.0 — Vibium coverage I (additive)

Requires robotframework-vibium ≥ 1.0.0 and vibium ≥ 26.8.21.

- [ ] **F1. Network interception / mocking** (#27)
- [ ] **F2. Event capture / waiting** (#28)
- [ ] **F3. Network events** (#29)
- [ ] **F4. Console and JS errors** (#30)
- [ ] **F5. Downloads** (#31)
- [ ] **F26. Browser listeners** (#65 Part 2) — `on_page` / `on_popup` / `remove_all_listeners`

## v1.2.0 — Vibium coverage II (additive)

Requires robotframework-vibium ≥ 1.0.0 and vibium ≥ 26.8.21.

- [ ] **F6. Clock / simulated time** (#32)
- [ ] **F7. Video recording** (#33)
- [ ] **F8. Popups / multi-page** (#34)
- [ ] **F9. WebSocket** (#35)
- [ ] **F12, F15–F21. Remaining 1:1 wrappers** (#36)
  Core wrappers (F10, F11, F13, F14, F20, F22, F23) → **#51**; F24 → **#57**; F25 → **#67**; F12/F27 → **#70**.
  - [x] **F12. `Tap Element` / `Tap`** — done in #70 as ``Tap`` (+ ``Highlight``, ``Touch Tap``)
  - [ ] **F15. `Add Script Tag` / `Add Style Tag`**
  - [ ] **F16. `Add Init Script`**
  - [ ] **F17. `Expose Function`**
  - [ ] **F18. `Set Geolocation`**
  - [ ] **F19. `Emulate Media`**
  - [x] **F20. `Set Window` / `Get Window`** — done in #51 as `Set Window` / `Get Window Info`
  - [ ] **F21. `Set Extra HTTP Headers`** (may overlap #27)

## v1.x — Extensibility (additive, future)

- [ ] **D1. Plugin API** (#37)
- [ ] **D2. Per-component listener** (#38)
- [ ] **D3. Translation / localization** (#39)

---

## Key dependencies

- **1.0.0 before 1.1+**: stable core + Vibium 26.8.21 floor is the base for additive coverage.
- **V1 + V2 + V3 + V6/V6b/V6c + V7 + V8**: done (#47, #48, #49, #54, #72, #75, #55, #56).
- **C2 + E8 (#21, #23)**: should be done together.
- **A2 (#18)**: shipped in 1.0; follow-ups → #77 (v1.1).
- **#65 listeners**: launch parity done; browser event listeners → 1.1 (F26).
