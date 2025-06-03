from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from .utils import verify_password, get_password_hash, create_access_token
from Db.db_config import get_db_cursor
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



def register(user):
    mycursor, db_config = get_db_cursor()
    mycursor.execute("SELECT id FROM autenticator WHERE email = %s", (user.email,)) #verificacion de email
    if mycursor.fetchone():
        return {"error": "El email ya está registrado"}
    hashed_password = get_password_hash(user.passwd)
    sql = "INSERT INTO autenticator (nombre, email, passwd) VALUES (%s, %s, %s)"
    val = (user.nombre, user.email, hashed_password)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except Exception as err:
        return {"error": f"Error al registrar: {err}"}
    return {"message": "Usuario registrado exitosamente"}


def login(form_data: OAuth2PasswordRequestForm = Depends()):
    mycursor, _ = get_db_cursor()
    try:
        mycursor.execute("SELECT id, nombre, email, passwd FROM autenticator WHERE email = %s", (form_data.username,))
        user = mycursor.fetchone()
        if not user:
            return {"error": "Email no registrado"}
        if not verify_password(form_data.password, user[3]):
            return {"error": "Contraseña incorrecta"}
        access_token = create_access_token(data={"sub": user[2]})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as err:
        return {"error": f"Error en login: {err}"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    mycursor, _ = get_db_cursor()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    mycursor.execute("SELECT id, nombre, email FROM autenticator WHERE email = %s", (email,))
    user = mycursor.fetchone()
    if user is None:
        raise credentials_exception
    return {"id": user[0], "nombre": user[1], "email": user[2]}
