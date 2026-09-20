"""Idempotent taxonomy/demo seed. No credentials are embedded in source."""

import argparse
import asyncio
import os
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db import base  # noqa: F401 - register all ORM tables
from app.models.user import User
from app.models.profile import Profile
from app.models.student import StudentProfile
from app.models.alumni import AlumniProfile
from app.models.subscription import Domain
from app.models.platform import (
    Discipline,
    DomainProfile,
    DomainPolicy,
    Institution,
    Skill,
    Competency,
    StudentSkill,
    Assessment,
    LearningResource,
    Opportunity,
    Requirement,
)
from app.services.identity_service import password_hash

CATALOG = {
    "Engineering": (
        "Computer Science",
        [
            ("Python", "technical"),
            ("SQL", "technical"),
            ("Machine Learning", "technical"),
            ("Docker", "technical"),
            ("AWS", "technical"),
            ("Communication", "communication"),
        ],
    ),
    "Medical": (
        "MBBS",
        [
            ("Clinical Examination", "clinical"),
            ("Communication", "communication"),
            ("Research Methodology", "research"),
            ("Digital Health", "technical"),
        ],
    ),
    "AYUSH": (
        "Ayurveda",
        [
            ("Ayurvedic Knowledge", "domain"),
            ("Clinical Competency", "clinical"),
            ("Research Methodology", "research"),
            ("Communication", "communication"),
            ("Digital Health", "technical"),
        ],
    ),
    "Pharmacy": ("Pharmacy", [("Pharmacology", "domain")]),
    "Science": ("General Science", []),
    "Agriculture": ("Agriculture", []),
    "Management": ("Management", []),
    "Commerce": ("Commerce", []),
    "Law": ("Law", []),
    "Arts and Humanities": ("Humanities", []),
    "Other": ("Other", []),
}


async def ensure(db, model, lookup, **values):
    row = (await db.scalars(select(model).filter_by(**lookup))).first()
    if not row:
        row = model(**lookup, **values)
        db.add(row)
        await db.flush()
    return row


