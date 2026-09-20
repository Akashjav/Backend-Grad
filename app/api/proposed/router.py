from fastapi import APIRouter
from app.api.proposed import mentorship as mentor_discovery
from app.api.proposed import delivery, training, practical
from app.api.proposed import (
    auth,
    taxonomy,
    students,
    assessments,
    opportunities,
    matching,
    learning,
    documents,
    organizations,
    projects,
    collaborations,
    institutions,
    governance,
    communication,
)

router = APIRouter(prefix="/api/v1")
router.include_router(mentor_discovery.router)
router.include_router(delivery.router)
router.include_router(training.router)
router.include_router(practical.router)
for module in [
    auth,
    taxonomy,
    students,
    assessments,
    opportunities,
    matching,
    learning,
    documents,
    organizations,
    projects,
    collaborations,
    institutions,
    governance,
    communication,
]:
    router.include_router(module.router)


def include_foundation_routes():
    """Reuse foundation APIs under v1, replacing their auth/db dependencies."""
    from fastapi.routing import APIRoute
    from app.api.V1 import (
        communities,
        community_posts,
        events,
        conversations,
        notifications,
        settings,
        mentorship,
        dashboard,
    )
    from app.api.V1.users import get_current_user
    from app.api.deps import get_db
    from app.api.proposed.deps import current_user, transaction
    import inspect
    from fastapi import params

    for module in [
        communities,
        community_posts,
        events,
        conversations,
        notifications,
        settings,
        mentorship,
        dashboard,
    ]:
        for route in module.router.routes:
            if not isinstance(route, APIRoute):
                continue
            # Build a wrapper with the same validated signature and v1 session auth.
            original = route.endpoint

            async def endpoint(_original=original, **kwargs):
                return await _original(**kwargs)

            parameters = []
            for p in inspect.signature(original).parameters.values():
                default = p.default
                if isinstance(default, params.Depends):
                    if default.dependency == get_current_user:
                        default = params.Depends(current_user)
                    elif default.dependency == get_db:
                        default = params.Depends(transaction)
                parameters.append(p.replace(default=default))
            endpoint.__signature__ = inspect.signature(original).replace(
                parameters=parameters
            )
            endpoint.__name__ = (
                f"v1_{module.__name__.split('.')[-1]}_{original.__name__}"
            )
            path = route.path.removeprefix("/api").rstrip("/") or "/"
            router.add_api_route(
                path,
                endpoint,
                methods=list(route.methods),
                tags=["2.0 Foundation"],
                response_model=route.response_model,
            )


include_foundation_routes()
