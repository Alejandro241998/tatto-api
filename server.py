from dataclasses import fields
import json
import re
import base64
import urllib, os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, DATETIME, FLOAT
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from flask_marshmallow import Marshmallow
from dotenv import load_dotenv
from cryptography.fernet import Fernet

import datetime

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
SQL_SERVER_URL = os.getenv('SQL_SERVER_URL')
f = Fernet(SECRET_KEY)
params = urllib.parse.quote_plus(SQL_SERVER_URL)

app = Flask(__name__)


# ENGINE CONNECT (SQLALCHEMY)
engine = create_engine( "mssql+pyodbc:///?odbc_connect=%s" % params, echo=True)
Session = sessionmaker(bind=engine)
sess = Session()
Base = declarative_base()
ma = Marshmallow(app)

class Operador(Base):
	__tablename__ = 'Operador'
	id = Column(Integer, primary_key=True, autoincrement=True)
	nombre = Column(String(60), nullable=False)
	apellido = Column(String(60), nullable=False)
	sexo = Column(String(1), nullable=False)
	usuario = Column(String(10), nullable=False)
	clave = Column(String(255), nullable=False)
	fecha_registro = Column(DATETIME, nullable=False)
	rol = Column(String(20), nullable=False)

class Region(Base):
	__tablename__ = 'Region'
	id_region = Column(Integer, primary_key=True, autoincrement=True)
	nomRegion = Column(String(50), nullable=False)
	field_data = relationship('Persona', backref="Region", uselist=False)

class Persona(Base):
	__tablename__ = 'Persona'
	id_persona = Column(Integer, primary_key=True, autoincrement=True)
	nomPersona = Column(String(50), nullable=False)
	apellidosPersona = Column(String(50), nullable=False)
	sexoPersona = Column(String(1), nullable=False)
	edadPersona = Column(Integer, nullable=False)
	fechaNacim = Column(DATETIME, nullable=False)
	pesoP = Column(FLOAT, nullable=False)
	estaturaP = Column(FLOAT, nullable=False)
	ladoTatuaje = Column(String(10), nullable=False)
	regionNacim = Column(Integer, ForeignKey(Region.id_region))

class Imagen(Base):
	__tablename__ = 'Imagen'
	idImg = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(50), nullable=False)
	color = Column(String(50), nullable=False)
	description = Column(String(50), nullable=False)
	fecha_registro = Column(DATETIME, nullable=False)
	path_img = Column(String(255), nullable=False)
	categoria = Column(String(50), nullable=False)

class Cuerpo(Base):
	__tablename__ = 'Cuerpo'
	id = Column(Integer, primary_key=True, autoincrement=True)
	lado = Column(String(10), nullable=False)
	tattoId = Column(String(10), nullable=False)
	region = Column(String(50), nullable=False)

Base.metadata.create_all(engine)

# SCHEMAS
class OperadorSchema(ma.Schema):
	class Meta:
		fields = ('id', 'nombre', 'apellido', 'sexo', 'usuario', 'clave', 'fecha_registro', 'rol')

class PersonaSchema(ma.Schema):
	class Meta:
		fields = ('id_persona', 'nomPersona', 'apellidosPersona', 'sexoPersona', 'edadPersona', 'fechaNacim', 'pesoP', 'estaturaP', 'ladoTatuaje', 'regionNacim')

class RegionSchema(ma.Schema):
	class Meta:
		fields = ('id_region', 'nomRegion')

class CategoriaSchema(ma.Schema):
	class Meta:
		fields = ('idCategoria', 'nomCategoria')

class ImagenSchema(ma.Schema):
	class Meta:
		fields = ('idImg', 'name', 'color', 'description', 'categoria', 'fecha_registro', 'path_img')

class CuerpoSchema(ma.Schema):
	class Meta:
		fields = ('id', 'lado', 'tattoId', 'region')


operador_schema = OperadorSchema()
operadores_schema = OperadorSchema(many=True)

persona_schema = PersonaSchema()
personas_schema = PersonaSchema(many=True)

region_schema = RegionSchema()
regiones_schema = RegionSchema(many=True)

categoria_schema = CategoriaSchema()
categorias_schema = CategoriaSchema(many=True)

