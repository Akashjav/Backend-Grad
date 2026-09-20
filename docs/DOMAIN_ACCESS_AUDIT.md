# Role and domain access audit

Reviewed 2026-09-19 against the local backend and frontend source.

**Conclusion: role access and domain-aware eligibility are implemented, but separate, strictly isolated Engineering and Ayurveda areas are not fully implemented.** This is a source and automated-test audit, not evidence of deployment to a live server.

## Existing behavior

| Area | Current implementation | Limitation |
| --- | --- | --- |
| Roles | Versioned APIs enforce roles, resource ownership, and assigned institution scope where applicable. Student, alumni, admin, and industry are supported. | Role checks alone do not separate academic domains. |
| Domain taxonomy | `Domain`, `Discipline`, `DomainProfile`, domain skills, competencies, and policies exist. Seed data defines Engineering/Computer Science and AYUSH/Ayurveda, plus other domains. | Ayurveda is a discipline under AYUSH. Seed definitions do not prove any particular deployment has loaded them. |
| Opportunity applications | With `cross_domain=false`, the student's profile domain must match; a specified discipline must also match. Mismatches return 403. | The profile's domain is self-editable, so this is not a verified institutional boundary. |
| Matching | Ineligible candidates are excluded from recommendations and employer candidate matches. | Eligibility uses the same self-declared domain data. |
| Cross-domain opportunities | `cross_domain=true` bypasses both domain and discipline eligibility checks. | This opens eligibility to all domains, not a curated subset. |
| Opportunity requirements | Non-cross-domain opportunities reject skills from another domain. | Publishers can create opportunities in domains other than their own. |
| Visibility | Published opportunities can be read by authenticated users across domains. Optional domain filters include cross-domain opportunities. | A filter is not authorization. Direct IDs do not enforce domain visibility. |
| Assessments and learning | Assessments carry domains; question skills must match their assessment domain. Assessment listing supports a domain filter. | Students can start another domain's assessment. Learning resources and public taxonomy are not restricted to the user's domain. |
| Profiles and directories | Ownership and privacy/discoverability checks protect relevant operations. | There is no universal domain restriction on directory browsing. |
| Frontend | Roles choose their dashboards/workspace. Active registration now uses versioned signup with domain and discipline selection. Workspace lists default to the user's domain where supported. | These filters and shared module pages do not enforce strict Engineering/AYUSH isolation. |
| Legacy API | Older jobs, dashboards, and registration remain available. | They do not consistently use `DomainProfile` or the new domain eligibility service. Versioned checks do not automatically apply to legacy routes. |

## Evidence

- `app/api/proposed/deps.py`: authentication, role, owner, and administrator helpers.
- `app/services/opportunities_service.py`: application domain/discipline eligibility.
- `app/services/matching_service.py`: matching eligibility and recommendation filtering.
- `app/api/proposed/opportunities.py`: visibility, optional filters, skill requirements.
- `app/services/identity_service.py`: `update_profile` permits domain changes after validating the taxonomy relationship.
- `app/api/proposed/assessments.py`: assessment access and attempt creation.
- `app/api/proposed/learning.py`, `organizations.py`: learning and directory access.
- `app/db/seed.py`: Engineering and AYUSH/Ayurveda catalogue definitions.
- `../Frontend-Grad/src/app/components/platform/PlatformRegistration.tsx`: active domain/discipline registration; the old `RegisterPage.tsx` is retained but is no longer the active registration screen.
- `../Frontend-Grad/src/app/components/platform/PlatformWorkspace.tsx`: role-aware modules and default domain filters.
- `../Frontend-Grad/src/lib/roleRedirect.ts`: role navigation, not domain navigation.

`tests/test_domain_access_audit.py` checks the Engineering-to-AYUSH application denial, explicit cross-domain allowance, candidate matching, ownership protection, and documents the current broader visibility, assessment access, and self-service domain-change behavior. Assertions documenting gaps must change when the policy changes.

## Work required for genuinely separate domain areas

1. Model role and verified domain membership independently: for example `student + Engineering` or `industry + AYUSH`. Decide whether one user may belong to multiple domains.
2. Make institution/admin approval authoritative for domain membership if it is intended as a security boundary; a self-editable profile must not grant protected access.
3. Centralize the domain policy and enforce it on both listings and direct-ID reads/writes, across versioned and legacy routes. Specify which catalogue and public collaboration information stays shared.
4. Define assessment/learning access explicitly and preserve intentional interdisciplinary learning through an explicit policy.
5. Domain and discipline onboarding selectors and default workspace domain filters are now implemented. Further domain-specific dashboard presentation and the centralized access policy remain separate requirements.
6. Give domain administrators an explicit scope if they must manage only Engineering or AYUSH; current global administrators are not domain administrators.
7. Test two users with the same role in different domains, forged domain filters, direct IDs, approved domain changes, legacy endpoints, and cross-domain exceptions.

These are remaining requirements, not completed changes. This audit does not silently impose new domain restrictions on existing users.

## Validation

- Backend after frontend integration: `python -m pytest -q` — 20 passed on SQLite, including the domain audit tests; one existing Starlette/AnyIO deprecation warning.
- Frontend: `npm.cmd test` — 16 passed, including role routing, versioned authentication, contract coverage and rendered module actions. 75 generated form payloads also pass backend model validation.
- Frontend production build: `npm.cmd run build` passed.
- An in-app browser was unavailable, so interactive UI behavior was not browser-verified.