async def run(demo=False):
    async with AsyncSessionLocal() as db:
        institution = await ensure(
            db,
            Institution,
            {"name": "GradAlumni Demo Institution"},
            description="Synthetic demonstration data",
        )
        catalog = {}
        for domain_name, (discipline_name, names) in CATALOG.items():
            domain = await ensure(db, Domain, {"name": domain_name})
            discipline = await ensure(
                db, Discipline, {"name": discipline_name, "domain_id": domain.id}
            )
            skills = []
            for name, category in names:
                skill = await ensure(
                    db,
                    Skill,
                    {"name": name, "domain_id": domain.id},
                    category=category,
                    aliases=["Amazon Web Services"] if name == "AWS" else [],
                )
                skills.append(skill)
                await ensure(
                    db,
                    LearningResource,
                    {"skill_id": skill.id, "title": f"{name} guided practice"},
                    url="https://example.com/demo-learning-resource",
                    kind="project",
                    target_level=80,
                )
            if skills:
                await ensure(
                    db,
                    Competency,
                    {"domain_id": domain.id, "name": f"{domain_name} foundation"},
                    skill_weights={str(s.id): 1 for s in skills},
                )
                categories = {s.category for s in skills}
                await ensure(
                    db,
                    DomainPolicy,
                    {"domain_id": domain.id},
                    readiness_weights={c: 1 for c in categories},
                )
                # These are workflow test questions, not professional assessment instruments.
                await ensure(
                    db,
                    Assessment,
                    {"domain_id": domain.id, "title": f"{domain_name} DEMO assessment"},
                    questions=[
                        {
                            "id": f"skill-{s.id}",
                            "prompt": f"DEMO: Choose the evidence-based practice option for {s.name}.",
                            "options": [
                                "Practice with reviewed evidence",
                                "Skip validation",
                            ],
                            "answer": 0,
                            "skill_id": s.id,
                            "weight": 1,
                        }
                        for s in skills
                    ],
                )
            catalog[domain_name] = domain, discipline, skills
        admin_email, admin_password = (
            os.getenv("BOOTSTRAP_ADMIN_EMAIL"),
            os.getenv("BOOTSTRAP_ADMIN_PASSWORD"),
        )
        if admin_email and admin_password:
            if len(admin_password) < 12:
                raise ValueError(
                    "BOOTSTRAP_ADMIN_PASSWORD must have at least 12 characters"
                )
            admin = await ensure(
                db,
                User,
                {"email": admin_email.lower()},
                role="super_admin",
                is_verified=True,
                password_hash=password_hash(admin_password),
            )
            # Never promote a pre-existing account based on an email collision.
            if admin.role != "super_admin":
                raise ValueError(
                    "Bootstrap email already belongs to a non-admin account"
                )
            await ensure(
                db,
                Profile,
                {"user_id": admin.id},
                display_name="Platform Administrator",
            )
            await ensure(db, DomainProfile, {"user_id": admin.id})
        if demo:
            password = os.getenv("DEMO_PASSWORD", "")
            if len(password) < 12:
                raise ValueError(
                    "Set DEMO_PASSWORD to at least 12 characters before --demo"
                )
            seeded = {}
            for role, domain_name in [
                ("student", "Engineering"),
                ("student", "Medical"),
                ("student", "AYUSH"),
                ("industry", "Engineering"),
                ("academician", "Medical"),
                ("alumni", "Engineering"),
                ("institution_admin", "Engineering"),
            ]:
                domain, discipline, skills = catalog[domain_name]
                email = f"{role}.{domain_name.lower()}@demo.gradalumni.example.com"
                user = await ensure(
                    db,
                    User,
                    {"email": email},
                    role=role,
                    is_verified=True,
                    password_hash=password_hash(password),
                )
                await ensure(
                    db,
                    Profile,
                    {"user_id": user.id},
                    display_name=f"Demo {domain_name} {role}",
                )
                await ensure(
                    db,
                    DomainProfile,
                    {"user_id": user.id},
                    domain_id=domain.id,
                    discipline_id=discipline.id,
                    institution_id=institution.id,
                    interests=["research", "healthcare", "backend"],
                    verified=True,
                )
                if role == "student":
                    await ensure(
                        db,
                        StudentProfile,
                        {"user_id": user.id},
                        department=discipline.name,
                    )
                elif role == "alumni":
                    await ensure(db, AlumniProfile, {"user_id": user.id})
                levels = (
                    [85, 80, 70, 20, 10, 75]
                    if domain_name == "Engineering"
                    else [88, 85, 40, 30, 25]
                )
                for skill, score in zip(skills, levels):
                    await ensure(
                        db,
                        StudentSkill,
                        {"user_id": user.id, "skill_id": skill.id},
                        score=score,
                        evidence_type="assessment_verified",
                        evidence={
                            "source": "synthetic-demo",
                            "not_real_assessment": True,
                        },
                    )
                seeded[role, domain_name] = user
            industry = seeded["industry", "Engineering"]
            for domain_name in ["Engineering", "Medical", "AYUSH"]:
                domain, discipline, skills = catalog[domain_name]
                opp = await ensure(
                    db,
                    Opportunity,
                    {
                        "title": f"Demo {domain_name} Internship",
                        "owner_id": industry.id,
                    },
                    domain_id=domain.id,
                    description="Synthetic demonstration opportunity",
                    status="published",
                    approved=True,
                    interests=["research"],
                )
                for skill in skills:
                    await ensure(
                        db,
                        Requirement,
                        {"opportunity_id": opp.id, "skill_id": skill.id},
                        level=60,
                        weight=1,
                        core=True,
                    )
            eng = catalog["Engineering"]
            project = await ensure(
                db,
                Opportunity,
                {
                    "title": "AI + Healthcare + Ayurveda Research Project",
                    "owner_id": industry.id,
                },
                domain_id=eng[0].id,
                description="Synthetic cross-disciplinary team demonstration",
                kind="project",
                cross_domain=True,
                status="published",
                approved=True,
                interests=["research", "healthcare"],
            )
            for name, index in [("Engineering", 2), ("Medical", 0), ("AYUSH", 0)]:
                await ensure(
                    db,
                    Requirement,
                    {
                        "opportunity_id": project.id,
                        "skill_id": catalog[name][2][index].id,
                    },
                    level=70,
                    weight=1,
                    core=True,
                )
        await db.commit()
    print(
        "Seed completed. Demo learning URLs and assessment questions are explicitly synthetic."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    asyncio.run(run(parser.parse_args().demo))
