# coding: latin-1
import bottle
#import json
import logging
import datetime
import time
import simplejson as json
from bottle import route, run, error, static_file, request, response
from google.appengine.ext.webapp import util
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api.datastore_types import *

class DictModel(db.Model):
    def to_dict(self):
       return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

class Lugar(DictModel):
    name = db.StringProperty()
    longitude = db.StringProperty()
    latitude = db.StringProperty()
    path = db.StringProperty()

class Tag(DictModel):
    lugar = db.StringProperty()
    tag = db.StringProperty()
    correcto = db.IntegerProperty()
	
class Usuario(DictModel):
    username = db.StringProperty()
    experience = db.IntegerProperty()
    nivel = db.IntegerProperty()
    password = db.StringProperty()
    email = db.StringProperty()

class Pregunta(DictModel):
    lugar = db.ReferenceProperty(Lugar)
    question = db.StringProperty()
    options = db.StringProperty()
    correct = db.StringProperty()
    posX = db.IntegerProperty()
    posY = db.IntegerProperty()
    expPoints = db.IntegerProperty()

class PreguntaXUsuario(DictModel):
    usuario = db.ReferenceProperty(Usuario)
    pregunta = db.ReferenceProperty(Pregunta)
    flag = db.StringProperty()

class ExperienciaXQuest(DictModel):
    pregunta = db.ReferenceProperty(Pregunta)
    nivel = db.IntegerProperty()

class DesafioTag(DictModel):
    lugar = db.StringProperty()
    usuario = db.StringProperty()
    tag = db.StringProperty()
    correcto = db.IntegerProperty()
    incorrecto = db.IntegerProperty()


class PreguntaDTO:
    def __init__(self, idPreguntaXUsuario, question, options, correct, posX, posY, expPoints, flag):
    	self.idPreguntaXUsuario = idPreguntaXUsuario
    	self.question = question
    	self.options = options
    	self.correct = correct
    	self.posX = posX
    	self.posY = posY
    	self.expPoints = expPoints
    	self.flag = flag

class InfoLugar:
	def __init__(self, id, name, latitude, longitude, path):
		self.id = id
		self.name = name
		self.latitude = latitude
		self.longitude = longitude
		self.path = path

def convert_to_builtin_type(obj):
	# Convert objects to a dictionary of their representation
	d = { 'idPreguntaXUsuario':obj.idPreguntaXUsuario, 
		'question':obj.question.encode("latin-1"),
		'options':obj.options,
		'correct':obj.correct,
		'posX':obj.posX,
		'posY':obj.posY,
		'expPoints':obj.expPoints,
		'flag':obj.flag,
		}
	d.update(obj.__dict__)
	return d

@route('/')
@route('/index.html')
def index():
    return "<a href='/hello'>Go to Hello World page</a>"

@route('/pregunta/resolver')
def resolverpregunta():
    username = request.GET.get('username')
    newExp = request.GET.get('newExp')
    idPreguntaXUsuario = request.GET.get('idPreguntaXUsuario')
    qry0 = db.GqlQuery("SELECT * FROM Usuario WHERE username = :1", username)
    usuario = qry0.get()
    usuario.experience = int(newExp)
    usuario.put()
    preguntaXUsuario = PreguntaXUsuario.get_by_id(int(idPreguntaXUsuario))
    preguntaXUsuario.flag = 'C'
    preguntaXUsuario.put()
    return 'correct'

@route('/pregunta/listar')
def listarpreguntas():
    username = request.GET.get('username')
    nombreLugar = request.GET.get('nombreLugar')
    qry0 = db.GqlQuery("SELECT * FROM Usuario WHERE username = :1", username)
    usuario = qry0.get()
    qry1 = db.GqlQuery("SELECT * FROM Lugar WHERE name = :1", nombreLugar)
    lugar = qry1.get()
    quests = []
    for quest in lugar.pregunta_set:
    	quests.append(quest.key())
    result = db.GqlQuery("SELECT * FROM PreguntaXUsuario WHERE usuario = :1 and pregunta in :2", usuario.key(), quests )
    lista = result.fetch(20)
    logging.info(len(lista))
    preguntas = []
    for pregunta in lista:
		preguntas.append(PreguntaDTO(pregunta.key().id(), pregunta.pregunta.question, pregunta.pregunta.options, pregunta.pregunta.correct, pregunta.pregunta.posX, pregunta.pregunta.posY, pregunta.pregunta.expPoints, pregunta.flag))
		logging.info(pregunta.pregunta.question)
    #lugar = Lugar.get_by_id(64001)
    return json.dumps(preguntas, default=convert_to_builtin_type)

