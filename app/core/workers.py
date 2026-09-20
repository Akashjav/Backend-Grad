from anyio import CapacityLimiter, to_thread

password_limiter = CapacityLimiter(4)
document_limiter = CapacityLimiter(2)


async def password_work(function, *args):
    return await to_thread.run_sync(function, *args, limiter=password_limiter)


async def document_work(function, *args):
    return await to_thread.run_sync(function, *args, limiter=document_limiter)