imagen_schema = ImagenSchema()
imagenes_schema = ImagenSchema(many=True)

cuerpo_schema = CuerpoSchema()
cuerpos_schema = CuerpoSchema(many=True)
# Test ENDPOINTS
@app.route('/', methods=['POST'])
def test(): return jsonify({'message': "success", "code":200})

# AUTH ENDPOINTS
@app.route('/api/v1/auth/login/', methods=['POST'])
def login():
	print('/api/v1/auth/login/')
	user, passwd = request.form['user'], request.form['password']

	# check if user exists in db
	user = sess.query(Operador).filter_by(usuario=user).first()

	if not user:
		return jsonify({'message': 'Usuario o contraseña invalidos', 'code': 404})

	# decrypt password
	user_pass = f.decrypt(user.clave.encode('utf-8'))

	if str(user_pass, 'utf-8') != passwd: return jsonify({'message': 'Usuario o contraseña invalidos', 'code': 401})

	# save user to db
	return jsonify({'message': 'success', 'code': 200, "data": operador_schema.dump(user)})

# operators ENDPOINTS
@app.route('/api/v1/operators/register', methods=['POST'])
def register():
	print('/api/v1/operators/register')
	nombre = request.json['Nombre']
	apellido = request.json['Apellido']
	sexo = request.json['Sexo']
	usuario = request.json['User']
	passwd = request.json['Password']
	fecha_registro = request.json['FechaRegistro']
	rol = request.json['Rol']

	# encrypt password
	passwd = f.encrypt(passwd.encode('utf-8'))

	# convert feccha_registro to datetime object
	fecha_registro = datetime.datetime.strptime(fecha_registro, "%d/%m/%Y").strftime("%Y-%m-%d")

	# check if user exists in db
	user = sess.query(Operador).filter_by(usuario=usuario).first()

	if user: return jsonify({'message': 'Usuario ya existe', 'code': 400})

	# create new user
	new_user = Operador(nombre=nombre, apellido=apellido, sexo=sexo, usuario=usuario, clave=passwd, fecha_registro=fecha_registro, rol=rol)
	sess.add(new_user)
	sess.commit()

	# find user in db
	user = sess.query(Operador).filter_by(usuario=usuario).first()

	print(operador_schema.dump(user))

	return jsonify({'message': 'success', 'code': 200, "data": operador_schema.dump(new_user)})



@app.route('/api/v1/operators/deleteall', methods=['POST'])
def clear_all_users():
	print('/api/v1/auth/clear')
	sess.query(Operador).delete()
	sess.commit()
	return jsonify({'message': 'success', 'code': 200})

@app.route('/api/v1/operators/delete/<int:id>', methods=['POST'])
def delete_user(id):
	print('/api/v1/operators/delete')
	user = sess.query(Operador).filter_by(id=id).first()

	if not user:
		return jsonify({'message': 'El usuario no existe', 'code': 400})
	sess.delete(user)
	sess.commit()
	return jsonify({'message': 'success', 'code': 200, 'data': operador_schema.dump(user)})

@app.route('/api/v1/operators/getall', methods=['GET'])
def get_all_users():
	print('/api/v1/auth/getall')
	users = sess.query(Operador).all()
	return jsonify({'message': 'success', 'code': 200, 'data': operadores_schema.dump(users)})

# get by name
@app.route('/api/v1/operadores/getbyname', methods=['POST'])
def get_operador_by_name():
	print('/api/v1/operadores/getbyname')
	nombre = request.form['nombre']
	operador = sess.query(Operador).filter_by(nombre=nombre).first()
	if not operador:
		return jsonify({'message': 'No se encontro el operador', 'code': 404})
	return jsonify({'message': 'success', 'code': 200, 'data': operador_schema.dump(operador)})

# get by apellido
@app.route('/api/v1/operadores/getbylastname', methods=['POST'])
def get_operador_by_lastname():
	print('/api/v1/operadores/getbylastname')
	apellido = request.form['apellido']
	operador = sess.query(Operador).filter_by(apellido=apellido).first()
	if not operador:
		return jsonify({'message': 'No se encontro el operador', 'code': 404})
	return jsonify({'message': 'success', 'code': 200, 'data': operador_schema.dump(operador)})

