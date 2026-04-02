from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.notifications import send_status_change_notification

router = APIRouter(prefix="/projects/{project_id}/issues", tags=["issues"])


def _get_project_or_404(project_id: int, db: Session, user_id: int) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return project


# ── Create ────────────────────────────────────────────────────────────────────


@router.post("/", response_model=schemas.IssueOut, status_code=201)
def create_issue(
    project_id: int,
    issue_in: schemas.IssueCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_project_or_404(project_id, db, current_user.id)
    issue = models.Issue(
        title=issue_in.title,
        description=issue_in.description,
        priority=issue_in.priority,
        project_id=project_id,
        reporter_id=current_user.id,
        assignee_id=issue_in.assignee_id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


# ── List (paginated) ──────────────────────────────────────────────────────────


@router.get("/", response_model=schemas.PaginatedIssues)
def list_issues(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_project_or_404(project_id, db, current_user.id)

    query = db.query(models.Issue).filter(models.Issue.project_id == project_id)

    if status:
        query = query.filter(models.Issue.status == status)
    if priority:
        query = query.filter(models.Issue.priority == priority)

    total = query.count()

    skip = (page - 1) * page_size
    items = query.order_by(models.Issue.created_at.desc()).offset(skip).limit(page_size).all()

    return schemas.PaginatedIssues(total=total, page=page, page_size=page_size, items=items)


# ── Search ────────────────────────────────────────────────────────────────────


@router.get("/search", response_model=List[schemas.IssueOut])
def search_issues(
    project_id: int,
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_project_or_404(project_id, db, current_user.id)

    results = (
        db.query(models.Issue)
        .filter(
            models.Issue.project_id == project_id,
            or_(
                models.Issue.title.ilike(f"%{q}%"),
                models.Issue.description.ilike(f"%{q}%"),
            ),
        )
        .order_by(models.Issue.updated_at.desc())
        .all()
    )
    return results


# ── Get one ───────────────────────────────────────────────────────────────────


@router.get("/{issue_id}", response_model=schemas.IssueOut)
def get_issue(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_project_or_404(project_id, db, current_user.id)
    issue = (
        db.query(models.Issue)
        .filter(models.Issue.id == issue_id, models.Issue.project_id == project_id)
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


# ── Update ────────────────────────────────────────────────────────────────────


@router.put("/{issue_id}", response_model=schemas.IssueOut)
async def update_issue(
    project_id: int,
    issue_id: int,
    issue_in: schemas.IssueUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # BUG: Missing authorization check. Any authenticated user who has access
    # to the project can update any issue, regardless of whether they are the
    # reporter or assignee. Add a check like:
    #
    #   if issue.reporter_id != current_user.id and issue.assignee_id != current_user.id:
    #       raise HTTPException(status_code=403, detail="Not authorized to edit this issue")

    _get_project_or_404(project_id, db, current_user.id)
    issue = (
        db.query(models.Issue)
        .filter(models.Issue.id == issue_id, models.Issue.project_id == project_id)
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    old_status = issue.status
    for field, value in issue_in.model_dump(exclude_unset=True).items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)

    if issue_in.status and issue_in.status != old_status:
        assignee_email = issue.assignee.email if issue.assignee else None
        reporter_email = issue.reporter.email if issue.reporter else None
        await send_status_change_notification(
            issue.id,
            issue.title,
            old_status,
            issue.status,
            assignee_email,
            reporter_email,
        )

    return issue


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete("/{issue_id}", status_code=204)
def delete_issue(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_project_or_404(project_id, db, current_user.id)
    issue = (
        db.query(models.Issue)
        .filter(models.Issue.id == issue_id, models.Issue.project_id == project_id)
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the reporter can delete an issue")

    db.delete(issue)
    db.commit()
