from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import (
    FastAPI,
    Depends,
    Request,
    Form,
    HTTPException,
    status,
    Response,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Base, Sale, UserModel
from schemas import User, SaleCreate
from database import engine, get_db
from forecasting import forecast_with_dynamic_features
from authenticate import (
    authenticate_user,
    get_user_roles,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
)


Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    db_user = UserModel(username=username, email=email)
    db_user.set_password(password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return RedirectResponse(url="/", status_code=303)


@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.username == username).first()

    if not user or not user.check_password(password):
        return RedirectResponse(
            url="/register", status_code=status.HTTP_303_SEE_OTHER
        )

    roles = get_user_roles(user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": roles},
        expires_delta=access_token_expires,
    )

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/", response_class=HTMLResponse)
def read_root(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    forecast_list = forecast_with_dynamic_features(db)
    past_sales = db.query(Sale).order_by(desc(Sale.sale_date)).limit(20).all()

    past_sales_list = [
        {
            "item_id": sale.item_id,
            "date": sale.sale_date.strftime("%Y-%m-%d"),
            "quantity": sale.quantity,
        }
        for sale in past_sales
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "forecast": forecast_list,
            "past_sales": past_sales_list,
            "current_user": current_user,
        },
    )


@app.post("/add_sale")
def add_sale(
    sale_date: str = Form(...),
    quantity: int = Form(...),
    item_id: int = Form(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin role required.",
        )

    sale_date = datetime.strptime(sale_date, "%Y-%m-%d").date()
    new_sale = Sale(sale_date=sale_date, quantity=quantity, item_id=item_id)
    db.add(new_sale)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/sales")
def create_sale(
        sale: SaleCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user),
):
    if not current_user or "admin" not in get_user_roles(current_user):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    db_sale = Sale(
        sale_date=sale.sale_date.date(),
        quantity=sale.quantity,
        item_id=sale.item_id,
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return {
        "message": "Продажа успешно добавлена.",
        "sale": {
            "sale_date": db_sale.sale_date,
            "quantity": db_sale.quantity,
            "item_id": db_sale.item_id,
        },
    }


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user or "admin" not in get_user_roles(current_user):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    return templates.TemplateResponse(
        "admin.html", {"request": request, "current_user": current_user}
    )