# update operador
@app.route('/api/v1/operadores/update', methods=['POST'])
def update_operador():
	print('/api/v1/operadores/update')
	nombre = request.json['Nombre']
	apellido = request.json['Apellido']
	sexo = request.json['Sexo']
	usuario = request.json['User']
	passwd = request.json['Password']
	fecha_registro = request.json['FechaRegistro']
	rol = request.json['Rol']

	# check if user exists in sqlserver
	user = sess.query(Operador).filter_by(usuario=usuario).first()
	if not user:
		return jsonify({'message': 'El usuario no existe', 'code': 404})

	# encrypt password
	passwd = f.encrypt(passwd.encode('utf-8'))

	# convert feccha_registro to datetime object
	fecha_registro = datetime.datetime.strptime(fecha_registro, "%d/%m/%Y").strftime("%Y-%m-%d")

	# update user in sqlserver
	user.nombre = nombre
	user.apellido = apellido
	user.sexo = sexo
	user.usuario = usuario
	user.passwd = passwd
	user.fecha_registro = fecha_registro
	user.rol = rol
	sess.commit()

	return jsonify({'message': 'success', 'code': 200, 'data': operador_schema.dump(user)})

# ENPOINTS REGIONES
@app.route('/api/v1/regiones/create', methods=['POST'])
def create_region():
	# create regions from array
	regiones = ['Abasolo', 'Aldama', 'Altamira', 'Antiguo', 'Morelos', 'Burgos', 'Bustamante', 'Camargo', 'Casas', 'Ciudad Madero', 'Cruillas', 'Gomez Farias',
	'Gonzalez', 'Guemez', 'Guerrero', 'Gustavo Diaz Ordaz', 'Hidalgo', 'Jaumave', 'Jimenez', 'Llera',  'Mainero', 'El Mante', 'Matamoros',
	'Mendez', 'Mier', 'Miguel Aleman', 'Miquihuana', 'Nuevo Laredo', 'Nuevo Morelos', 'Ocampo', 'Padilla', 'Palmillas', 'Reynosa', 'Rio Bravo',
	'San Carlos', 'San Fernando', 'San Nicolas', 'Soto la Marina', 'Tampico', 'Tula', 'Valle Hermoso', 'Victoria', 'Villagran', 'Xicotencatl']

	for region in regiones:
		# search if region exists
		region_ = sess.query(Region).filter_by(nomRegion=region).first()

		if not region_:
			new_region = Region(nomRegion=region)
			sess.add(new_region)
			sess.commit()
			print('region added')
		else:
			return jsonify({'message': 'Las regiones ya existen', 'code': 400})

	return jsonify({'message': 'success', 'code': 200})

@app.route('/api/v1/regiones/deleteall', methods=['POST'])
def clear_all_regiones():
	print('/api/v1/auth/clear')
	sess.query(Region).delete()
	sess.commit()
	return jsonify({'message': 'success', 'code': 200})

@app.route('/api/v1/regiones/getall', methods=['GET'])
def get_all_regiones():
	print('/api/v1/auth/getall')
	regiones = sess.query(Region).all()
	return jsonify({'message': 'success', 'code': 200, 'data': regiones_schema.dump(regiones)})

# ENPOINTS PERSONAS
@app.route('/api/v1/personas/register', methods=['POST'])
def register_persona():
	print('/api/v1/personas/register')
	nomPersona = request.json['Nombre']
	apellidosPersona = request.json['Apellido']
	sexoPersona = request.json['Sexo']
	edadPersona = request.json['Edad']
	fechaNacim = request.json['FechaNacimiento']
	pesoP = request.json['Peso']
	estaturaP =  request.json['Estatura']
	ladoTatuaje = request.json['LadoTatuaje']
	regionNacim = request.json['NombreRegion']

	# convert feccha_registro to datetime object
	fechaNacim = datetime.datetime.strptime(fechaNacim, "%d/%m/%Y").strftime("%Y-%m-%d")

	persona = sess.query(Persona).filter_by(nomPersona=nomPersona).first()
	region = sess.query(Region).filter_by(nomRegion=regionNacim).first()

	if persona: return jsonify({'message': 'La persona ya existe', 'code': 400})
	if not region: return jsonify({'message': 'La region no existe', 'code': 400})

	# create persona
	new_persona = Persona(
		nomPersona=nomPersona,
		apellidosPersona=apellidosPersona,
		sexoPersona=sexoPersona,
		edadPersona=int(edadPersona),
		fechaNacim=fechaNacim,
		pesoP=float(pesoP),
		estaturaP=float(estaturaP),
		ladoTatuaje=ladoTatuaje,
		regionNacim=region.id_region
	)
	sess.add(new_persona)
	sess.commit()

	data = persona_schema.dump(new_persona)
	data['regionNacim'] = region.nomRegion

	return jsonify({'message': 'success', 'code': 200, 'data': data})

