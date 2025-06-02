from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, StringConstraints, Field, field_validator
from typing import Annotated
from datetime import date, timedelta, datetime
import mysql.connector
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, status

# app = FastAPI()
app = FastAPI(
    title="Mi API",
    description="Documentación organizada por módulos",
    version="1.0.0",
    openapi_tags=[
        {"name": "usuario", "description": "Operaciones con usuarios"},
        {"name": "producto", "description": "Gestión de productos"},
        {"name": "cliente", "description": "Administración de clientes"},
        {"name": "venta", "description": "Control de ventas"},
        {"name": "autenticador", "description": "Login y autenticación"},
    ]
)


# Configuración JWT
SECRET_KEY = "supersecretkeyjwt123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

try:
    db_config = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="ProyectoF",
        port=3306
    )
    print(f"Conexión exitosa a la base de datos MySQL")
except mysql.connector.Error as err:
    print(f"Error al conectar a la base de datos: {err}")

mycursor = db_config.cursor()


#* ----------- USUARIO Model-----------
class Usuario(BaseModel):
    id: int
    username: str
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=10)]
    cargo: str

#* ----------- CLIENTE Model-----------
class Cliente(BaseModel):
    id: int
    nombre: Annotated[str, StringConstraints(min_length=1)]  # obligatorio
    nit: Annotated[str, StringConstraints(min_length=9)]     # mayor a 8 caracteres

#* ----------- PRODUCTO Model-----------
class Producto(BaseModel):
    id: int
    producto: Annotated[str, StringConstraints(min_length=1)]
    precio_compra: float
    precio_venta: float
    stock: Annotated[int, Field(ge=0)]  # no puede ser negativo

    @field_validator('precio_compra')
    @classmethod
    def validar_precio_compra(cls, v):
        if v <= 0:
            raise ValueError('El precio de compra debe ser mayor a 0')
        return v

    @field_validator('precio_venta')
    @classmethod
    def validar_precio_venta(cls, v):
        if v < 0:
            raise ValueError('El precio de venta no puede ser negativo')
        return v

#* ----------- VENTA Model -----------
class Venta(BaseModel):
    id: int
    fecha: date
    producto_id: int
    cliente_id: int
    usuario_id: int
    cantidad: Annotated[int, Field(gt=0)]  # mayor a 0
    precio_unitario: float
    total: float

#* ----------- AUTENTICACIÓN Model -----------
class RegisterModel(BaseModel):
    nombre: str
    email: EmailStr
    passwd: str

class LoginModel(BaseModel):
    email: EmailStr
    passwd: str



#* ----------- Logica de autenticacion y hasheo de passwd -----------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def get_current_user(token: str = Depends(oauth2_scheme)):
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

# --------- FIN Auth -------------

#! -------- GET ALL -------------
#* Endpoint para obtener todos los usuarios
@app.get("/usuarios", tags=["usuario"])
def get_usuarios():
    mycursor.execute("SELECT * FROM usuario")
    usuarios = mycursor.fetchall()
    return {"usuarios": usuarios}

#* Endpoint para obtener todos los clientes
@app.get("/clientes", tags=["cliente"])
def get_clientes():
    mycursor.execute("SELECT * FROM cliente")
    clientes = mycursor.fetchall()
    return {"clientes": clientes}

#* Endpoint para obtener todos los productos
@app.get("/productos", tags=["producto"])
def get_productos():
    mycursor.execute("SELECT * FROM producto")
    productos = mycursor.fetchall()
    return {"productos": productos}

#* Endpoint para obtener todas las ventas (protegido)
@app.get("/ventas", tags=["venta"])
def get_ventas(current_user: dict = Depends(get_current_user)):
    mycursor.execute("SELECT * FROM venta")
    ventas = mycursor.fetchall()
    return {"ventas": ventas}


#! -------- GET BY ID -------------
#* Endpoint para obtener un usuario por ID
@app.get("/usuarios/{id}", tags=["usuario"])
def get_usuario(id: int):
    mycursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
    usuario = mycursor.fetchone()
    if usuario:
        return {"usuario": usuario}
    return {"message": "Usuario no encontrado"} 

#* Endpoint para obtener un cliente por ID
@app.get("/clientes/{id}", tags=["cliente"])
def get_cliente(id: int):
    mycursor.execute("SELECT * FROM cliente WHERE id = %s", (id,))
    cliente = mycursor.fetchone()
    if cliente:
        return {"cliente": cliente}
    return {"message": "Cliente no encontrado"}


#* Endpoint para obtener un producto por ID
@app.get("/productos/{id}", tags=["producto"])
def get_producto(id: int):
    mycursor.execute("SELECT * FROM producto WHERE id = %s", (id,))
    producto = mycursor.fetchone()
    if producto:
        return {"producto": producto}
    return {"message": "Producto no encontrado"}


#* Endpoint para obtener una venta por ID (protegido)
@app.get("/ventas/{id}", tags=["venta"])
def get_venta(id: int, current_user: dict = Depends(get_current_user)):
    mycursor.execute("SELECT * FROM venta WHERE id = %s", (id,))
    venta = mycursor.fetchone()
    if venta:
        return {"venta": venta}
    return {"message": "Venta no encontrada"}



#! ------- POST ALL -------------
#* Endpoint para crear un nuevo usuario
@app.post("/usuarios", tags=["usuario"])
def create_usuario(usuario: Usuario):
    sql = "INSERT INTO usuario (username, email, password, cargo) VALUES (%s, %s, %s, %s)"
    val = (usuario.username, usuario.email, usuario.password, usuario.cargo)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al insertar usuario: {err}"}
    return {"message": "Usuario creado exitosamente", "usuario": usuario}

