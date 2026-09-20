# GradAlumni 2.0 API inventory

Generated from the running FastAPI route definitions. See `openapi.json` for request bodies and schemas.

| Method | Endpoint | Module |
|---|---|---|
| GET | `/` |  |
| GET | `/api/admin/alumni-earnings` | Admin |
| GET | `/api/admin/alumni-earnings/{alumni_id}` | Admin |
| POST | `/api/admin/alumni-payouts` | Admin |
| PATCH | `/api/admin/alumni-payouts/{payout_id}/mark-paid` | Admin |
| POST | `/api/admin/alumni/{alumni_id}/verify` | Admin |
| POST | `/api/admin/events/{event_id}/publish` | Admin |
| PATCH | `/api/admin/student-documents/{document_id}/verify` | Admin |
| GET | `/api/admin/users` | Admin |
| PATCH | `/api/admin/users/{user_id}/role` | Admin |
| POST | `/api/ai-chat/` | AI Assistant |
| GET | `/api/ai-chat/history` | AI Assistant |
| DELETE | `/api/ai-chat/history` | AI Assistant |
| GET | `/api/alumni/` | Alumni |
| POST | `/api/alumni/` | Alumni |
| GET | `/api/alumni/{alumni_id}` | Alumni |
| POST | `/api/auth/signin` | Auth |
| POST | `/api/auth/signup` | Auth |
| POST | `/api/auth/signup/alumni` | Auth |
| POST | `/api/auth/signup/student` | Auth |
| GET | `/api/communities/` | Communities |
| POST | `/api/communities/` | Communities |
| GET | `/api/communities/{community_id}` | Communities |
| POST | `/api/communities/{community_id}/join` | Communities |
| DELETE | `/api/communities/{community_id}/membership` | Communities |
| POST | `/api/communities/{community_id}/posts` | Community Posts |
| GET | `/api/communities/{community_id}/posts` | Community Posts |
| POST | `/api/community-posts/{post_id}/like` | Community Posts |
| DELETE | `/api/community-posts/{post_id}/like` | Community Posts |
| POST | `/api/community-posts/{post_id}/replies` | Community Posts |
| GET | `/api/community-posts/{post_id}/replies` | Community Posts |
| GET | `/api/conversations/` | Conversations |
| POST | `/api/conversations/` | Conversations |
| GET | `/api/conversations/{conversation_id}` | Conversations |
| GET | `/api/conversations/{conversation_id}/messages` | Conversations |
| POST | `/api/conversations/{conversation_id}/messages` | Conversations |
| POST | `/api/conversations/{conversation_id}/read` | Conversations |
| GET | `/api/dashboard/` | Dashboard |
| GET | `/api/dashboard/admin` | Dashboard |
| GET | `/api/dashboard/alumni` | Dashboard |
| GET | `/api/dashboard/student` | Dashboard |
| GET | `/api/domains` | Domains & Subscriptions |
| POST | `/api/domains` | Domains & Subscriptions |
| GET | `/api/events/` | Events |
| POST | `/api/events/` | Events |
| GET | `/api/events/{event_id}` | Events |
| POST | `/api/events/{event_id}/rsvp` | Events |
| DELETE | `/api/events/{event_id}/rsvp` | Events |
| GET | `/api/health` |  |
| POST | `/api/jobs/` | Jobs |
| GET | `/api/jobs/` | Jobs |
| GET | `/api/jobs/applied` | Jobs |
| GET | `/api/jobs/saved` | Jobs |
| GET | `/api/jobs/{job_id}` | Jobs |
| POST | `/api/jobs/{job_id}/apply` | Jobs |
| POST | `/api/jobs/{job_id}/save` | Jobs |
| DELETE | `/api/jobs/{job_id}/save` | Jobs |
| GET | `/api/me` | Users |
| POST | `/api/mentorship/requests` | Mentorship |
| GET | `/api/mentorship/requests/incoming` | Mentorship |
| GET | `/api/mentorship/requests/my` | Mentorship |
| PATCH | `/api/mentorship/requests/{request_id}/accept` | Mentorship |
| PATCH | `/api/mentorship/requests/{request_id}/reject` | Mentorship |
| POST | `/api/mentorship/sessions` | Mentorship |
| GET | `/api/mentorship/sessions/my` | Mentorship |
| PATCH | `/api/mentorship/sessions/{session_id}/cancel` | Mentorship |
| PATCH | `/api/mentorship/sessions/{session_id}/complete` | Mentorship |
| GET | `/api/notifications/` | Notifications |
| POST | `/api/notifications/` | Notifications |
| POST | `/api/notifications/read-all` | Notifications |
| POST | `/api/notifications/{notification_id}/read` | Notifications |
| GET | `/api/settings/` | Settings |
| PATCH | `/api/settings/account` | Settings |
| PATCH | `/api/settings/language` | Settings |
| PATCH | `/api/settings/notifications` | Settings |
| PATCH | `/api/settings/privacy` | Settings |
| PATCH | `/api/settings/security` | Settings |
| GET | `/api/student/documents/` | Student Documents |
| POST | `/api/student/documents/` | Student Documents |
| GET | `/api/subscription-plans` | Domains & Subscriptions |
| POST | `/api/subscription-plans` | Domains & Subscriptions |
| POST | `/api/subscriptions/activate` | Domains & Subscriptions |
| GET | `/api/subscriptions/me` | Domains & Subscriptions |
| POST | `/api/subscriptions/start-trial` | Domains & Subscriptions |
| GET | `/api/v1/academicians/{academician_id}/research` | 2.0 Alumni, academia and industry |
| POST | `/api/v1/admin/alumni/{user_id}/verify` | 2.0 Governance |
| GET | `/api/v1/admin/analytics` | 2.0 Governance |
| GET | `/api/v1/admin/audit-logs` | 2.0 Governance |
| POST | `/api/v1/admin/faculty/{user_id}/verify` | 2.0 Governance |
| POST | `/api/v1/admin/industry/{user_id}/verify` | 2.0 Governance |
| POST | `/api/v1/admin/opportunities/{opportunity_id}/approve` | 2.0 Governance |
| POST | `/api/v1/admin/portfolio/{item_id}/verify` | 2.0 Governance |
| GET | `/api/v1/admin/review-queue` | 2.0 Governance |
| POST | `/api/v1/admin/taxonomy/import` | 2.0 Governance |
| GET | `/api/v1/admin/users` | 2.0 Governance |
| PATCH | `/api/v1/admin/users/{user_id}/institution` | 2.0 Governance |
| POST | `/api/v1/admin/users/{user_id}/restore` | 2.0 Governance |
| PATCH | `/api/v1/admin/users/{user_id}/role` | 2.0 Governance |
| POST | `/api/v1/admin/users/{user_id}/skills/verify` | 2.0 Governance |
| POST | `/api/v1/admin/users/{user_id}/suspend` | 2.0 Governance |
| POST | `/api/v1/ai/career-assistant` | 2.0 Documents and intelligence |
| POST | `/api/v1/ai/opportunity/extract` | 2.0 Documents and intelligence |
| POST | `/api/v1/ai/profile/summarize` | 2.0 Documents and intelligence |
| POST | `/api/v1/ai/resume/extract` | 2.0 Documents and intelligence |
| POST | `/api/v1/ai/resume/map-skills` | 2.0 Documents and intelligence |
| GET | `/api/v1/alumni` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/alumni/me/profile` | 2.0 Alumni, academia and industry |
| PATCH | `/api/v1/alumni/me/profile` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/alumni/{user_id}` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/alumni/{user_id}/expertise` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/alumni/{user_id}/skills` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/applications/{application_id}` | 2.0 Opportunities and applications |
| POST | `/api/v1/applications/{application_id}/certificate` | 2.0 Certificates and milestones |
| POST | `/api/v1/applications/{application_id}/feedback` | 2.0 Opportunities and applications |
| PATCH | `/api/v1/applications/{application_id}/progress` | 2.0 Opportunities and applications |
| PATCH | `/api/v1/applications/{application_id}/status` | 2.0 Opportunities and applications |
| POST | `/api/v1/assessments` | 2.0 Assessments |
| GET | `/api/v1/assessments` | 2.0 Assessments |
| GET | `/api/v1/assessments/{assessment_id}` | 2.0 Assessments |
| POST | `/api/v1/assessments/{assessment_id}/reassess` | 2.0 Assessments |
| GET | `/api/v1/assessments/{assessment_id}/result` | 2.0 Assessments |
| POST | `/api/v1/assessments/{assessment_id}/start` | 2.0 Assessments |
| POST | `/api/v1/assessments/{assessment_id}/submit` | 2.0 Assessments |
| POST | `/api/v1/auth/forgot-password` | 2.0 Identity |
| GET | `/api/v1/auth/me` | 2.0 Identity |
| DELETE | `/api/v1/auth/me` | 2.0 Identity |
| PATCH | `/api/v1/auth/me` | 2.0 Identity |
| POST | `/api/v1/auth/refresh` | 2.0 Identity |
| POST | `/api/v1/auth/resend-otp` | 2.0 Identity |
| POST | `/api/v1/auth/reset-password` | 2.0 Identity |
| POST | `/api/v1/auth/signin` | 2.0 Identity |
| POST | `/api/v1/auth/signout` | 2.0 Identity |
| POST | `/api/v1/auth/signup` | 2.0 Identity |
| POST | `/api/v1/auth/verify-otp` | 2.0 Identity |
| GET | `/api/v1/certificates/me` | 2.0 Certificates and milestones |
| GET | `/api/v1/certificates/verify/{code}` | 2.0 Certificates and milestones |
| GET | `/api/v1/certificates/{certificate_id}/download` | 2.0 Certificates and milestones |
| POST | `/api/v1/certificates/{certificate_id}/revoke` | 2.0 Certificates and milestones |
| GET | `/api/v1/collaborations` | 2.0 Collaboration |
| POST | `/api/v1/collaborations` | 2.0 Collaboration |
| GET | `/api/v1/collaborations/{collaboration_id}` | 2.0 Collaboration |
| PATCH | `/api/v1/collaborations/{collaboration_id}` | 2.0 Collaboration |
| POST | `/api/v1/collaborations/{collaboration_id}/feedback` | 2.0 Collaboration |
| POST | `/api/v1/collaborations/{collaboration_id}/invite` | 2.0 Collaboration |
| POST | `/api/v1/collaborations/{collaboration_id}/join` | 2.0 Collaboration |
| POST | `/api/v1/collaborations/{collaboration_id}/members` | 2.0 Collaboration |
| GET | `/api/v1/collaborations/{collaboration_id}/members` | 2.0 Collaboration |
| DELETE | `/api/v1/collaborations/{collaboration_id}/members/{user_id}` | 2.0 Collaboration |
| GET | `/api/v1/collaborations/{collaboration_id}/milestones` | 2.0 Certificates and milestones |
| POST | `/api/v1/collaborations/{collaboration_id}/milestones` | 2.0 Certificates and milestones |
| GET | `/api/v1/collaborations/{collaboration_id}/progress` | 2.0 Collaboration |
| GET | `/api/v1/collaborations/{collaboration_id}/skills` | 2.0 Collaboration |
| GET | `/api/v1/communities` | 2.0 Foundation |
| POST | `/api/v1/communities` | 2.0 Foundation |
| GET | `/api/v1/communities/{community_id}` | 2.0 Foundation |
| POST | `/api/v1/communities/{community_id}/join` | 2.0 Foundation |
| DELETE | `/api/v1/communities/{community_id}/membership` | 2.0 Foundation |
| POST | `/api/v1/communities/{community_id}/posts` | 2.0 Foundation |
| GET | `/api/v1/communities/{community_id}/posts` | 2.0 Foundation |
| POST | `/api/v1/community-posts/{post_id}/like` | 2.0 Foundation |
| DELETE | `/api/v1/community-posts/{post_id}/like` | 2.0 Foundation |
| POST | `/api/v1/community-posts/{post_id}/replies` | 2.0 Foundation |
| GET | `/api/v1/community-posts/{post_id}/replies` | 2.0 Foundation |
| GET | `/api/v1/competencies` | 2.0 Taxonomy |
| POST | `/api/v1/competencies` | 2.0 Taxonomy |
| GET | `/api/v1/competencies/{competency_id}` | 2.0 Taxonomy |
| GET | `/api/v1/conversations` | 2.0 Foundation |
| POST | `/api/v1/conversations` | 2.0 Foundation |
| GET | `/api/v1/conversations/{conversation_id}` | 2.0 Foundation |
| GET | `/api/v1/conversations/{conversation_id}/messages` | 2.0 Foundation |
| POST | `/api/v1/conversations/{conversation_id}/messages` | 2.0 Foundation |
| POST | `/api/v1/conversations/{conversation_id}/read` | 2.0 Foundation |
| GET | `/api/v1/dashboard` | 2.0 Foundation |
| GET | `/api/v1/dashboard/admin` | 2.0 Foundation |
| GET | `/api/v1/dashboard/alumni` | 2.0 Foundation |
| GET | `/api/v1/dashboard/student` | 2.0 Foundation |
| GET | `/api/v1/disciplines` | 2.0 Taxonomy |
| POST | `/api/v1/disciplines` | 2.0 Taxonomy |
| GET | `/api/v1/disciplines/{discipline_id}` | 2.0 Taxonomy |
| GET | `/api/v1/documents/resume` | 2.0 Documents and intelligence |
| POST | `/api/v1/documents/resume` | 2.0 Documents and intelligence |
| GET | `/api/v1/documents/resume/{document_id}` | 2.0 Documents and intelligence |
| DELETE | `/api/v1/documents/resume/{document_id}` | 2.0 Documents and intelligence |
| GET | `/api/v1/documents/verification/{document_id}` | 2.0 Documents and intelligence |
| GET | `/api/v1/domains` | 2.0 Taxonomy |
| POST | `/api/v1/domains` | 2.0 Taxonomy |
| GET | `/api/v1/domains/{domain_id}` | 2.0 Taxonomy |
| PATCH | `/api/v1/domains/{domain_id}` | 2.0 Taxonomy |
| GET | `/api/v1/domains/{domain_id}/competency-map` | 2.0 Taxonomy |
| GET | `/api/v1/domains/{domain_id}/disciplines` | 2.0 Taxonomy |
| PUT | `/api/v1/domains/{domain_id}/weights` | 2.0 Taxonomy |
| GET | `/api/v1/events` | 2.0 Foundation |
| POST | `/api/v1/events` | 2.0 Foundation |
| GET | `/api/v1/events/{event_id}` | 2.0 Foundation |
| POST | `/api/v1/events/{event_id}/rsvp` | 2.0 Foundation |
| DELETE | `/api/v1/events/{event_id}/rsvp` | 2.0 Foundation |
| GET | `/api/v1/faculty` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/faculty/consultancy` | 2.0 Projects and research |
| POST | `/api/v1/faculty/consultancy` | 2.0 Projects and research |
| GET | `/api/v1/faculty/consultancy/{item_id}` | 2.0 Projects and research |
| PATCH | `/api/v1/faculty/consultancy/{item_id}` | 2.0 Projects and research |
| DELETE | `/api/v1/faculty/consultancy/{item_id}` | 2.0 Projects and research |
| POST | `/api/v1/faculty/consultancy/{item_id}/apply` | 2.0 Projects and research |
| GET | `/api/v1/faculty/fdp` | 2.0 Projects and research |
| POST | `/api/v1/faculty/fdp` | 2.0 Projects and research |
| GET | `/api/v1/faculty/fdp/{item_id}` | 2.0 Projects and research |
| PATCH | `/api/v1/faculty/fdp/{item_id}` | 2.0 Projects and research |
| DELETE | `/api/v1/faculty/fdp/{item_id}` | 2.0 Projects and research |
| POST | `/api/v1/faculty/fdp/{item_id}/apply` | 2.0 Projects and research |
| GET | `/api/v1/faculty/me/profile` | 2.0 Alumni, academia and industry |
| PATCH | `/api/v1/faculty/me/profile` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/faculty/{user_id}` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/faculty/{user_id}/expertise` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry/me/candidate-matches` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry/me/faculty-matches` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry/me/opportunities` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry/me/profile` | 2.0 Alumni, academia and industry |
| PATCH | `/api/v1/industry/me/profile` | 2.0 Alumni, academia and industry |
| POST | `/api/v1/industry/profile` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry/{user_id}` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/industry/{user_id}/expertise` | 2.0 Alumni, academia and industry |
| GET | `/api/v1/institutions` | 2.0 Institutions and analytics |
| POST | `/api/v1/institutions` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/analytics` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/departments` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/industry-collaboration` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/placement` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/profile` | 2.0 Institutions and analytics |
| PATCH | `/api/v1/institutions/me/profile` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/readiness` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/reports` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/skill-demand` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/skill-gaps` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/students` | 2.0 Institutions and analytics |
| GET | `/api/v1/institutions/me/training-programs` | 2.0 Institution training |
| POST | `/api/v1/institutions/me/training-programs` | 2.0 Institution training |
| PATCH | `/api/v1/institutions/me/training-programs/{program_id}` | 2.0 Institution training |
| POST | `/api/v1/institutions/me/training-programs/{program_id}/enrollments/{enrollment_id}/complete` | 2.0 Institution training |
| GET | `/api/v1/institutions/me/training-programs/{program_id}/report` | 2.0 Institution training |
| GET | `/api/v1/institutions/{institution_id}` | 2.0 Institutions and analytics |
| GET | `/api/v1/learning/resources` | 2.0 Learning |
| POST | `/api/v1/learning/resources` | 2.0 Learning |
| GET | `/api/v1/learning/resources/{resource_id}` | 2.0 Learning |
| POST | `/api/v1/learning/{resource_id}/complete` | 2.0 Learning |
| POST | `/api/v1/learning/{resource_id}/start` | 2.0 Learning |
| POST | `/api/v1/matching/candidates/{student_id}/score` | 2.0 Matching and skill gaps |
| POST | `/api/v1/matching/opportunities/{opportunity_id}/score` | 2.0 Matching and skill gaps |
| GET | `/api/v1/matching/{match_id}/explanation` | 2.0 Matching and skill gaps |
| GET | `/api/v1/matching/{match_id}/skill-gaps` | 2.0 Matching and skill gaps |
| GET | `/api/v1/mentors` | 2.0 Mentor discovery and feedback |
| GET | `/api/v1/mentors/recommended` | 2.0 Mentor discovery and feedback |
| GET | `/api/v1/mentorship/requests` | 2.0 Mentor discovery and feedback |
| POST | `/api/v1/mentorship/requests` | 2.0 Foundation |
| GET | `/api/v1/mentorship/requests/incoming` | 2.0 Foundation |
| GET | `/api/v1/mentorship/requests/my` | 2.0 Foundation |
| PATCH | `/api/v1/mentorship/requests/{request_id}` | 2.0 Mentor discovery and feedback |
| PATCH | `/api/v1/mentorship/requests/{request_id}/accept` | 2.0 Foundation |
| PATCH | `/api/v1/mentorship/requests/{request_id}/reject` | 2.0 Foundation |
| GET | `/api/v1/mentorship/sessions` | 2.0 Mentor discovery and feedback |
| POST | `/api/v1/mentorship/sessions` | 2.0 Foundation |
| GET | `/api/v1/mentorship/sessions/my` | 2.0 Foundation |
| PATCH | `/api/v1/mentorship/sessions/{session_id}/cancel` | 2.0 Foundation |
| PATCH | `/api/v1/mentorship/sessions/{session_id}/complete` | 2.0 Foundation |
| POST | `/api/v1/mentorship/sessions/{session_id}/feedback` | 2.0 Mentor discovery and feedback |
| POST | `/api/v1/milestones/{milestone_id}/review` | 2.0 Certificates and milestones |
| POST | `/api/v1/milestones/{milestone_id}/submit` | 2.0 Certificates and milestones |
| GET | `/api/v1/notifications` | 2.0 Foundation |
| POST | `/api/v1/notifications` | 2.0 Foundation |
| POST | `/api/v1/notifications/read-all` | 2.0 Foundation |
| POST | `/api/v1/notifications/{notification_id}/read` | 2.0 Foundation |
| GET | `/api/v1/opportunities` | 2.0 Opportunities and applications |
| POST | `/api/v1/opportunities` | 2.0 Opportunities and applications |
| GET | `/api/v1/opportunities/{opportunity_id}` | 2.0 Opportunities and applications |
| PATCH | `/api/v1/opportunities/{opportunity_id}` | 2.0 Opportunities and applications |
| DELETE | `/api/v1/opportunities/{opportunity_id}` | 2.0 Opportunities and applications |
| GET | `/api/v1/opportunities/{opportunity_id}/applications` | 2.0 Opportunities and applications |
| POST | `/api/v1/opportunities/{opportunity_id}/apply` | 2.0 Opportunities and applications |
| POST | `/api/v1/opportunities/{opportunity_id}/publish` | 2.0 Opportunities and applications |
| GET | `/api/v1/opportunities/{opportunity_id}/requirements` | 2.0 Opportunities and applications |
| POST | `/api/v1/opportunities/{opportunity_id}/requirements` | 2.0 Opportunities and applications |
| PATCH | `/api/v1/opportunities/{opportunity_id}/requirements/{requirement_id}` | 2.0 Opportunities and applications |
| GET | `/api/v1/practical-assessments` | 2.0 Practical assessments |
| POST | `/api/v1/practical-assessments` | 2.0 Practical assessments |
| DELETE | `/api/v1/practical-assessments/{practical_id}` | 2.0 Practical assessments |
| POST | `/api/v1/practical-assessments/{practical_id}/submit` | 2.0 Practical assessments |
| GET | `/api/v1/practical-submissions` | 2.0 Practical assessments |
| POST | `/api/v1/practical-submissions/{submission_id}/review` | 2.0 Practical assessments |
| GET | `/api/v1/projects` | 2.0 Projects and research |
| POST | `/api/v1/projects` | 2.0 Projects and research |
| GET | `/api/v1/projects/{item_id}` | 2.0 Projects and research |
| PATCH | `/api/v1/projects/{item_id}` | 2.0 Projects and research |
| DELETE | `/api/v1/projects/{item_id}` | 2.0 Projects and research |
| POST | `/api/v1/projects/{item_id}/apply` | 2.0 Projects and research |
| GET | `/api/v1/projects/{project_id}/members` | 2.0 Projects and research |
| POST | `/api/v1/projects/{project_id}/members` | 2.0 Projects and research |
| POST | `/api/v1/projects/{project_id}/mentor` | 2.0 Projects and research |
| GET | `/api/v1/recommendations/internships` | 2.0 Matching and skill gaps |
| GET | `/api/v1/recommendations/jobs` | 2.0 Matching and skill gaps |
| GET | `/api/v1/recommendations/mentors` | 2.0 Mentor discovery and feedback |
| GET | `/api/v1/recommendations/opportunities` | 2.0 Matching and skill gaps |
| GET | `/api/v1/recommendations/projects` | 2.0 Matching and skill gaps |
| GET | `/api/v1/recommendations/research` | 2.0 Matching and skill gaps |
| GET | `/api/v1/research` | 2.0 Projects and research |
| POST | `/api/v1/research` | 2.0 Projects and research |
| GET | `/api/v1/research/{item_id}` | 2.0 Projects and research |
| PATCH | `/api/v1/research/{item_id}` | 2.0 Projects and research |
| DELETE | `/api/v1/research/{item_id}` | 2.0 Projects and research |
| POST | `/api/v1/research/{item_id}/apply` | 2.0 Projects and research |
| GET | `/api/v1/settings` | 2.0 Foundation |
| PATCH | `/api/v1/settings/account` | 2.0 Foundation |
| PATCH | `/api/v1/settings/language` | 2.0 Foundation |
| PATCH | `/api/v1/settings/notifications` | 2.0 Foundation |
| PATCH | `/api/v1/settings/privacy` | 2.0 Foundation |
| PATCH | `/api/v1/settings/security` | 2.0 Foundation |
| GET | `/api/v1/skills` | 2.0 Taxonomy |
| POST | `/api/v1/skills` | 2.0 Taxonomy |
| GET | `/api/v1/skills/search` | 2.0 Taxonomy |
| GET | `/api/v1/skills/{skill_id}` | 2.0 Taxonomy |
| PATCH | `/api/v1/skills/{skill_id}` | 2.0 Taxonomy |
| GET | `/api/v1/skills/{skill_id}/assessment-framework` | 2.0 Assessments |
| GET | `/api/v1/students/me/applications` | 2.0 Opportunities and applications |
| GET | `/api/v1/students/me/assessment-history` | 2.0 Assessments |
| GET | `/api/v1/students/me/career-paths` | 2.0 Matching and skill gaps |
| GET | `/api/v1/students/me/competencies` | 2.0 Student competency |
| POST | `/api/v1/students/me/competencies/recalculate` | 2.0 Student competency |
| GET | `/api/v1/students/me/education` | 2.0 Student competency |
| POST | `/api/v1/students/me/education` | 2.0 Student competency |
| PATCH | `/api/v1/students/me/education/{item_id}` | 2.0 Student competency |
| DELETE | `/api/v1/students/me/education/{item_id}` | 2.0 Student competency |
| GET | `/api/v1/students/me/learning-history` | 2.0 Learning |
| GET | `/api/v1/students/me/learning-recommendations` | 2.0 Learning |
| GET | `/api/v1/students/me/learning-roadmap` | 2.0 Learning |
| GET | `/api/v1/students/me/portfolio` | 2.0 Student competency |
| POST | `/api/v1/students/me/portfolio` | 2.0 Student competency |
| PATCH | `/api/v1/students/me/portfolio/{item_id}` | 2.0 Student competency |
| DELETE | `/api/v1/students/me/portfolio/{item_id}` | 2.0 Student competency |
| GET | `/api/v1/students/me/profile` | 2.0 Student competency |
| PATCH | `/api/v1/students/me/profile` | 2.0 Student competency |
| GET | `/api/v1/students/me/readiness` | 2.0 Student competency |
| GET | `/api/v1/students/me/readiness/history` | 2.0 Student competency |
| GET | `/api/v1/students/me/skill-gaps` | 2.0 Matching and skill gaps |
| POST | `/api/v1/students/me/skill-gaps/recalculate` | 2.0 Matching and skill gaps |
| GET | `/api/v1/students/me/skill-gaps/{gap_id}` | 2.0 Matching and skill gaps |
| POST | `/api/v1/students/me/skill-gaps/{gap_id}/reassess` | 2.0 Learning |
| GET | `/api/v1/students/me/skills` | 2.0 Student competency |
| PUT | `/api/v1/students/me/skills` | 2.0 Student competency |
| GET | `/api/v1/students/me/training-programs` | 2.0 Institution training |
| POST | `/api/v1/training-programs/{program_id}/enroll` | 2.0 Institution training |
| GET | `/health` |  |

## WebSocket

`WS /api/v1/ws/conversations/{conversation_id}`: send `{"token":"ACCESS_TOKEN"}` as the first frame within 10 seconds, then `{"body":"message"}`.

Messages are persisted in PostgreSQL. Other participants receive committed messages through one-second database polling. No in-memory broadcast dependency; Redis pub/sub is a future scaling optimization.

## Earlier API specification coverage

186 / 186 distinct method/path targets registered. Path parameter names are normalized for comparison. This is route coverage, not a claim that every route is independently integration-tested.