@app.route('/api/v1/personas/getall', methods=['GET'])
def get_all_personas():
	print('/api/v1/auth/getall')
	personas = sess.query(Persona).all()

	data = []
	
	# get region name for each persona and append to data
	for persona in personas:
		region = sess.query(Region).filter_by(id_region=persona.regionNacim).first()
		data.append(persona_schema.dump(persona))
		data[-1]['regionNacim'] = region.nomRegion

	return jsonify({'message': 'success', 'code': 200, 'data': data})

@app.route('/api/v1/personas/deleteall', methods=['POST'])
def clear_all_personas():
	print('/api/v1/auth/clear')
	sess.query(Persona).delete()
	sess.commit()
	return jsonify({'message': 'success', 'code': 200})

# delete persona by id
@app.route('/api/v1/personas/delete/<int:id_persona>', methods=['POST'])
def delete_persona(id_persona):
	print('/api/v1/auth/delete')
	persona = sess.query(Persona).filter_by(id_persona=id_persona).first()
	if not persona: return jsonify({'message': 'La persona no existe', 'code': 400})
	sess.delete(persona)
	sess.commit()
	return jsonify({'message': 'success', 'code': 200})

# get persona by name
@app.route('/api/v1/personas/getbyname', methods=['POST'])
def get_persona_by_name():
	print('/api/v1/personas/getbyname')
	nombre = request.form['nombre']
	persona = sess.query(Persona).filter_by(nomPersona=nombre).first()
	
	if not persona: return jsonify({'message': 'No se encontro la persona', 'code': 404})
	
	data = persona_schema.dump(persona)
	region = sess.query(Region).filter_by(id_region=persona.regionNacim).first()
	data['regionNacim'] = region.nomRegion

	return jsonify({'message': 'success', 'code': 200, 'data': data})

# get persona by last name
@app.route('/api/v1/personas/getbylastname', methods=['POST'])
def get_persona_by_last_name():
	print('/api/v1/personas/getbylastname')
	apellido = request.form['apellido']
	persona = sess.query(Persona).filter_by(apellidosPersona=apellido).first()
	
	if not persona: return jsonify({'message': 'No se encontro la persona', 'code': 404})
	
	data = persona_schema.dump(persona)
	region = sess.query(Region).filter_by(id_region=persona.regionNacim).first()
	data['regionNacim'] = region.nomRegion

	return jsonify({'message': 'success', 'code': 200, 'data': data})

# update persona by id
@app.route('/api/v1/personas/update/<int:id_persona>', methods=['POST'])
def update_persona(id_persona):
	print('/api/v1/personas/update/<int:id_persona> | POST')
	persona = sess.query(Persona).filter_by(id_persona=id_persona).first()
	if not persona: return jsonify({'message': 'La persona no existe', 'code': 400})

	fecha_nacim = datetime.datetime.strptime(request.json['FechaNacimiento'], "%d/%m/%Y").strftime("%Y-%m-%d")

	region = sess.query(Region).filter_by(nomRegion=request.json['NombreRegion']).first()

	# update persona
	persona.nomPersona = request.json['Nombre']
	persona.apellidosPersona = request.json['Apellido']
	persona.sexoPersona = request.json['Sexo']
	persona.edadPersona = int(request.json['Edad'])
	persona.fechaNacim = fecha_nacim
	persona.pesoP = float(request.json['Peso'])
	persona.estaturaP = float(request.json['Estatura'])
	persona.ladoTatuaje = request.json['LadoTatuaje']
	persona.regionNacim = region.id_region
	
	sess.commit()

	data = persona_schema.dump(persona)
	data['regionNacim'] = region.nomRegion

	return jsonify({'message': 'success', 'code': 200, 'data': data})

