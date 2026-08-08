# Import every model module here. app/database.py's init_db() calls
# Base.metadata.create_all(), which only creates tables for models that have
# actually been imported somewhere by the time it runs. Routers only import the
# specific models they use directly, so models with no router (Decision, Strategy,
# ExecutionPlan, Task, ResearchSession, ResearchSource, ProductAnalytics,
# LearningFingerprint, OnboardingQuestion) were silently never getting their
# tables created. Importing app.models (this file) from app/database.py before
# create_all() runs fixes that for good, regardless of which routers exist later.

from app.models.user import User
from app.models.product import Product
from app.models.knowledge import MasterKnowledge, OnboardingQuestion
from app.models.decision import Decision
from app.models.research import ResearchSession, ResearchSource
from app.models.strategy import Strategy, ExecutionPlan, Task
from app.models.analytics import ProductAnalytics, LearningFingerprint
from app.models.execution import WorkerExecution, WorkerEventLog

__all__ = [
    "User", "Product", "MasterKnowledge", "OnboardingQuestion", "Decision",
    "ResearchSession", "ResearchSource", "Strategy", "ExecutionPlan", "Task",
    "ProductAnalytics", "LearningFingerprint",
    "WorkerExecution", "WorkerEventLog",
]