@route('/votetag')
def votaruntag():
    logging.info("agregando voto por un tag")
    eltag = request.GET.get('eltag')
    nombrelugar = request.GET.get('nombrelugar')
    valor = request.GET.get('valor')
    logging.info("tome todo del get, ahora consulto")
    qry0 = db.GqlQuery("SELECT * FROM DesafioTag WHERE lugar = :1 AND tag = :2", nombrelugar,eltag)
    desafio = qry0.get()
    logging.info("reviso valor")
    if valor == "yes":
        desafio.correcto+=1
        desafio.put()
    elif valor == "no":
        desafio.incorrecto+=1
        desafio.put()
    return eltag

@route('/addtagchallenge')
def agregardesafiotag():
    logging.info("agregando tag")
    username = request.GET.get('username')
    nombrelugar = request.GET.get('nombrelugar')
    eltag = request.GET.get('eltag')
    logging.info("tome todo del get")
    newTag = DesafioTag(lugar = nombrelugar,usuario = username,tag = eltag, correcto=0, incorrecto=0)
    newTag.put()
    return eltag
	
@route('/addnewplace')
def agregarnuevolugar():
    logging.info("agregando lugar")
    nombrelugar = request.GET.get('nombrelugar')
    lostags = request.GET.get('lostags')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    logging.info("tome todo del get")
    newPlace = Lugar(name= nombrelugar, latitude=latitude, longitude=longitude, path='desert.tmx')
    newPlace.put()
    logging.info("agregue el lugar ^^")
    for word in lostags.split(','):
      logging.info("agregando un tag")
      t = Tag(lugar= nombrelugar,tag=word, correcto = 1)
      t.put()
    logging.info("agrego algunos desafios")
    result = db.GqlQuery("SELECT * FROM Tag WHERE lugar != :1", nombrelugar )
    lista = result.fetch(10)
    logging.info(len(lista))
    for elem in lista:
        logging.info("agregando un desafio")
        dTag = DesafioTag(lugar = nombrelugar,usuario = 'admin',tag = elem.tag, correcto=0, incorrecto=0)
        dTag.put()
    return 'fin'

@route('/addnewtag')
def agregarnuevotag():
    logging.info("agregando nuevo tag")
    nombrelugar = request.GET.get('nombrelugar')
    eltag = request.GET.get('eltag')
    logging.info("tome todo del get")
    newTag = Tag(lugar = nombrelugar, tag = eltag)
    newTag.put()
    logging.info("borrando el desafio")
    list= db.GqlQuery(" SELECT * FROM DesafioTag  WHERE lugar = :1 AND tag = :2",nombrelugar,eltag)
    for entity in list:
        db.delete(entity)
    logging.info("done!")
    return eltag

@route('/getdesafiotag')
def obtenerdesafiotag():
    logging.info("desafio tag")
    username = request.GET.get('username')
    placename = request.GET.get('placename')
    logging.info("consulto para obtener un desafio")
    result = db.GqlQuery("SELECT * FROM DesafioTag WHERE usuario != :1 and lugar = :2", username, placename )
    listaDesafios = result.fetch(20)
    logging.info("tomo los desafios")
    desafiostag = ''
    if len(listaDesafios) > 0:
        logging.info("hay desafios")
        for desaf in listaDesafios:
            logging.info("agrego")
            desafiostag= desafiostag+';'+desaf.lugar+','+desaf.tag
    	return desafiostag[1:]
    return 'none'
    
@route('/getvalidaciontag')
def obtenervalidaciontag():
    logging.info("validacion tag")
    username = request.GET.get('username')
    placename = request.GET.get('placename')
    logging.info("consulto para obtener un desafio")
    result = db.GqlQuery("SELECT * FROM Tag WHERE lugar = :1", placename )
    listaDesafios = result.fetch(20)
    logging.info("tomo los desafios")
    desafiostag = ''
    if len(listaDesafios) > 0:
        logging.info("hay desafios")
        for desaf in listaDesafios:
            logging.info("agrego")
            desafiostag= desafiostag+';'+desaf.lugar+','+desaf.tag+','+str(desaf.correcto)
    	return desafiostag[1:]
    return 'none'

@route('/gettags')
def obtenertags():
    logging.info("obteniendo tags")
    placename = request.GET.get('placename')
    logging.info("consulto para obtener los tags")
    result = db.GqlQuery("SELECT * FROM Tag WHERE lugar = :1 and correcto = 1", placename )
    logging.info("listo")
    listaTags = result.fetch(20)
    if len(listaTags) > 0:
        logging.info("hay tags")
        losTags = ''
        for untag in listaTags:
            logging.info("agrego tag")
            losTags = losTags+','+untag.tag
        logging.info("retorno los tags")
        losTags = losTags[1:]
        return losTags
    return 'no hay tags'

