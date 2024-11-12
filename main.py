import customtkinter as ctk
from customtkinter import filedialog
from tkinter import messagebox, Toplevel, simpledialog
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import datetime
import random
import os
import webbrowser
import PyPDF2
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import BBCodeFormatter
import threading
import time
import pyperclip

global root, sidebar_frame, main_frame, chat_area, code_area, input_field, typing_label, api_key
global notebook, copy_button, ax, canvas
root = None
# Configuración inicial
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Variables globales
chat = []
current_history_file = f"history_{datetime.datetime.now().strftime('%d-%m-%Y')}.txt"
model = None
text = ""
tags = set()
current_tags = set()


def toggle_dark_mode():
    current_mode = ctk.get_appearance_mode().lower()
    new_mode = "light" if current_mode == "dark" else "dark"
    ctk.set_appearance_mode(new_mode)
    update_ui_colors()


def update_ui_colors():
    is_dark = ctk.get_appearance_mode().lower() == "dark"
    bg_color = "#2b2b2b" if is_dark else "#f0f0f0"
    fg_color = "#ffffff" if is_dark else "#000000"

    root.configure(fg_color=bg_color)
    sidebar_frame.configure(fg_color=bg_color)
    main_frame.configure(fg_color=bg_color)
    chat_area.configure(fg_color=bg_color, text_color=fg_color)
    code_area.configure(fg_color=bg_color, text_color=fg_color)
    input_field.configure(fg_color=bg_color, text_color=fg_color)


def show_typing_animation():
    typing_label.configure(text="GenAI está escribiendo")
    for _ in range(3):
        for dots in range(1, 4):
            typing_label.configure(text="GenAI está escribiendo" + "." * dots)
            time.sleep(0.5)
    typing_label.configure(text="")


def send_message_with_animation():
    threading.Thread(target=show_typing_animation, daemon=True).start()
    send_message()


# Actualizar la función update_code_display para asegurarse de que el botón de copiar esté visible
def update_code_display(code):
    code_area.configure(state="normal")
    code_area.delete("1.0", ctk.END)
    code_area.insert(ctk.END, code)
    code_area.configure(state="disabled")
    notebook.set("Código")  # Cambiar a la pestaña de código
    copy_button.lift()  # Asegurarse de que el botón esté visible

    # Detect the language (you can expand this list)
    language = "python"  # default
    if code.strip().startswith("<?php"):
        language = "php"
    elif code.strip().startswith("<"):
        language = "html"
    elif "function" in code or "var" in code or "let" in code or "const" in code:
        language = "javascript"

    # Highlight the code
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = BBCodeFormatter(style="monokai")
    highlighted_code = highlight(code, lexer, formatter)

    # Insert the highlighted code
    for line in highlighted_code.split("\n"):
        if line.startswith("[color="):
            color = line[7 : line.index("]")]
            text = line[line.index("]") + 1 : line.rindex("[")]
            code_area.insert(ctk.END, text, color)
        else:
            code_area.insert(ctk.END, line)
        code_area.insert(ctk.END, "\n")

    code_area.configure(state="disabled")
    notebook.set("Código")  # Switch to the code tab


def update_chat_display():
    chat_area.configure(state="normal")
    chat_area.delete("1.0", ctk.END)
    for message in chat:
        if message.startswith("Tú: "):
            chat_area.insert(ctk.END, message, "user")
        elif message.startswith("GenAI: "):
            chat_area.insert(ctk.END, message, "ai")
        else:
            chat_area.insert(ctk.END, message)
    chat_area.configure(state="disabled")
    chat_area.see(ctk.END)


def pdf_to_text():
    global text
    pdf_path = ctk.filedialog.askopenfilename(filetypes=[("Archivos pdf", "*.pdf")])
    if pdf_path:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text


def load_api_key():
    """Carga la clave de API desde un archivo."""
    if os.path.exists("api.txt"):
        with open("api.txt", "r") as file:
            return file.read().strip()
    return ""


def save_api_key(api_key):
    """Guarda la clave de API en un archivo."""
    with open("api.txt", "w") as file:
        file.write(api_key)


def configure_generative_ai(api_key):
    """Configura el modelo de IA generativa con la clave de API proporcionada."""
    global model
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except GoogleAPIError as e:
        messagebox.showerror("Error de API", f"No se pudo configurar la API: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {str(e)}")


