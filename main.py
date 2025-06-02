from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, StringConstraints, Field, field_validator
from typing import Annotated
from datetime import date
import mysql.connector

app = FastAPI()

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


# Create tables if they do not exist
mycursor.execute("""
CREATE TABLE IF NOT EXISTS usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    cargo VARCHAR(50) NOT NULL
)
""")

mycursor.execute("""
CREATE TABLE IF NOT EXISTS cliente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nit VARCHAR(20) NOT NULL UNIQUE
)
""")

mycursor.execute("""
CREATE TABLE IF NOT EXISTS producto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto VARCHAR(100) NOT NULL,
    precio_compra DECIMAL(10, 2) NOT NULL,
    precio_venta DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL
)
""")

mycursor.execute("""
CREATE TABLE IF NOT EXISTS venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    producto_id INT NOT NULL,
    cliente_id INT NOT NULL,
    usuario_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (producto_id) REFERENCES producto(id),
    FOREIGN KEY (cliente_id) REFERENCES cliente(id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
)
""")


#! -------- GET ALL -------------
#* Endpoint para obtener todos los usuarios
@app.get("/usuario")
def get_usuarios():
    mycursor.execute("SELECT * FROM usuario")
    usuarios = mycursor.fetchall()
    return {"usuarios": usuarios}

#* Endpoint para obtener todos los clientes
@app.get("/cliente")
def get_clientes():
    mycursor.execute("SELECT * FROM cliente")
    clientes = mycursor.fetchall()
    return {"clientes": clientes}

#* Endpoint para obtener todos los productos
@app.get("/producto")
def get_productos():
    mycursor.execute("SELECT * FROM producto")
    productos = mycursor.fetchall()
    return {"productos": productos}

#* Endpoint para obtener todas las ventas
@app.get("/venta")
def get_ventas():
    mycursor.execute("SELECT * FROM venta")
    ventas = mycursor.fetchall()
    return {"ventas": ventas}


#! -------- GET BY ID -------------
#* Endpoint para obtener un usuario por ID
@app.get("/usuario/{id}")
def get_usuario(id: int):
    mycursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
    usuario = mycursor.fetchone()
    if usuario:
        return {"usuario": usuario}
    return {"message": "Usuario no encontrado"} 

#* Endpoint para obtener un cliente por ID
@app.get("/cliente/{id}")
def get_cliente(id: int):
    mycursor.execute("SELECT * FROM cliente WHERE id = %s", (id,))
    cliente = mycursor.fetchone()
    if cliente:
        return {"cliente": cliente}
    return {"message": "Cliente no encontrado"}


#* Endpoint para obtener un producto por ID
@app.get("/producto/{id}")
def get_producto(id: int):
    mycursor.execute("SELECT * FROM producto WHERE id = %s", (id,))
    producto = mycursor.fetchone()
    if producto:
        return {"producto": producto}
    return {"message": "Producto no encontrado"}


#* Endpoint para obtener una venta por ID
@app.get("/venta/{id}")
def get_venta(id: int):
    mycursor.execute("SELECT * FROM venta WHERE id = %s", (id,))
    venta = mycursor.fetchone()
    if venta:
        return {"venta": venta}
    return {"message": "Venta no encontrada"}



#! ------- POST ALL -------------
#* Endpoint para crear un nuevo usuario
@app.post("/usuario")
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
@app.post("/cliente")
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
@app.post("/producto")
def create_producto(producto: Producto):
    sql = "INSERT INTO producto (producto, precio_compra, precio_venta, stock) VALUES (%s, %s, %s, %s)"
    val = (producto.producto, producto.precio_compra, producto.precio_venta, producto.stock)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al insertar producto: {err}"}
    return {"message": "Producto creado exitosamente", "producto": producto}

#* Endpoint para crear una nueva venta
@app.post("/venta")
def create_venta(venta: Venta):
    sql = "INSERT INTO venta (fecha, producto_id, cliente_id, usuario_id, cantidad, precio_unitario, total) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (venta.fecha, venta.producto_id, venta.cliente_id, venta.usuario_id, venta.cantidad, venta.precio_unitario, venta.total)
    try:
        mycursor.execute(sql, val)
        db_config.commit()
    except mysql.connector.Error as err:
        return {"error": f"Error al insertar venta: {err}"}
    return {"message": "Venta creada exitosamente", "venta": venta}


#! --------- PUT ALL -------------
#* Endpoint para actualizar un usuario
@app.put("/usuario/{id}")
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
@app.put("/cliente/{id}")
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
@app.put("/producto/{id}")
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

#* Endpoint para actualizar una venta
@app.put("/venta/{id}")
def update_venta(id: int, venta: Venta):
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
@app.delete("/usuario/{id}")
def delete_usuario(id: int):
    sql = "DELETE FROM usuario WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Usuario eliminado exitosamente"}
    else:
        return {"message": "No se encontró el usuario a eliminar"}

#* Endpoint para eliminar un cliente
@app.delete("/cliente/{id}")
def delete_cliente(id: int):
    sql = "DELETE FROM cliente WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Cliente eliminado exitosamente"}
    else:
        return {"message": "No se encontró el cliente a eliminar"}

#* Endpoint para eliminar un producto
@app.delete("/producto/{id}")
def delete_producto(id: int):
    sql = "DELETE FROM producto WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Producto eliminado exitosamente"}
    else:
        return {"message": "No se encontró el producto a eliminar"}

#* Endpoint para eliminar una venta
@app.delete("/venta/{id}")
def delete_venta(id: int):
    sql = "DELETE FROM venta WHERE id = %s"
    mycursor.execute(sql, (id,))
    db_config.commit()
    if mycursor.rowcount > 0:
        return {"message": "Venta eliminada exitosamente"}
    else:
        return {"message": "No se encontró la venta a eliminar"}
