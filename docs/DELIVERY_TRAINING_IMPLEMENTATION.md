# Delivery evidence, training and practical assessments

This continuation implements four previously incomplete proposal areas. It adds six tables, 22 HTTP operations and three frontend workspace modules. Existing collaboration pages gain milestone actions. The full contract has 277 REST paths and 350 HTTP operations plus the existing WebSocket route.

## Apply locally

From PowerShell, with your backend `.env` configured for your local PostgreSQL database:

```powershell
cd D:\SIH\Backend-Grad
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd D:\SIH\Frontend-Grad
npm.cmd run dev
```

The additive migration `ga20_delivery` follows `ga20_platform`. It creates completion certificates, project milestones, training programs/enrollments and practical assessments/submissions. Your application database was not migrated automatically; migration validation used an isolated test database.

## Completion certificates

The PDF now follows the supplied green-and-gold landscape reference: a hanging ribbon and medallion, gold border, prominent student name and engagement heading. It uses GradAlumni branding and actual issuance data. The reference's example names, signatures and duration claims are not copied into student credentials. Text scales within bounded regions for longer names/titles; revoked certificates carry a visible red status label. A non-valid sample is available at `output/pdf/student-certificate-sample.pdf`. No database migration is needed for this design update.

Proposal sections 26–28. Open **Workspace → Certificates**.

1. The opportunity owner completes the engagement through the existing application lifecycle.
2. The owner or assigned mentor records evaluation through the existing feedback endpoint.
3. The opportunity owner, or a platform administrator, issues the certificate using the application reference.
4. The student lists their certificates and downloads a PDF. The owner, assigned mentor and platform administrators can also download it.
5. A signed-in verifier can enter the unguessable verification code. The response contains the snapshotted recipient, engagement and issuer, issuance time and current validity; it does not expose account identifiers or evaluation scores.
6. The issuer or platform administrator can revoke with a reason. Subsequent verification reports invalidity and subsequent PDF downloads visibly show revocation.

Issuance is idempotent and serialized on the application. Revocation does not silently reissue a new credential. PDFs use a stored issuance snapshot, so later profile/title changes do not rewrite an issued credential. Verification is an online database-backed check, not a cryptographic PDF signature. Possession of a code allows authenticated verification; private download authorization is checked separately. Sharing the code intentionally shares the certificate's identity details.

Files: `app/services/certificate_service.py`, `app/api/proposed/delivery.py`.

## Project milestones

Proposal sections 23–24. Open **Workspace → Collaboration teams**.

- The collaboration owner creates milestones with descriptions and optional due dates.
- Active members submit an evidence URL and a note. Invited but inactive members cannot access the workflow.
- The owner accepts evidence or requests changes. A submitter cannot approve their own evidence.
- Accepted milestones determine collaboration progress. A team with milestones cannot be marked complete while any are unaccepted.
- Accepted submissions cannot be silently overwritten. Changes-requested submissions can be resubmitted and reviewed.

URLs are stored as evidence links; the server does not fetch them or execute submitted code. Owners should have another team member submit evidence for their review. Existing collaborations without milestones retain the original progress workflow.

Files: `app/api/proposed/delivery.py`, `app/api/proposed/collaborations.py`.

## Institution training cohorts

Proposal sections 29–31. Open **Workspace → Training programs**.

- An institution administrator creates a program with target skills and an optional discipline, and can open or close enrollment.
- Students can discover and enroll only in their assigned institution and eligible discipline. Institution assignments remain administrator-controlled.
- Enrollment records validated skill evidence as the baseline; self-declared scores and missing evidence count as zero.
- After training and assessment, the institution administrator records completion. This captures the latest validated scores without awarding new skill scores.
- The report compares paired baseline/outcome snapshots for completed participants and shows enrollment and completion counts. Results describe observed improvement, not proof that training caused it.
- Administrators cannot access another institution's program. Students who leave the institution are excluded from its identifiable report and cannot be completed by that institution.

Training content delivery, timetabling and automatic attendance integration are not included. Administrators confirm completion; skill validation remains the assessment/feedback workflow.

Files: `app/api/proposed/training.py`.

## Practical assessment and review

Proposal section 12. Open **Workspace → Practical assessments**.

- A verified academician, industry professional or alumni reviewer can author an assessment in their domain. Platform administrators can also author assessments.
- Every rubric entry identifies a skill and gives explicit evaluation criteria. Skills must belong to the assessment domain.
- Eligible students submit a repository/report/demonstration link and explanation. Only one pending attempt is permitted; a new attempt is possible after review.
- The assigned reviewer must still be authorized when reviewing. They score every rubric skill, provide feedback and cannot review their own submission.
- Review updates validated skill evidence and readiness. Reviewed submissions remain immutable; unrelated users cannot list submitted evidence.
- Archiving stops new submissions while preserving historical review records.

This enables human-reviewed coding/design and supervised practical evidence. It does not execute code, provide an automated coding judge, validate clinical licensure, or supply expert-authored clinical question banks.

Files: `app/api/proposed/practical.py`, `app/schemas/development.py`.

## Frontend and validation

The new operations are connected through role-aware workspace forms, reference selection and record views. PDF responses use the existing authenticated download support. Practical submission actions remain visible independently of the MCQ assessment runner. Backend authorization is authoritative even when a shared form is visible to more than one role.

Validation results are recorded in the proposal audit. Tests cover issuance prerequisites, duplicate issuance, download privacy, revocation, membership, review ownership, milestone progress, institution boundaries, skill snapshots, reviewer verification, rubric validation and immutable reviews. The PDF preview was rendered and visually inspected.

## Still outside completed scope

Full browser E2E, automated sandboxed code execution, clinical credential validation, authored career curricula, automated interdisciplinary team optimization, richer bespoke role dashboards, advanced semantic/LLM integrations and production deployment remain unfinished. These additions should not be described as completion of every item in the full proposal.
