# API Routers package
from .trending import router as trending_router
from .stats import router as stats_router
from .settings import router as settings_router
from .tasks import router as tasks_router
from .analysis import router as analysis_router

__all__ = [
    'trending_router',
    'stats_router',
    'settings_router',
    'tasks_router',
    'analysis_router',
]