def prompt_for_api_key():
    dialog = ctk.CTk()
    dialog.title("Ingresar Clave de API de Google")
    dialog.geometry("400x200")
    dialog.resizable(False, False)

    label = ctk.CTkLabel(dialog, text="Ingresa la clave de la API:")
    label.pack(pady=10)

    api_entry = ctk.CTkEntry(dialog, width=300)
    api_entry.pack(pady=10)

    def save_and_configure():
        api_key = api_entry.get().strip()
        if api_key:
            save_api_key(api_key)
            configure_generative_ai(api_key)
            dialog.destroy()
            main()
        else:
            messagebox.showerror("Error", "La clave de la API no puede estar vacía.")

    save_button = ctk.CTkButton(
        dialog,
        text="Guardar y continuar",
        command=save_and_configure,
        bg_color="#064F36",
    )
    save_button.pack(pady=10)

    get_key_button = ctk.CTkButton(
        dialog,
        text="Obtener clave",
        command=lambda: webbrowser.open(
            "https://ai.google.dev/gemini-api/docs/api-key?hl=es-419"
        ),
    )
    get_key_button.pack(pady=10)

    dialog.grab_set()  # Hacer que la ventana de entrada de clave de API sea modal


def apply_chat_styles():
    chat_area.tag_config("user", background="#36a8b4", foreground="black")
    chat_area.tag_config("ai", background="#cab93f", foreground="black")


