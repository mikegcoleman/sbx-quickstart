from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(
    prefix="/projects/{project_id}/issues/{issue_id}/comments",
    tags=["comments"],
)


def _get_issue_or_404(
    project_id: int, issue_id: int, db: Session, user_id: int
) -> models.Issue:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project or project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    issue = (
        db.query(models.Issue)
        .filter(models.Issue.id == issue_id, models.Issue.project_id == project_id)
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/", response_model=schemas.CommentOut, status_code=201)
def add_comment(
    project_id: int,
    issue_id: int,
    comment_in: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_issue_or_404(project_id, issue_id, db, current_user.id)
    comment = models.Comment(
        content=comment_in.content,
        issue_id=issue_id,
        author_id=current_user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/", response_model=List[schemas.CommentOut])
def list_comments(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_issue_or_404(project_id, issue_id, db, current_user.id)
    return (
        db.query(models.Comment)
        .filter(models.Comment.issue_id == issue_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    project_id: int,
    issue_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_issue_or_404(project_id, issue_id, db, current_user.id)
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")
    db.delete(comment)
    db.commit()