# Image modules
@app.route('/api/v1/image/register', methods=['POST'])
def register_image():
	image = request.json['Image']
	color = request.json['Color']
	name = request.json['Name']
	description = request.json['Description']
	category = request.json['Category']
	fecha_registro = request.json['FechaRegistro']

	fecha_registro = datetime.datetime.strptime(fecha_registro, "%d/%m/%Y").strftime("%Y-%m-%d")

	# convert base64 to image and save it
	image_path = f'./images/{name}.jpg'
	with open(image_path, "wb") as fh: fh.write(base64.decodebytes(image.encode()))

	# save image data in database
	new_imagen = Imagen(
		name=name,
		color=color,
		description=description,
		categoria=category,
		fecha_registro=fecha_registro,
		path_img=image_path
	)
	sess.add(new_imagen)
	sess.commit()
	return jsonify({'message': 'success', 'code': 200})

@app.route('/api/v1/image/getImageData/<name>', methods=['POST'])
def get_image_data(name):
	image_path = f'./images/{name}.jpg'

	# Find path_img in database
	image = sess.query(Imagen).filter_by(path_img=image_path).first()
	if not image: return jsonify({'message': 'No se encontro la imagen', 'code': 404})

	data_dump = imagen_schema.dump(image)
	return jsonify({'message': 'success', 'code': 200, 'data': data_dump})

@app.route('/api/v1/image/delete/<name>', methods=['POST'])
def delete_image(name):
	image_path = f'./images/{name}.jpg'

	# Find path_img in database
	image = sess.query(Imagen).filter_by(path_img=image_path).first()
	if not image: return jsonify({'message': 'No se encontro la imagen', 'code': 404})

	sess.delete(image)
	sess.commit()

	# Delete image from disk
	os.remove(image_path)

	return jsonify({'message': 'success', 'code': 200})

@app.route('/api/v1/image/update/<int:id>', methods=['POST'])
def update_image(id):

	name = request.json['Name']
	color = request.json['Color']
	description = request.json['Description']
	path_img = request.json['ImagePath']
	fecha_registro = request.json['FechaRegistro']
	category = request.json['Category']

	imagen = sess.query(Imagen).filter_by(idImg=id).first()
	if not imagen: return jsonify({'message': 'No se encontro la imagen', 'code': 404})

	old_image_path = imagen.path_img
	new_image_path = f'./images/{name}.jpg'

	os.rename(old_image_path, new_image_path)


	fecha_registro = datetime.datetime.strptime(fecha_registro, "%d/%m/%Y").strftime("%Y-%m-%d")

	imagen.name = name
	imagen.color = color
	imagen.description = description
	imagen.categoria = category
	imagen.fecha_registro = fecha_registro
	imagen.path_img = new_image_path

	sess.commit()

	data = imagen_schema.dump(imagen)

	return jsonify({'message': 'success', 'code': 200, "data": data})

@app.route('/api/v1/modulo', methods=['POST'])
def register_modulo():
	data = request.json['Data']

	chunks = []
	# split data into chunks of 3 elements
	data = data.split(',')
	for i in range(0, len(data), 3):
		chunks.append(data[i:i+3])

	# clean spaces in first two elements of each chunk and remove the first character of the third element
	try:
		for i in range(len(chunks)):
			chunks[i][0] = chunks[i][0].strip()
			chunks[i][1] = chunks[i][1].strip()
			chunks[i][2] = chunks[i][2][1:]
	except IndexError:
		return jsonify({'message': 'Error en el formato de los datos', 'code': 400})

	# for each chunk save it in database
	for chunk in chunks:
		new_modulo = Cuerpo(
			lado = chunk[0],
			tattoId = chunk[1],
			region = chunk[2]
		)
		sess.add(new_modulo)
		sess.commit()

	return jsonify({'message': 'success', 'code': 200})

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port=8000)