from services.category import (
    _process_category_deletion_cleanup,
    _audit_category_deletion,
    _update_category_statistics_cascade,
    _rebuild_category_search_index
)
from services.category import CategoryService
from fastapi import BackgroundTasks, HTTPException, status
import uuid
from typing import Optional
import logging
from tasks.models import TaskResults

logger = logging.getLogger(__name__)


async def delete_category(category_id: uuid.UUID,
                          background_tasks: BackgroundTasks,
                          content_action: str,
                          target_category_id: Optional[uuid.UUID],
                          subcategory_action: str,
                          force_delete: bool,
                          current_user: dict,
                          category_service: CategoryService) -> TaskResults:

    category = await category_service.get_category(
        category_id,
        include_parent=True,
        include_statistics=True
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Perform deletion using enhanced service layer
    deletion_result = await category_service.delete_category(
        category_id=category_id,
        current_user_id=uuid.UUID(current_user.get("user_id")),
        content_action=content_action,
        subcategory_action=subcategory_action,
        target_category_id=target_category_id,
        force_delete=force_delete
    )

    # Schedule background tasks for cleanup and processing
    background_tasks.add_task(
        _process_category_deletion_cleanup,
        str(category_id),
        deletion_result.get("statistics", {})
    )

    background_tasks.add_task(
        _audit_category_deletion,
        str(category_id),
        current_user.get("user_id"),
        {
            "category_name": deletion_result.get("category_name"),
            "actions_taken": deletion_result.get("actions_taken", {}),
            "statistics": deletion_result.get("statistics", {})
        }
    )

    # Update statistics for affected categories
    affected_categories = []
    if category.parent_id:
        affected_categories.append(str(category.parent_id))
    if target_category_id:
        affected_categories.append(str(target_category_id))

    if affected_categories:
        background_tasks.add_task(
            _update_category_statistics_cascade,
            affected_categories
        )

    # Rebuild search index for the affected category tree
    background_tasks.add_task(
        _rebuild_category_search_index,
        str(category.parent_id) if category.parent_id else None
    )

    logger.info(
        f"Category deleted successfully: {category_id}",
        extra={
            "category_id": str(category_id),
            "user_id": current_user.get("user_id"),
            "deletion_result": deletion_result
        }
    )

    return TaskResults(
        success=True,
        message="Category deleted successfully",
        object_id=str(category_id),
        results=deletion_result,
        background_tasks_scheduled=4
    )
