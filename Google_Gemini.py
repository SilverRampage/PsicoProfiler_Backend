from flask import Flask, request, jsonify
import google.generativeai as genai
import pymysql

app = Flask(__name__)

# Configura tu API Key
API_KEY = 'AIzaSyCB8nAf2wGjHu9h9WdaY8a7h1fVB6BaBOU'  # Reemplaza con tu API Key
genai.configure(api_key=API_KEY)

# Configuración del modelo Gemini 1.5 Flash
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='psycobase',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/registro', methods=['POST'])
def registrar_usuario():
    try:
        data = request.json
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuarios (nombre, apellido, email, password, fechaNacimiento, genero, ubicacion, padecimiento) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (data['nombre'], data['apellido'], data['email'], data['password'], data['fechaNacimiento'], data['genero'], data['ubicacion'], data['padecimiento'])
            )
            connection.commit()
        return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def iniciar_sesion():
    try:
        data = request.json
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Cambia la consulta para seleccionar todos los campos del usuario
            cursor.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s", (data['email'], data['contrasena']))
            user = cursor.fetchone()
            if user:
                # Convierte el resultado a un diccionario, asumiendo que `user` es una tupla
                
                return jsonify({"mensaje": "Inicio de sesión exitoso", "usuario": user}), 200
            else:
                return jsonify({"error": "Credenciales incorrectas"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para obtener soluciones basadas en el ID del usuario y su padecimiento
@app.route('/soluciones', methods=['POST'])
def obtener_soluciones():
    try:
        data = request.json
        user_id = data['Id']

        # Conectar a la base de datos para obtener la información del usuario
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT padecimiento FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            padecimiento = user['padecimiento']

        # Crear el prompt personalizado para el API de generación de texto
        prompt = (
            f"Eres un asistente psicológico especializado en ayudar a personas en crisis. "
            f"Proporciona técnicas efectivas y probadas para manejar {padecimiento}, asegurándote de que sean "
            f"estrategias prácticas y fácilmente implementables para alguien que está experimentando una crisis. solo 5 soluciones"
            f"Evita sugerir artículos o recursos generales; en su lugar, enfócate en pasos de acción claros."
        )

        # Conectar con el API para generar soluciones
        chat_session = genai.GenerativeModel(
            model_name="gemini-1.5-flash"  # Ajusta según el modelo que estés utilizando
        ).start_chat(history=[])
        response = chat_session.send_message(prompt)

        # Simular obtención de soluciones basadas en el prompt
        soluciones = response.text.strip().split("\n")[:5]

        return jsonify({"soluciones": soluciones}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    

@app.route('/gettop3soluciones', methods=['POST'])
def gettop3soluciones():
    try:
        data = request.json
        user_id = data['Id']

        # Conectar a la base de datos para obtener la información del usuario
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT padecimiento FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            padecimiento = user['padecimiento']

        # Crear el prompt personalizado para el API de generación de texto
        prompt = (
            f"Proporcioname una tecnica mas, efectiva y probadas para manejar {padecimiento}, asegurándote de que sean "
            f"estrategias prácticas y fácilmente implementables para alguien que está experimentando una crisis. solo 1 solucion"
            f"Evita sugerir artículos o recursos generales; en su lugar, enfócate en pasos de acción claros."
        )

        # Conectar con el API para generar soluciones
        chat_session = genai.GenerativeModel(
            model_name="gemini-1.5-flash"  # Ajusta según el modelo que estés utilizando
        ).start_chat(history=[])
        response = chat_session.send_message(prompt)

        # Simular obtención de soluciones basadas en el prompt
        soluciones = response.text.strip().split("\n")[:5]

        return jsonify({"soluciones": soluciones}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/retroalimentacion', methods=['POST'])
def recibir_retroalimentacion():
    try:
        user_id = request.json.get('userId')
        solucion_id = request.json.get('solucionId')
        funciono = request.json.get('funciono')
        comentario = request.json.get('comentario')

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO retroalimentacion (user_id, solucion_id, funciono, comentario, fecha, hora) VALUES (%s, %s, %s, %s, CURDATE(), CURTIME())",
                (user_id, solucion_id, funciono, comentario)
            )
            connection.commit()

        return jsonify({"mensaje": "Retroalimentación recibida"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/emergencia', methods=['POST'])
def manejar_emergencia():
    try:
        user_id = request.json.get('userId')
        tipo_emergencia = request.json.get('tipoEmergencia')
        latitud = request.json.get('latitud')
        longitud = request.json.get('longitud')
        ubicacion = request.json.get('ubicacion')  # Puede ser una descripción de la ubicación, como "Calle X, Ciudad Y"

        # Verificar que se haya enviado la latitud y longitud
        if not latitud or not longitud:
            return jsonify({"error": "Latitud y longitud son requeridas para la emergencia."}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO emergencias (user_id, tipo_emergencia, fecha, hora, ubicacion, latitud, longitud) VALUES (%s, %s, CURDATE(), CURTIME(), %s, %s, %s)",
                (user_id, tipo_emergencia, ubicacion, latitud, longitud)
            )
            connection.commit()

        return jsonify({"mensaje": "Emergencia reportada. Se ha enviado la ubicación."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
