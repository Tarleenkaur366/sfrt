from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.category import FinancialCategory
from app.models.transaction import FinancialTransaction
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, VALID_CATEGORY_TYPES
from app.routers.deps import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
def list_categories(
    category_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialCategory).filter(FinancialCategory.user_id == current_user.id)
    if category_type:
        query = query.filter(FinancialCategory.category_type == category_type.upper())
    return query.order_by(FinancialCategory.name.asc()).all()

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    req: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c_type = req.category_type.upper()
    if c_type not in VALID_CATEGORY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category type. Allowed types: {', '.join(VALID_CATEGORY_TYPES)}"
        )

    # Check duplicate name for user
    existing = db.query(FinancialCategory).filter(
        FinancialCategory.user_id == current_user.id,
        FinancialCategory.name == req.name.strip()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists."
        )

    cat = FinancialCategory(
        user_id=current_user.id,
        name=req.name.strip(),
        category_type=c_type,
        description=req.description.strip() if req.description else None
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    AuditService.log(db, current_user.id, "CREATE", "CATEGORY", cat.id, f"Created category '{cat.name}'")
    return cat

@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    req: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cat = db.query(FinancialCategory).filter(
        FinancialCategory.id == category_id,
        FinancialCategory.user_id == current_user.id
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    if req.name is not None:
        cat.name = req.name.strip()
    if req.category_type is not None:
        c_type = req.category_type.upper()
        if c_type not in VALID_CATEGORY_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category type.")
        cat.category_type = c_type
    if req.description is not None:
        cat.description = req.description.strip()

    db.commit()
    db.refresh(cat)
    AuditService.log(db, current_user.id, "UPDATE", "CATEGORY", cat.id, f"Updated category '{cat.name}'")
    return cat

@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cat = db.query(FinancialCategory).filter(
        FinancialCategory.id == category_id,
        FinancialCategory.user_id == current_user.id
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    # Unlink transactions (set category_id = NULL) to protect historical transaction integrity
    db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.category_id == category_id
    ).update({"category_id": None})

    db.delete(cat)
    db.commit()
    AuditService.log(db, current_user.id, "DELETE", "CATEGORY", category_id, f"Deleted category '{cat.name}'")
    return {"message": "Category deleted successfully."}