@route('/admintags')
def administrartags():
    logging.info("obteniendo tags")
    logging.info("consulto para obtener los tags")
    result = db.GqlQuery("SELECT * FROM DesafioTag" )
    logging.info("listo")
    listaTags = result.fetch(200)
    if len(listaTags) > 0:
        logging.info("hay tags")
        losTags = ''
        for untag in listaTags:
            logging.info("agrego tag")
            #losTags = losTags+untag.lugar+','+untag.usuario+','+untag.tag+','+untag.correcto+','+untag.incorrecto+';'
            losTags = losTags+untag.lugar+'::'+untag.tag+'::\n SI: '+str(untag.correcto)+' NO: '+str(untag.incorrecto)+';'
        logging.info("retorno los tags")
        return losTags
    return 'no hay tags'

@route('/usuario/register')
def registrar():
    username = request.GET.get('username')
    password = request.GET.get('password')
    email = request.GET.get('email')
    #Procedemos a registrar al nuevo usuario
    newUser = Usuario(username = username, experience = 1, nivel = 1, password = password, email = email)
    newUser.put()
    #Procedemos a agregar los quest disponibles para el usuario
    lista = Pregunta.all()
    for pregunta in lista:
    	obj = PreguntaXUsuario(usuario = newUser, pregunta = pregunta, flag = 'I')
    	obj.put()
    return {'username': newUser.username, 'experience': newUser.experience, 'nivel': newUser.nivel, 'email': newUser.email}
    #return 'username: %s , password: %s ,email: %s' % (username, password, email)

@route('/usuario/login')
def login():
    username = request.GET.get('username')
    password = request.GET.get('password')
    result = db.GqlQuery("SELECT * FROM Usuario WHERE username = :1 and password = :2 LIMIT 1", username, password )
    listaUsuarios = result.fetch(1)
    logging.info(len(listaUsuarios))
    if len(listaUsuarios) > 0:
    	usuario = listaUsuarios[0]
    	logging.info(usuario.key())
    	return {'username': usuario.username, 'experience': usuario.experience, 'nivel': usuario.nivel, 'email': usuario.email}
    	#return 'username: %s , password: %s ,email: %s' % (usuario.username, usuario.password, usuario.email)
    return {'username': 'null', 'experience': 0, 'nivel': 1, 'email': 'null'}
    #return 'username: %s , password: %s ,email: %s' % ('null', 'null', 'null')
    #if usuario is None:
    	#return 'username: %s , password: %s ,email: %s' % ('null', 'null', 'null')
    #return 'username: %s , password: %s ,email: %s' % (usuario.username, usuario.password, usuario.email)

@route('/hello')
def hello():
	#Insertando los lugares
    o3 = Lugar(name='Catedral Metropolitana de Santiago', latitude='-33.437658', longitude='-70.651806', path='desert.tmx')
    o3.put()
    o4 = Lugar(name='Cerro Santa Lucia', latitude='-33.440000', longitude='-70.644000', path='desert.tmx')
    o4.put()
    o5 = Lugar(name='Museo Historico Nacional', latitude='-33.437000', longitude='-70.650611', path='desert.tmx')
    o5.put()
    o6 = Lugar(name='Plaza de Armas de Santiago', latitude='-33.437967', longitude='-70.650400', path='desert.tmx')
    o6.put()
    logging.info('Termina de insertar los lugares')
    logging.info('Insertando Tags')
    t1 = Tag(lugar='Cerro Santa Lucia',tag='cerro')
    t1.put()
    t2 = Tag(lugar='Cerro Santa Lucia',tag='patrimonio')
    t2.put()
    t3 = Tag(lugar='Cerro Santa Lucia',tag='cultural')
    t3.put()
    t4 = Tag(lugar='Plaza de Armas de Santiago',tag='plaza')
    t4.put()
    t8 = Tag(lugar='Plaza de Armas de Santiago',tag='patromonio')
    t8.put()
    t5 = Tag(lugar='Museo Historico Nacional',tag='museo')
    t5.put()
    t6 = Tag(lugar='Catedral Metropolitana de Santiago',tag='iglesia')
    t6.put()
    logging.info('Fin agregar tags')
    
    o7 = DesafioTag(lugar='Cerro Santa Lucia',usuario='admin',tag='estatuas', correcto=0, incorrecto=0)
    logging.info('insertando desafios')
    o7.put()
    #logging.info(o3.key())
    #insertando las preguntas de cada lugar
    p1 = Pregunta(lugar = o3, question = u'¿Quién fue el arquitecto que dirigió su construcción?', options = u'Diego Portales-Manuel Montt-Antonio Acuña-Manuel Rodriguez', correct = u'Antonio Acuña', posX = 30, posY = 50, expPoints = 2)
    p2 = Pregunta(lugar = o3, question = u'¿De quiénes son los restos encontrados en la renovación del año 2005?', options = u'Diego Portales-Manuel Rodriguez-José Miguel Carrera-Inés de Suarez', correct = 'Diego Portales', posX = 90, posY = 50, expPoints = 2)
    p3 = Pregunta(lugar = o3, question = u'¿En que año se comenzó a construir?', options = '1555-1556-1557-1558', correct = '1556', posX = 90, posY = 100, expPoints = 2)
    p4 = Pregunta(lugar = o3, question = u'¿Alrededor de qué año se terminó de construir?', options = '1590-1595-1600-1605', correct = '1600', posX = 150, posY = 50, expPoints = 2)
    logging.info('Termina de crear las preguntas')
    p1.put()
    logging.info('Inserta primera pregunta')
    p2.put()
    logging.info('Inserta segunda pregunta')
    p3.put()
    logging.info('Inserta tercera pregunta')
    p4.put()
    logging.info('Inserta cuarta pregunta')
    return '<b>Hello Won!</b>'