#* Endpoint para crear un nuevo cliente
@app.post("/clientes", tags=["cliente"])
def create_cliente(cliente: Cliente):
    sql = "INSERT INTO cliente (nombre, nit) VALUES (%s, %s)"
    val = (cliente.nombre, cliente.nit)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al insertar cliente: {err}"}
    return {"message": "Cliente creado exitosamente", "cliente": cliente}

#* Endpoint para crear un nuevo producto
@app.post("/productos", tags=["producto"])
def create_producto(producto: Producto):
    sql = "INSERT INTO producto (producto, precio_compra, precio_venta, stock) VALUES (%s, %s, %s, %s)"
    val = (producto.producto, producto.precio_compra, producto.precio_venta, producto.stock)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al insertar producto: {err}"}
    return {"message": "Producto creado exitosamente", "producto": producto}

#* Endpoint para registrar usuario en autenticator
@app.post("/auth/register", tags=["autenticador"])
def register(user: RegisterModel):
    hashed_password = get_password_hash(user.passwd)
    sql = "INSERT INTO autenticator (nombre, email, passwd) VALUES (%s, %s, %s)"
    val = (user.nombre, user.email, hashed_password)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al registrar: {err}"}
    return {"message": "Usuario registrado exitosamente"}

# Endpoint para login y obtener token
@app.post("/auth/login", tags=["autenticador"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    mycursor.execute("SELECT id, nombre, email, passwd FROM autenticator WHERE email = %s", (form_data.username,))
    user = mycursor.fetchone()
    if not user or not verify_password(form_data.password, user[3]):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")
    access_token = create_access_token(data={"sub": user[2]})
    return {"access_token": access_token, "token_type": "bearer"}


#! --------- PUT ALL -------------
#* Endpoint para actualizar un usuario
@app.put("/usuarios/{id}", tags=["usuario"])
def update_usuario(id: int, usuario: Usuario):
    sql = "UPDATE usuario SET username = %s, email = %s, password = %s, cargo = %s WHERE id = %s"
    val = (usuario.username, usuario.email, usuario.password, usuario.cargo, id)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al actualizar usuario: {err}"}
    if mycursor.rowcount > 0:
        return {"message": "Usuario actualizado exitosamente", "usuario": usuario}
    return {"message": "No se encontró el usuario a actualizar"}

#* Endpoint para actualizar un cliente
@app.put("/clientes/{id}", tags=["cliente"])
def update_cliente(id: int, cliente: Cliente):
    sql = "UPDATE cliente SET nombre = %s, nit = %s WHERE id = %s"
    val = (cliente.nombre, cliente.nit, id)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al actualizar cliente: {err}"}
    if mycursor.rowcount > 0:
        return {"message": "Cliente actualizado exitosamente", "cliente": cliente}
    return {"message": "No se encontró el cliente a actualizar"}

#* Endpoint para actualizar un producto
@app.put("/productos/{id}", tags=["producto"])
def update_producto(id: int, producto: Producto):
    sql = "UPDATE producto SET producto = %s, precio_compra = %s, precio_venta = %s, stock = %s WHERE id = %s"
    val = (producto.producto, producto.precio_compra, producto.precio_venta, producto.stock, id)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al actualizar producto: {err}"}
    if mycursor.rowcount > 0:
        return {"message": "Producto actualizado exitosamente", "producto": producto}
    return {"message": "No se encontró el producto a actualizar"}

#* Endpoint para actualizar una venta (protegido)
@app.put("/ventas/{id}", tags=["venta"])
def update_venta(id: int, venta: Venta, current_user: dict = Depends(get_current_user)):
    sql = "UPDATE venta SET fecha = %s, producto_id = %s, cliente_id = %s, usuario_id = %s, cantidad = %s, precio_unitario = %s, total = %s WHERE id = %s"
    val = (venta.fecha, venta.producto_id, venta.cliente_id, venta.usuario_id, venta.cantidad, venta.precio_unitario, venta.total, id)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al actualizar venta: {err}"}
    if mycursor.rowcount > 0:
        return {"message": "Venta actualizada exitosamente", "venta": venta}
    return {"message": "No se encontró la venta a actualizar"}



#! ----------DELETE ALL --------------
#* Endpoint para eliminar un usuario
@app.delete("/usuarios/{id}", tags=["usuario"])
def delete_usuario(id: int):
    sql = "DELETE FROM usuario WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Usuario eliminado exitosamente"}
    else:
        return {"message": "No se encontró el usuario a eliminar"}

#* Endpoint para eliminar un cliente
@app.delete("/clientes/{id}", tags=["cliente"])
def delete_cliente(id: int):
    sql = "DELETE FROM cliente WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Cliente eliminado exitosamente"}
    else:
        return {"message": "No se encontró el cliente a eliminar"}

#* Endpoint para eliminar un producto
@app.delete("/productos/{id}", tags=["producto"])
def delete_producto(id: int):
    sql = "DELETE FROM producto WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Producto eliminado exitosamente"}
    else:
        return {"message": "No se encontró el producto a eliminar"}

#* Endpoint para eliminar una venta (protegido)
@app.delete("/ventas/{id}", tags=["venta"])
def delete_venta(id: int, current_user: dict = Depends(get_current_user)):
    sql = "DELETE FROM venta WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Venta eliminada exitosamente"}
    else:
        return {"message": "No se encontró la venta a eliminar"}
