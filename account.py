import time
import uuid

from fastapi import APIRouter
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

import controller
import models
import encrypt

router = APIRouter()


@router.post("/create")  # TODO: validate email
async def create_new_account(user: models.UserCreate):
    result = await controller.is_name_or_email_exist(user.name, user.email)
    if result == controller.IsNameOrEmailResult.NAME_EXIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name already exist"
        )
    if result == controller.IsNameOrEmailResult.EMAIL_EXIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exist"
        )
    if result == controller.IsNameOrEmailResult.BOTH_EMAIL_AND_NAME_EXIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both name and email already exist"
        )
    hashed_password = encrypt.get_password_hash(user.password)
    await controller.add_row(
        models.User(email=user.email, name=user.name, password=hashed_password, is_activated=True)
    )


@router.get("/is_name_exist")
async def is_name_exist(name: str):
    return await controller.is_name_exist(name)


@router.get("/is_email_exist")
async def is_email_exist(email: str):
    return await controller.is_email_exist(email)


@router.get("/user")
async def get_user(user: str):
    return await controller.get_user(user)


@router.post("/login", response_model=models.Token)
async def login_for_access_token(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends()):
    user = await encrypt.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO: validate client secret
    session_uuid = str(uuid.uuid4())
    await controller.add_row(models.Session(
        uuid=session_uuid,
        user_id=str(user.id),
        client_name=form_data.client_id,
        ip=request.client.host,
        last_active=time.time(),
        created_at=time.time()
    ))
    token_data = session_uuid + ":" + str(user.id)
    access_token = encrypt.create_access_token(data={"sub": token_data})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/renew_token", response_model=models.Token)
async def renew_access_token(token_data: str = Depends(encrypt.get_token_data)):
    access_token = encrypt.create_access_token(data={"sub": token_data})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")  # TODO: Create another model
async def read_users_me(current_user=Depends(encrypt.get_current_user)):
    print(current_user)