def load_chat_history(file_path):
    global current_history_file, chat
    current_history_file = file_path
    chat_area.configure(state="normal")
    chat_area.delete("1.0", ctk.END)
    try:
        with open(file_path, "r") as file:
            chat = file.readlines()
            for line in chat:
                if line.startswith("Tú: "):
                    chat_area.insert(ctk.END, line, "user")
                elif line.startswith("GenAI: "):
                    chat_area.insert(ctk.END, line, "ai")
                else:
                    chat_area.insert(ctk.END, line)
    except FileNotFoundError:
        messagebox.showerror("Error", f"No se encontró el archivo: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    chat_area.see(ctk.END)
    chat_area.configure(state="disabled")
    apply_chat_styles()


def new_chat():
    global current_history_file, chat
    current_history_file = f"history_{datetime.datetime.now().strftime('%d-%m-%Y')}_{random.randint(1, 100)}.txt"
    chat = []
    chat_area.configure(state="normal")
    chat_area.delete("1.0", ctk.END)
    chat_area.configure(state="disabled")


def save_custom_prompt(prompt):
    if prompt:
        with open("prompt.txt", "w") as file:
            file.write(prompt)
        messagebox.showinfo("Éxito", "Prompt personalizado guardado correctamente.")
    else:
        messagebox.showerror("Error", "El prompt no puede estar vacío.")


def load_custom_prompt():
    try:
        with open("prompt.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""


def prompt_for_custom_prompt():
    dialog_promt = Toplevel()
    dialog_promt.title("Prompt Personalizado")
    dialog_promt.configure(background="#2b2b2b")
    dialog_promt.geometry("500x300")
    dialog_promt.resizable(False, False)

    label = ctk.CTkLabel(
        dialog_promt,
        text="Ingresa el prompt personalizado:",
        text_color="#ffffff",
        fg_color="transparent",
        bg_color="transparent",
    )
    label.pack(pady=10, padx=10)

    custom_prompt_entry = ctk.CTkTextbox(
        dialog_promt,
        height=150,
        fg_color="#3a3a3a",
        text_color="#ffffff",
        border_color="#555555",
        border_width=1,
    )
    custom_prompt_entry.pack(pady=10, padx=10, fill="both", expand=True)
    custom_prompt_entry.insert("0.0", load_custom_prompt())

    def save_and_close():
        prompt = custom_prompt_entry.get("0.0", "end-1c").strip()
        save_custom_prompt(prompt)
        dialog_promt.destroy()

    save_button = ctk.CTkButton(
        dialog_promt,
        text="Guardar Prompt",
        command=save_and_close,
        fg_color="#064F36",
        hover_color="#0D845B",
    )
    save_button.pack(pady=10)

    dialog_promt.mainloop()


def correccion(code):
    prompt_template = f"""
    Sigue estas instrucciones cuidadosamente:
    1. no modifiques el codigo mas de lo necesarios
    2.no uses if **name** == "__main__":
    3. manten el codigo lo mas igual posible, solo cambia lo justo para que compile
    4.acomoda LA IDENTACION y la syntaxis
    5.borra el nombre del lenguaje, no uses ```, y tampoco ninguna explicacion
    6.no uses markdown

    por ejemplo, en este codigo: 
    ```php
    <?php
    function suma($a, $b) 
    
    ?>
    ```
    deberias borrar ```php y ``` ademas de las llaves de apertura y cierre
    el codigo a modificar es el siguiente: 
    7.Solo usa caracteres que esten en UTF-8
    8.No uses tildes, ni caracteres que puedan causar errores con la codificacion de UTF-8
    """
    full_prompt = prompt_template + code
    return model.generate_content(full_prompt).text


def execute_code():
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    def name(response):
        prompt = f"""
        quiero que generes un titulo conciso y claro y resumido y corto 
        5.no digas ni escribas nada mas que el titulo, sin ningun espacio antes o despues, ni comillas, con un maximo de 3 palabras
        6.la respuesta que me des solo puede tener el titulo, no quiero ninguna explicacion
        7.solo elije tu que titulo va a ser, no me des posibilidades
        8.no quiero que me digas nada mas que el titulo, ninguna introduccion ni nada
        9.dame un solo titulo
        10.antecede el primer titutlo con "TITULO:" y aue termine con "TITULO_END:"
        11.que el nombre tenga la extension que corresponda al lenguaje de programacion que escribiste
        por ejemplo si es python que sea py, si es javascript que sea js etc
        para ponerle como nombre un archivo con este codigo: 
        """
        full_prompt = prompt + response
        return model.generate_content(full_prompt).text

    code = code_area.get("1.0", ctk.END).strip()
    if code:
        response = correccion(code)

        try:
            nom = name(response)
            nombre = nom.split("TITULO:")[1].split("TITULO_END:")[0].strip()
            nombre = (
                nombre.replace(" ", "_")
                .replace("TITULO:", "")
                .replace("TITULO_END:", "")
            )

            # Agregar extensión según el lenguaje detectado
            if "python" in code.lower() or ".py" in nombre.lower():
                nombre += ".py"
            elif "javascript" in code.lower() or ".js" in nombre.lower():
                nombre += ".js"
            elif "php" in code.lower() or ".php" in nombre.lower():
                nombre += ".php"
            elif "java" in code.lower() or ".java" in nombre.lower():
                nombre += ".java"
            elif "c" in code.lower() and not "cpp" in code.lower():
                nombre += ".c"
            elif "cpp" in code.lower() or "c++" in code.lower():
                nombre += ".cpp"
            elif "cs" in code.lower() or ".cs" in nombre.lower():
                nombre += ".cs"
            else:
                print(
                    "No se detectó un lenguaje compatible o el nombre no contiene una extensión válida."
                )
                return

            with open(f"{nombre}", "a") as file:
                file.write(response)
            print(f"Archivo '{nombre}' creado con éxito.")
        except IndexError:
            print("No se pudo encontrar el nombre del archivo en el código corregido.")
        except Exception as e:
            print(f"Error al crear el archivo: {e}")
    else:
        print("No se ha proporcionado ningún código.")

    # Ejecución según la extensión
    if nombre.endswith(".py"):
        os.system("python3 " + nombre)
    elif nombre.endswith(".js"):
        os.system("node " + nombre)
    elif nombre.endswith(".php"):
        os.system("php " + nombre)
    elif nombre.endswith(".java"):
        os.system("javac " + nombre + " && java " + nombre.split(".")[0])
    elif nombre.endswith(".c"):
        os.system("gcc " + nombre + " -o " + nombre.split(".")[0])
        os.system("./" + nombre.split(".")[0])
    elif nombre.endswith(".cpp"):
        os.system("g++ " + nombre + " -o " + nombre.split(".")[0])
        os.system("./" + nombre.split(".")[0])
    elif nombre.endswith(".cs"):
        os.system("dotnet run " + nombre)
    else:
        print("El lenguaje no es compatible con el sistema operativo.")


def copy_code_to_clipboard():
    codigo = code_area.get("1.0", ctk.END).strip()
    code = correccion(codigo)
    if code:
        pyperclip.copy(code)
        messagebox.showinfo("Copiado", "El código ha sido copiado al portapapeles.")
    else:
        messagebox.showwarning("Vacío", "No hay código para copiar.")


def update_code_display(code):
    code_area.configure(state="normal")
    code_area.delete("1.0", ctk.END)
    code_area.insert(ctk.END, code)
    code_area.configure(state="disabled")
    notebook.set("Código")  # Cambiar a la pestaña de código


def update_graph_display(x, y):
    ax.clear()
    ax.plot(x, y)
    canvas.draw()
    notebook.set("Gráfico")  # Cambiar a la pestaña de gráfico


def open_help_window():
    help_window = ctk.CTkToplevel(root)
    help_window.title("Ayuda")
    help_window.geometry("500x400")

    help_text = """
    Comandos Disponibles:

    /clear   - Limpiar el área de código.
    /code    - Mostrar el código actual.
    /graph   - Mostrar un gráfico simple.
    /save    - Guardar el historial del chat.
    /load    - Cargar el historial del chat.
    /copy    - Copiar el código al portapapeles.
    /run     - Ejecutar el código.
    /help    - Mostrar esta ventana de ayuda.
    /about   - Mostrar información sobre la aplicación.
    /exit    - Cerrar la aplicación.
    /theme   - Cambiar el tema de la aplicación (claro/oscuro).
    /font    - Cambiar el tamaño de la fuente.
    /export  - Exportar el chat a un archivo de texto.
    """

    help_textbox = ctk.CTkTextbox(help_window, width=480, height=320)
    help_textbox.insert("1.0", help_text)
    help_textbox.configure(state="disabled")
    help_textbox.pack(padx=10, pady=10)

    close_button = ctk.CTkButton(
        help_window, text="Cerrar", command=help_window.destroy
    )
    close_button.pack(pady=10)

    help_window.grab_set()  # Hacer que la ventana de ayuda sea modal


def open_about_window():
    about_window = ctk.CTkToplevel(root)
    about_window.title("Acerca de")
    about_window.geometry("400x350")

    about_text = """
    Aplicación de Chat
    Versión 1.1

    Desarrollado por Markbusking

    Esta aplicación es un asistente de programación
    y análisis de datos con inteligencia artificial.

    Para más información y actualizaciones, visita:
    https://github.com/markbus-ai/Gemini-desktop
    """

    about_textbox = ctk.CTkTextbox(about_window, width=380, height=220)
    about_textbox.insert("1.0", about_text)
    about_textbox.configure(state="disabled")
    about_textbox.pack(padx=10, pady=10)

    def open_github():
        webbrowser.open("https://github.com/markbus-ai/Gemini-desktop")

    github_button = ctk.CTkButton(
        about_window, text="Visitar GitHub", command=open_github
    )
    github_button.pack(pady=5)

    close_button = ctk.CTkButton(
        about_window, text="Cerrar", command=about_window.destroy
    )
    close_button.pack(pady=5)

    about_window.grab_set()  # Hacer que la ventana "Acerca de" sea modal
# Variable de control para detener la animación
stop_animation = False
animation_complete = False  # Para verificar si la animación ha terminado

def send_message(send_button=None):
    global stop_animation
    stop_animation = True
    message = input_field.get().strip()
    if not message:
        messagebox.showerror("Error", "No puedes enviar un mensaje vacío.")
        send_button.configure(text="Enviar")  # Restablecer el botón si no hay mensaje
        return

    if message.startswith("/"):
        command = message.lower().split()[0]
        if command == "/clear":
            clear_code_area()
        elif command == "/code":
            show_current_code()
        elif command == "/graph":
            show_graph()
        elif command == "/save":
            save_chat_history()
        elif command == "/load":
            load_chat_history()
        elif command == "/copy":
            copy_code_to_clipboard()
        elif command == "/run":
            execute_code()
        elif command == "/help":
            open_help_window()
        elif command == "/about":
            open_about_window()
        elif command == "/exit":
            exit_application()
        elif command == "/theme":
            toggle_theme()
        elif command == "/font":
            change_font_size()
        elif command == "/export":
            export_chat()
        else:
            messagebox.showwarning(
                "Comando desconocido", f"El comando '{command}' no es reconocido."
            )
        return

    append_to_chat(f"Tú: {message}", "user")
    input_field.delete(0, ctk.END)

    # Mostrar mensaje de "Generando..."
    append_to_chat("GenAI: Generando...", "ai")
    chat_area.see(ctk.END)

    try:
        chat_context = " ".join(chat)
        custom_prompt = load_custom_prompt()
        prompt_template = f"""
Eres un asistente AI especializado en programación y análisis de datos. Responde en español de manera concisa, precisa y profesional. Sigue estas instrucciones cuidadosamente:

1. Contexto: Utiliza el siguiente contexto del chat solo si es relevante: {chat_context}

2. Formato de respuesta:
   - No uses markdown en tus respuestas.
   - Si generas código, enciérralo entre triple backticks (```).
   - Para gráficos, sigue el formato especificado en el punto 4.

3. Generación de código:
   - Proporciona código limpio, eficiente y siguiendo buenas prácticas.
   - Incluye comentarios breves para explicar partes complejas.

4. Generación de gráficos:
   - Si se solicita un gráfico, genera datos de ejemplo apropiados.
   - Formato: "GRAPH_DATA: x1,y1 x2,y2 x3,y3 ..." (sin comillas)
   - Proporciona entre 5 y 20 pares de puntos.
   - Asegúrate de que los datos sean coherentes y representen una tendencia lógica.
   - cada vez que te pasen palabras para generar el grafico remplaza las palabras por numeros SIEMPRE
   - Ejemplo: GRAPH_DATA: 0,10 1,15 2,25 3,30 4,50
   - Ejemplo si te piden que generes un graficos por meses, remplaza los meses por numeros segun su orden en el calendario

5. Respuestas generales:
   - Sé directo y evita introducciones innecesarias.
   - Si una pregunta no tiene sentido o es ambigua, pide aclaraciones.
   - Ofrece explicaciones adicionales solo si se solicitan.

6. Conocimiento específico:
   - Basa tus respuestas en el contenido de este PDF cuando sea relevante: {text}
   - Si el PDF no contiene información relevante, utiliza tu conocimiento general.

7. Prompt personalizado: {custom_prompt}
   - Incorpora estas instrucciones específicas en tu respuesta cuando sea apropiado.

Responde al siguiente mensaje teniendo en cuenta todas estas instrucciones:
"""

        full_prompt = prompt_template + message
        response = model.generate_content(full_prompt).text

        # Reemplazar el mensaje de "Generando..." con la respuesta real
        chat_area.configure(state="normal")
        chat_area.delete("end-1c", ctk.END)  # Eliminar el mensaje de "Generando..."
        
        # Mostrar el mensaje de la IA de forma gradual
        display_message_gradually(response, "GenAI", send_button)

        # Detectar y manejar código
        if "```" in response:
            code_start = response.find("```") + 3
            code_end = response.find("```", code_start)
            if code_end != -1:
                code = response[code_start:code_end].strip()
                update_code_display(code)

        # Detectar y manejar datos para gráficos
        if "GRAPH_DATA:" in response:
            data_start = response.find("GRAPH_DATA:") + 11
            data_end = response.find("\n", data_start)
            if data_end != -1:
                data_str = response[data_start:data_end].strip()
                try:
                    x, y = zip(
                        *[map(float, point.split(",")) for point in data_str.split()]
                    )
                    update_graph_display(x, y)
                except:
                    print("Error al procesar datos del gráfico")

    except GoogleAPIError as e:
        append_to_chat(f"Error de API: {str(e)}", "ai")
    except Exception as e:
        append_to_chat(f"Error: {str(e)}", "ai")
    if stop_animation == True:
        send_button.configure(text="Enviar", command=lambda:send_message)
        print("boton dice enviar")





def display_message_gradually(message, sender, send_button=None):
    send_button.configure(text="Detener", command=lambda:stop_animation_now(send_button))
    print("boton dice detener")
    """Muestra un mensaje de forma gradual en el área de chat y permite detenerla con un botón."""
    global stop_animation, animation_complete
    stop_animation = False
    animation_complete = False

    # Inserta el nombre del remitente
    chat_area.configure(state="normal")
    chat_area.insert(ctk.END, f"{sender}: ", "user" if sender == "Tú" else "ai")
    chat_area.see(ctk.END)

    # Función para escribir cada carácter de forma gradual
    def type_character(index=0, send_button = None):
        global animation_complete
        if stop_animation or index >= len(message):
            # Si se detiene la animación o se termina el mensaje, muestra el mensaje completo y detén la animación
            if not animation_complete:
                if send_button:
                    send_button.configure(text="Enviar", command=lambda:send_message)
                chat_area.insert(ctk.END, message[index:], "ai")
                chat_area.insert(ctk.END, "\n")
                chat_area.configure(state="disabled")
                animation_complete = True  # Marca que la animación está completa
                print("boton dice enviar")
                root.update_idletasks()
                
                
            return

        # Continúa con la animación de escritura
        chat_area.insert(ctk.END, message[index], "ai")
        chat_area.see(ctk.END)
        root.update_idletasks()  # Actualiza la interfaz después de cada carácter
        root.after(50, type_character, index + 1)
    # Inicia la animación de escritura
    type_character(send_button=send_button)
    


# Función para detener la animación al instante
def stop_animation_now(send_button=None):
    global stop_animation
    stop_animation = True  # Activa la bandera para detener la animación
    send_button.configure(text="Enviar", command=lambda:send_message)
    print("boton dice enviar")

def clear_code_area():
    code_area.configure(state="normal")
    code_area.delete("1.0", ctk.END)
    code_area.configure(state="disabled")
    messagebox.showinfo("Limpieza", "El área de código ha sido limpiada.")


def show_current_code():
    code = code_area.get("1.0", ctk.END).strip()
    if code:
        update_code_display(code)
    else:
        messagebox.showinfo("Código", "No hay código para mostrar.")


def show_graph():
    x = [1, 2, 3, 4, 5]
    y = [1, 4, 9, 16, 25]
    update_graph_display(x, y)
    messagebox.showinfo("Gráfico", "Se ha generado un gráfico de ejemplo.")


def save_chat_history():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")]
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            chat_content = chat_area.get("1.0", ctk.END)
            file.write(chat_content)
        messagebox.showinfo(
            "Guardado", f"El historial del chat se ha guardado en {file_path}"
        )


def load_chat_history():
    file_path = filedialog.askopenfilename(filetypes=[("Archivo de texto", "*.txt")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as file:
            chat_content = file.read()
        chat_area.configure(state="normal")
        chat_area.delete("1.0", ctk.END)
        chat_area.insert(ctk.END, chat_content)
        chat_area.configure(state="disabled")
        messagebox.showinfo(
            "Cargado", f"Se ha cargado el historial del chat desde {file_path}"
        )


def exit_application():
    if messagebox.askyesno("Salir", "¿Estás seguro de que quieres salir?"):
        root.destroy()


def toggle_theme():
    current_theme = ctk.get_appearance_mode()
    new_theme = "Dark" if current_theme == "Light" else "Light"
    ctk.set_appearance_mode(new_theme)
    messagebox.showinfo("Tema", f"Tema cambiado a {new_theme}.")


def change_font_size():
    new_size = simpledialog.askinteger(
        "Cambiar tamaño de fuente",
        "Ingrese el nuevo tamaño de fuente:",
        minvalue=8,
        maxvalue=24,
    )
    if new_size:
        chat_area.configure(font=("Roboto", new_size))
        code_area.configure(font=("Fira Code", new_size))
        messagebox.showinfo("Fuente", f"Tamaño de fuente cambiado a {new_size}.")


def export_chat():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")]
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            chat_content = chat_area.get("1.0", ctk.END)
            file.write(chat_content)
        messagebox.showinfo("Exportado", f"Chat exportado correctamente a {file_path}")


def append_to_chat(message, sender):
    chat_area.configure(state="normal")
    if sender == "user":
        chat_area.insert(ctk.END, f"{message}\n", "user")
    else:
        chat_area.insert(ctk.END, f"{message}\n", "ai")

    chat_area.see(ctk.END)
    chat.append(f"{message}\n")
    with open(current_history_file, "a") as file:
        file.write(f"{message}\n")


def load_history_file():
    file_path = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
    if file_path:
        load_chat_history(file_path)

def new_chat():
    """Crea un nuevo chat limpiando el área de chat y creando un nuevo archivo de historial."""
    global current_history_file, chat
    
    # Generar nuevo nombre de archivo con timestamp
    timestamp = datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
    current_history_file = f"history_{timestamp}.txt"
    
    # Limpiar la lista de chat
    chat = []
    
    # Limpiar el área de chat
    chat_area.configure(state="normal")
    chat_area.delete("1.0", ctk.END)
    chat_area.configure(state="disabled")
    
    # Limpiar el área de código
    code_area.configure(state="normal")
    code_area.delete("1.0", ctk.END)
    code_area.configure(state="disabled")
    
    # Limpiar el gráfico
    ax.clear()
    canvas.draw()
    
    # Mostrar mensaje de confirmación
    typing_label.configure(text="Nuevo chat creado")
    root.after(2000, lambda: typing_label.configure(text=""))  # Limpiar mensaje después de 2 segundos

def main():
    global root, sidebar_frame, main_frame, chat_area, code_area, input_field, typing_label
    global notebook, copy_button, ax, canvas
    
    # Crear la ventana principal con un tema más moderno
    root = ctk.CTk()
    root.title("ChatBot AI")
    root.geometry("1200x800")

    # Configurar tema oscuro mejorado
    ctk.set_appearance_mode("dark")
    
    # Configurar grid layout principal
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Sidebar con diseño mejorado y efecto de profundidad
    sidebar_frame = ctk.CTkFrame(
        root,
        width=280,
        corner_radius=20,
        fg_color="#1a1a1a",
        border_width=2,
        border_color="#2d2d2d"
    )
    sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=20, pady=20)
    sidebar_frame.grid_rowconfigure(10, weight=1)
    sidebar_frame.grid_propagate(False)

    # Logo y título con efecto de brillo
    logo_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
    logo_frame.grid(row=0, column=0, padx=20, pady=(30, 15), sticky="ew")
    
    logo_label = ctk.CTkLabel(
        logo_frame,
        text="ChatBot AI",
        font=ctk.CTkFont(family="Roboto", size=32, weight="bold"),
        text_color="#4CAF50"
    )
    logo_label.pack(pady=15)

    # Separador con gradiente mejorado
    separator = ctk.CTkFrame(sidebar_frame, height=3, fg_color="#4CAF50")
    separator.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 25))

    # Botones del sidebar con efectos visuales mejorados
    button_params = {
        "fg_color": "#2d2d2d",
        "hover_color": "#3d8c40",
        "corner_radius": 15,
        "border_width": 2,
        "border_color": "#3d3d3d",
        "font": ctk.CTkFont(family="Roboto", size=15, weight="bold"),
        "height": 50,
        "width": 230
    }

    new_chat_button = ctk.CTkButton(
        sidebar_frame,
        text="Nuevo Chat",
        command=new_chat,
        **button_params
    )
    new_chat_button.grid(row=2, column=0, padx=20, pady=10)

    load_history_button = ctk.CTkButton(
        sidebar_frame,
        text="Cargar Historial",
        command=load_history_file,
        **button_params
    )
    load_history_button.grid(row=3, column=0, padx=20, pady=10)

    custom_prompt_button = ctk.CTkButton(
        sidebar_frame,
        text="Prompt Personalizado",
        command=prompt_for_custom_prompt,
        **button_params
    )
    custom_prompt_button.grid(row=4, column=0, padx=20, pady=10)

    # Frame principal con efecto de profundidad
    main_frame = ctk.CTkFrame(
        root,
        corner_radius=20,
        fg_color="#242424",
        border_width=2,
        border_color="#2d2d2d"
    )
    main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
    
    # Configurar el peso de las filas y columnas del main_frame
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)

    # Notebook con diseño más moderno
    notebook = ctk.CTkTabview(
        main_frame,
        corner_radius=15,
        segmented_button_fg_color="#2d2d2d",
        segmented_button_selected_color="#4CAF50",
        segmented_button_selected_hover_color="#3d8c40",
        fg_color="#1e1e1e",
        border_width=2,
        border_color="#2d2d2d"
    )
    notebook.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 0))

    # Crear y configurar pestañas
    chat_tab = notebook.add("Chat")
    code_tab = notebook.add("Código")
    graph_tab = notebook.add("Gráfico")

    # Configurar chat_tab para que ocupe todo el espacio
    chat_tab.grid_columnconfigure(0, weight=1)
    chat_tab.grid_rowconfigure(0, weight=1)

    # Área de chat con diseño mejorado y expandido
    chat_area = ctk.CTkTextbox(
        chat_tab,
        wrap="word",
        font=ctk.CTkFont(family="Roboto", size=14),
        fg_color="#2d2d2d",
        text_color="#ffffff",
        corner_radius=15,
        border_width=2,
        border_color="#3d3d3d",
        scrollbar_button_color="#4CAF50",
        scrollbar_button_hover_color="#3d8c40"
    )
    chat_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Estilos de mensajes mejorados con márgenes ajustados
    chat_area.tag_config(
        "user",
        justify="right",
        background="#2e7d32",
        foreground="#ffffff",
        spacing1=10,
        spacing3=10,
        lmargin1=60,
        rmargin=15
    )
    
    chat_area.tag_config(
        "ai",
        justify="left",
        background="#1565c0",
        foreground="#ffffff",
        spacing1=10,
        spacing3=10,
        lmargin1=15,
        rmargin=60
    )

    # Configurar code_tab con diseño mejorado
    code_frame = ctk.CTkFrame(code_tab, fg_color="#1e1e1e")
    code_frame.pack(expand=True, fill="both", padx=15, pady=15)

    code_area = ctk.CTkTextbox(
        code_frame,
        wrap="none",
        font=("Fira Code", 12),
        fg_color="#2d2d2d",
        text_color="#ffffff",
        corner_radius=12,
        border_width=1,
        border_color="#333333"
    )
    code_area.pack(side="left", expand=True, fill="both", padx=(0, 10))

    # Frame para botones de código
    code_buttons_frame = ctk.CTkFrame(code_frame, fg_color="transparent", width=120)
    code_buttons_frame.pack(side="right", fill="y", padx=(0, 5))

    copy_button = ctk.CTkButton(
        code_buttons_frame,
        text="Copiar Código",
        command=copy_code_to_clipboard,
        fg_color="#064F36",
        hover_color="#0D845B",
        corner_radius=8,
        height=40
    )
    copy_button.pack(pady=(0, 10))

    exec_button = ctk.CTkButton(
        code_buttons_frame,
        text="Ejecutar Código",
        command=execute_code,
        fg_color="#064F36",
        hover_color="#0D845B",
        corner_radius=8,
        height=40
    )
    exec_button.pack()

    # Configurar graph_tab
    graph_frame = ctk.CTkFrame(graph_tab, fg_color="#1e1e1e")
    graph_frame.pack(expand=True, fill="both", padx=15, pady=15)

    figure, ax = plt.subplots(figsize=(5, 4), dpi=100)
    canvas = FigureCanvasTkAgg(figure, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)

    # Frame de entrada mejorado
    input_frame = ctk.CTkFrame(
        main_frame,
        height=90,
        width=800,  # Ancho fijo para centrar
        fg_color="#2d2d2d",
        corner_radius=12
    )
    input_frame.grid(row=1, column=0, sticky="s", padx=15, pady=(0, 15))
    input_frame.grid_propagate(False)  # Mantener tamaño fijo
    input_frame.grid_columnconfigure(0, weight=1)
    
    # Centrar el input_frame
    main_frame.grid_columnconfigure(0, weight=1)  # Permite centrado horizontal

    # Campo de entrada con diseño moderno
    input_field = ctk.CTkEntry(
        input_frame,
        placeholder_text="Escribe tu mensaje aquí...",
        height=55,
        width=500,  # Ancho fijo para el campo de entrada
        font=ctk.CTkFont(family="Roboto", size=15),
        fg_color="#333333",
        text_color="#ffffff",
        placeholder_text_color="#888888",
        border_width=2,
        border_color="#4CAF50",
        corner_radius=15
    )
    input_field.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
    input_field.bind("<Return>", lambda event: send_message(send_button))

    # Frame para botones de acción
    button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
    button_frame.grid(row=0, column=1, padx=15)

    send_button = ctk.CTkButton(
        button_frame,
        text="Enviar",
        command=lambda: send_message(send_button),
        fg_color="#4CAF50",
        hover_color="#3d8c40",
        height=55,
        width=110,
        corner_radius=15,
        font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
        border_width=2,
        border_color="#3d8c40"
    )
    send_button.pack(side="left", padx=8)

    file_button = ctk.CTkButton(
        button_frame,
        text="Archivo",
        command=pdf_to_text,
        fg_color="#1976D2",
        hover_color="#1565c0",
        height=55,
        width=110,
        corner_radius=15,
        font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
        border_width=2,
        border_color="#1565c0"
    )
    file_button.pack(side="left", padx=8)

    # Etiqueta de estado mejorada
    typing_label = ctk.CTkLabel(
        input_frame,
        text="",
        font=ctk.CTkFont(family="Roboto", size=12),
        text_color="#888888"
    )
    typing_label.grid(row=1, column=0, columnspan=2, pady=(0, 5))

    root.mainloop()



def run_app():
    global api_key
    # Configuración inicial
    api_key = load_api_key()
    if not api_key:
        prompt_for_api_key()
    else:
        configure_generative_ai(api_key)
        main()


if __name__ == "__main__":
    run_app()
