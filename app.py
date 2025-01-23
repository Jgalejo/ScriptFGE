from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from collections import defaultdict

app = Flask(__name__)

@app.route('/consulta', methods=['POST'])
def consulta():
    # Extraer el número de identificación del cuerpo de la solicitud
    data = request.json
    if not data or 'numero_id' not in data:
        return jsonify({'error': 'Falta el parámetro numero_id'}), 400
    
    numero_id = data['numero_id']

    # Configura el controlador del navegador
    driver = webdriver.Chrome()  # Cambia a tu controlador correspondiente
    driver.maximize_window()
    driver.get("https://www.fiscalia.gob.ec/consulta-de-noticias-del-delito/")  # Reemplaza con la URL correcta

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "blockrandom")))
        iframe = driver.find_element(By.ID, "blockrandom")
        driver.switch_to.frame(iframe)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "pwd")))
        caja_texto = driver.find_element(By.NAME, "pwd")
        caja_texto.send_keys(numero_id)
        boton_buscar = driver.find_element(By.ID, "btn_buscar_denuncia")
        boton_buscar.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/div[2]/div/table[1]/tbody")))
        
        tabla = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div")
        filas = tabla.find_elements(By.TAG_NAME, "tr")

        datos_tabla = []

        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            datos_fila = [celda.text.strip() if celda.text.strip() else 'null' for celda in celdas]
            if datos_fila:
                datos_tabla.append(datos_fila)

        def procesar_datos(datos_tabla):
            resultado = []
            registros_actuales = []
            datos_dict = {}
            procesando_tabla = False

            for item in datos_tabla:
                if item[0] == "LUGAR":
                    if datos_dict:
                        resultado.append({"tabla": datos_dict, "registros": registros_actuales})
                    datos_dict = {}
                    registros_actuales = []
                    procesando_tabla = True

                if procesando_tabla:
                    if "UNIDAD" in item[0]:
                        datos_dict[item[0]] = item[1]
                        if len(item) > 3:
                            datos_dict[item[2]] = item[3]
                        procesando_tabla = False
                    else:
                        if len(item) > 1:
                            datos_dict[item[0]] = item[1]
                        if len(item) > 3:
                            datos_dict[item[2]] = item[3]
                else:
                    if item[0] not in ["CEDULA", "NOMBRES COMPLETOS", "ESTADO"]:
                        registros_actuales.append(item)

            if datos_dict:
                resultado.append({"tabla": datos_dict, "registros": registros_actuales})

            return resultado

        datos_procesados = procesar_datos(datos_tabla)

        # Devuelve los datos como JSON
        return jsonify(datos_procesados)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)