@route('/hellodesafios')
def hellodesafios():
	#Insertando desafios
    logging.info('insertando tags')
    t1 = Tag(lugar='Cerro Santa Lucia',tag='cerro')
    t1.put()
    
    
    logging.info('desafios insertados')
    return '<b>Wuii!</b>'
    
@route('/hellopruebatags')
def hellopruebatags():
	#Insertando desafios
    logging.info('insertando tags')
    t1 = Tag(lugar='mi pieza',tag='algo', correcto=0)
    t1.put()
    logging.info('tags insertados')
    qry0 = db.GqlQuery("SELECT * FROM Tag")
    for untag in qry0:
        untag.correcto = 1
        untag.put()
    return '<b>Wuii!</b>'

@route('/helloservicios')
def helloservicios():
	#Insertando desafios
    logging.info('insertando desafios')
    o1 = Lugar(name='Club Hipico', latitude='-33.458656', longitude='-70.667624', path='desert.tmx')
    o1.put()
    logging.info('Termina de insertar los lugares')
    logging.info('Insertando Tags')
    t1 = Tag(lugar='Club Hipico',tag='carreras')
    t1.put()
    a1 = Tag(lugar='Club Hipico',tag='nivel2')
    a1.put()
    o7 = DesafioTag(lugar='Club Hipico',usuario='admin',tag='caballos', correcto=0, incorrecto=0)
    o7.put()

    o2 = Lugar(name='Servipag', latitude='-33.459041', longitude='-70.663322', path='desert.tmx')
    o2.put()
    logging.info('Termina de insertar los lugares')
    logging.info('Insertando Tags')
    t2 = Tag(lugar='Servipag',tag='cuentas')
    t2.put()
    t3 = Tag(lugar='Servipag',tag='servicio')
    t3.put()
    o8 = DesafioTag(lugar='Servipag',usuario='admin',tag='luz', correcto=0, incorrecto=0)
    o8.put()

    o3 = Lugar(name='Santa Isabel', latitude='-33.452874', longitude='-70.664181', path='desert.tmx')
    o3.put()
    logging.info('Termina de insertar los lugares')
    logging.info('Insertando Tags')
    t4 = Tag(lugar='Santa Isabel',tag='cajero')
    t4.put()
    t5 = Tag(lugar='Santa Isabel',tag='servicio')
    t5.put()
    o9 = DesafioTag(lugar='Santa Isabel',usuario='admin',tag='supermercado', correcto=0, incorrecto=0)
    o9.put()


    
    logging.info('desafios insertados')
    return '<b>Wuii!</b>'
	
@route('/json')
def getJson():
    #o1 = InfoLugar(1, 'Desert1', '-33.370087', '-70.738875', 'desert.tmx')
    #o2 = InfoLugar(2, 'Desert2', '-33.369719', '-70.740495', 'mapa3.tmx')
    #lista = []
    lista = Lugar.all()
    #lista = {}
    #lista[str(o1.id)] = o1
    #lista[str(o2.id)] = o1
    #lista.append(o1)
    #lista.append(o2)
    #print 'mapa1'
    #print 'mapa2'
    #for lugar in lista:
	#	print lugar.name
    respuesta = json.dumps([p.to_dict() for p in lista])
    logging.info(respuesta)
    return respuesta
    #return json.dumps(lista, default=convert_to_builtin_type)
    #return {'name':o1.name, 'path':o1.path}
    #return {'name':'nombre', 'path':'path'}
	
@route('/object/:id#[0-9]+#')
def view_object(id):
    return "Object ID: %d" % int(id)

@route('/static/:filename')
def server_static(filename):
	return static_file(filename, root='./')
	
@error(404)
def error404(error):
    return 'Nothing here, sorry'

util.run_wsgi_app(bottle.default_app())

# run(host='localhost', port=8080)
