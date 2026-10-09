
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Milux Security 2.0
Original concept: Milux (2018)
Rebuilt in Python for Termux.
"""

import os
import sys
import subprocess
import re
import json
import time
import hmac
import hashlib
import secrets
import getpass
from pathlib import Path
from datetime import datetime

# ==============================
# CONFIGURACION
# ==============================

APP_NAME = "MILUX SECURITY"
VERSION = "2.0.0"
MAX_ATTEMPTS = 3

BASE_DIR = Path.home() / ".milux-security"
CONFIG_FILE = BASE_DIR / "config.json"
RECOVERY_FILE = BASE_DIR / "recovery.json"

GREEN = "\033[92m"
CYAN = "\033[96m"
RED = "\033[91m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"


# ==============================
# INTERFAZ
# ==============================

def clear_screen():
    print(CLEAR, end="")


def pause():
    input(f"\n{DIM}Presiona ENTER para continuar...{RESET}")


def secure_prompt(message, secret=False, max_length=256):
    """No permite que Ctrl+C o Ctrl+D cancelen el flujo."""
    while True:
        try:
            if secret:
                value = getpass.getpass(message)
            else:
                value = input(message)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupcion ignorada. Continua la autenticacion.{RESET}")
            continue

        except EOFError:
            print(f"\n{YELLOW}Entrada cerrada. Intenta de nuevo.{RESET}")
            continue

        if not value:
            print(f"{YELLOW}La entrada no puede estar vacia.{RESET}")
            continue

        if len(value) > max_length:
            print(f"{RED}Entrada demasiado larga.{RESET}")
            continue

        return value



def banner():
    print(f"""{GREEN}
 __  __ _ _            _____
|  \\/  (_) |_   _  __  / ____|
| |\\/| | | | | | |/ _` | (___   ___  ___ _   _ _ __ ___
| |  | | | | |_| | (_| |\\___ \\ / _ \\/ __| | | | '__/ _ \\
|_|  |_|_|_|\\__, |\\__,_|_____) |  __/ (__| |_| | | |  __/
            |___/             \\___|\\___|\\__,_|_|  \\___|
{RESET}{CYAN}
              SECURITY TERMINAL
                 Version {VERSION}
{RESET}""")


def loading(message="Verificando sistema", duration=1.2):
    print(f"{CYAN}{message}{RESET}", end=" ", flush=True)
    symbols = ["|", "/", "-", "\\"]
    steps = max(1, int(duration / 0.08))

    for i in range(steps):
        print(f"\r{CYAN}{message} {symbols[i % len(symbols)]}{RESET}",
              end="", flush=True)
        time.sleep(0.08)

    print(f"\r{GREEN}{message} [OK]{RESET}")


def success_animation():
    clear_screen()
    banner()
    loading("Validando credenciales", 1.0)
    loading("Iniciando sesion segura", 1.0)
    print(f"\n{GREEN}  [ ACCESS GRANTED ]{RESET}")
    print(f"{GREEN}  Bienvenido al sistema.{RESET}")
    time.sleep(0.8)


def error_animation(message):
    print(f"\n{RED}  [ ACCESS DENIED ]{RESET}")
    print(f"{RED}  {message}{RESET}")
    time.sleep(0.8)


def header():
    clear_screen()
    banner()
    print(f"{DIM}  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{DIM}  Estado: SISTEMA ACTIVO{RESET}")
    print(f"{GREEN}  {'-' * 42}{RESET}\n")


# ==============================
# SMS
# ==============================

def send_sms(number, message):
    """Envia un SMS usando explicitamente la SIM 1."""
    if not number or not message:
        return False

    try:
        result = subprocess.run(
            [
                "termux-sms-send",
                "-s", "0",
                "-n", number,
                message,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False

# ==============================
# ARCHIVOS Y PERMISOS
# ==============================

def prepare_storage():
    BASE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

    try:
        os.chmod(BASE_DIR, 0o700)
    except OSError:
        pass


def write_json(path, data):
    """Escribe JSON mediante un archivo temporal y reemplazo atomico."""
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())

    try:
        os.chmod(temp_path, 0o600)
    except OSError:
        pass

    os.replace(temp_path, path)

    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ==============================
# CONTRASENAS
# ==============================

def password_record(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32
    )

    return {
        "salt": salt.hex(),
        "hash": digest.hex(),
        "algorithm": "scrypt"
    }


def verify_password(password, record):
    try:
        salt = bytes.fromhex(record["salt"])
        expected = bytes.fromhex(record["hash"])

        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=32
        )

        return hmac.compare_digest(actual, expected)
    except (KeyError, ValueError, TypeError):
        return False



def ask_new_password():
    while True:
        password = secure_prompt(
            "Nueva contrasena: ",
            secret=True,
            max_length=256
        )

        if len(password) < 10:
            print(f"{YELLOW}Usa al menos 10 caracteres.{RESET}")
            continue

        confirmation = secure_prompt(
            "Repite la contrasena: ",
            secret=True,
            max_length=256
        )

        if not hmac.compare_digest(password, confirmation):
            error_animation("Las contrasenas no coinciden.")
            continue

        return password


# ==============================
# CODIGOS DE RECUPERACION
# ==============================

def hash_recovery_code(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_recovery_codes(count=8):
    codes = [
        secrets.token_hex(8).upper()
        for _ in range(count)
    ]

    records = [hash_recovery_code(code) for code in codes]
    write_json(RECOVERY_FILE, {"hashes": records})

    return codes


def show_recovery_codes(codes):
    print(f"\n{YELLOW}IMPORTANTE: GUARDA ESTOS CODIGOS{RESET}")
    print(f"{YELLOW}Cada codigo sirve una sola vez.{RESET}\n")

    for number, code in enumerate(codes, start=1):
        print(f"  {number}. {WHITE}{code}{RESET}")

    print(f"\n{RED}No se mostraran de nuevo.{RESET}")
    print("Guardalos en un lugar privado, fuera de esta carpeta.")


def consume_recovery_code(code):
    if not RECOVERY_FILE.exists():
        return False

    try:
        data = read_json(RECOVERY_FILE)
        hashes = data.get("hashes", [])
        candidate = hash_recovery_code(code.strip().upper())

        for index, stored_hash in enumerate(hashes):
            if hmac.compare_digest(candidate, stored_hash):
                # Consumir el codigo antes de autorizar el cambio.
                hashes.pop(index)
                write_json(RECOVERY_FILE, {"hashes": hashes})
                return True

    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False

    return False


# ==============================
# CONFIGURACION INICIAL
# ==============================

def first_setup():
    clear_screen()
    banner()

    print(f"{CYAN}Primera ejecucion: configuracion inicial{RESET}\n")
    print("Crea una contrasena para proteger el acceso al programa.")
    print("Minimo: 10 caracteres.\n")

    password = ask_new_password()

    config = {
        "version": VERSION,
        "password": password_record(password),
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    codes = generate_recovery_codes()
    write_json(CONFIG_FILE, config)

    
    print(f"\n{GREEN}Configuracion creada correctamente.{RESET}")
    show_recovery_codes(codes)
    pause()

    print(f"\n{CYAN}RECUPERACION POR TELEFONO{RESET}")
    print("Puedes registrar un telefono ahora o hacerlo mas tarde.")

    register_phone = secure_prompt(
        "¿Registrar telefono ahora? [s/N]: ",
        max_length=1
    ).strip().lower()

    if register_phone == "s":
        configure_recovery_phone()
    else:
        print("Puedes registrar el telefono desde el menu principal.")
        pause()



# ==============================
# AUTENTICACION Y RECUPERACION
# ==============================



def login():
    try:
        config = read_json(CONFIG_FILE)
        record = config["password"]
    except (OSError, ValueError, KeyError, TypeError):
        print(f"{RED}Error leyendo la configuracion.{RESET}")
        return False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        header()
        print(f"{CYAN}AUTENTICACION REQUERIDA{RESET}\n")

        try:
            password = secure_prompt(
                "Contrasena: ",
                secret=True,
                max_length=256
            )
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception:
            print(f"\n{RED}Error de entrada. Acceso denegado.{RESET}")
            return False

        if verify_password(password, record):
            success_animation()
            return "normal"

        remaining = MAX_ATTEMPTS - attempt
        error_animation("Contrasena incorrecta.")

        if remaining > 0:
            print(f"{YELLOW}Intentos restantes: {remaining}{RESET}")
            time.sleep(1)
    
        error_animation("Contrasena incorrecta.")

        if remaining > 0:
            print(f"{YELLOW}Intentos restantes: {remaining}{RESET}")
            time.sleep(1)

    print(f"\n{RED}MAXIMO DE INTENTOS ALCANZADO{RESET}")
    time.sleep(0.5)

    if recover_access():
        return "recovered"
    return False



def recover_access():
    header()
    print(f"{CYAN}RECUPERACION DE ACCESO{RESET}\n")
    print("Dispones de 3 intentos para introducir un codigo valido.\n")

    # Primera etapa: codigos de recuperacion
    for attempt in range(1, 4):
        try:
            code = secure_prompt(
                "Codigo de recuperacion: ",
                secret=True,
                max_length=16
            ).strip().upper()
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception:
            print(f"\n{RED}Error de entrada. Acceso denegado.{RESET}")
            return False

        if len(code) != 16 or any(
            char not in "0123456789ABCDEF" for char in code
        ):
            valid = False
        else:
            valid = recovery_code_is_valid(code)

        if not valid:
            remaining = 3 - attempt
            error_animation("Codigo invalido o ya utilizado.")

            if remaining > 0:
                print(f"{YELLOW}Intentos restantes: {remaining}{RESET}")
                continue

            print(f"\n{YELLOW}Codigos agotados. Intentando recuperar por SMS.{RESET}")
            break

        # Codigo correcto: cambiar la contrasena
        try:
            new_password = ask_new_password()
            config = read_json(CONFIG_FILE)

            if not consume_recovery_code(code):
                error_animation("El codigo ya no es valido.")
                return False

            config["password"] = password_record(new_password)
            config["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            write_json(CONFIG_FILE, config)

            print(f"\n{GREEN}Contrasena actualizada correctamente.{RESET}")
            loading("Restaurando acceso", 1.0)
            return True

        except (OSError, ValueError, TypeError, KeyError):
            error_animation("No se pudo completar la recuperacion.")
            return False

    # Segunda etapa: recuperacion por SMS
    try:
        config = read_json(CONFIG_FILE)
        number = config.get("recovery_phone")
        verified_at = config.get("recovery_phone_verified_at")
    except (OSError, ValueError, TypeError):
        error_animation("No se pudo leer la configuracion.")
        return False

    if not number or not verified_at:
        error_animation(
            "No hay un telefono verificado. Acceso denegado."
        )
        return False

    sms_code = f"{secrets.randbelow(1000000):06d}"

    print(f"\n{CYAN}RECUPERACION POR SMS{RESET}")
    print(f"Enviando codigo al telefono registrado: {number}")

    if not send_sms(
        number,
        f"Milux Security: codigo de recuperacion {sms_code}. "
        "Caduca en 5 minutos."
    ):
        error_animation("No se pudo enviar el SMS. Acceso denegado.")
        return False

    expires = time.monotonic() + 300

    for attempt in range(1, 4):
        if time.monotonic() >= expires:
            error_animation("El codigo SMS ha caducado.")
            return False

        try:
            entered = secure_prompt(
                "Codigo SMS de 6 digitos: ",
                secret=True,
                max_length=6
            ).strip()
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception:
            error_animation("Error de entrada. Acceso denegado.")
            return False

        if hmac.compare_digest(entered, sms_code):
            try:
                new_password = ask_new_password()
                config = read_json(CONFIG_FILE)
                config["password"] = password_record(new_password)
                config["updated_at"] = datetime.now().isoformat(
                    timespec="seconds"
                )
                write_json(CONFIG_FILE, config)
            except (OSError, ValueError, TypeError, KeyError):
                error_animation("No se pudo actualizar la contrasena.")
                return False

            print(f"\n{GREEN}Contrasena actualizada correctamente.{RESET}")
            loading("Restaurando acceso", 1.0)
            return True

        remaining = 3 - attempt
        error_animation("Codigo SMS incorrecto.")

        if remaining > 0:
            print(f"{YELLOW}Intentos restantes: {remaining}{RESET}")

    error_animation(
        "Verificacion SMS bloqueada. Inicia sesion nuevamente."
    )
    return False


def recovery_code_is_valid(code):
    if not RECOVERY_FILE.exists():
        return False

    try:
        data = read_json(RECOVERY_FILE)
        candidate = hash_recovery_code(code)

        return any(
            hmac.compare_digest(candidate, stored)
            for stored in data.get("hashes", [])
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def change_password():
    header()
    print(f"{CYAN}CAMBIAR CONTRASENA{RESET}\n")

    try:
        config = read_json(CONFIG_FILE)
    except (OSError, ValueError):
        error_animation("No se pudo leer la configuracion.")
        pause()
        return

    current = getpass.getpass("Contrasena actual: ")

    if not verify_password(current, config.get("password", {})):
        error_animation("Contrasena actual incorrecta.")
        pause()
        return

    new_password = ask_new_password()
    config["password"] = password_record(new_password)
    config["updated_at"] = datetime.now().isoformat(timespec="seconds")

    try:
        write_json(CONFIG_FILE, config)
        print(f"\n{GREEN}Contrasena cambiada correctamente.{RESET}")
    except OSError:
        error_animation("No se pudo guardar el cambio.")

    pause()


def regenerate_recovery_codes():
    header()
    print(f"{CYAN}RENOVAR CODIGOS DE RECUPERACION{RESET}\n")

    try:
        config = read_json(CONFIG_FILE)
    except (OSError, ValueError):
        error_animation("No se pudo leer la configuracion.")
        pause()
        return

    current = secure_prompt("Contrasena actual: ", secret=True)

    if not verify_password(current, config.get("password", {})):
        error_animation("Contrasena incorrecta.")
        pause()
        return

    codes = generate_recovery_codes()
    show_recovery_codes(codes)
    pause()


# ==============================
# MENU PRINCIPAL
# ==============================


def configure_recovery_phone():
    header()
    print(f"{CYAN}REGISTRAR TELEFONO DE RECUPERACION{RESET}\n")

    try:
        config = read_json(CONFIG_FILE)
    except (OSError, ValueError, TypeError):
        error_animation("No se pudo leer la configuracion.")
        pause()
        return

    number = secure_prompt(
        "Numero con prefijo internacional (+1...): ",
        max_length=16
    ).strip()

    if not re.fullmatch(r"\+[1-9][0-9]{7,14}", number):
        error_animation("Formato invalido. Usa + seguido del numero.")
        pause()
        return

    code = f"{secrets.randbelow(1000000):06d}"

    print("\nEnviando codigo de verificacion por la SIM 1...")

    if not send_sms(
        number,
        f"Milux Security: tu codigo es {code}. Caduca en 5 minutos."
    ):
        error_animation("No se pudo iniciar el envio del SMS.")
        pause()
        return

    expires = time.monotonic() + 300

    for attempt in range(3):
        if time.monotonic() >= expires:
            error_animation("El codigo ha caducado.")
            pause()
            return

        entered = secure_prompt(
            "Codigo recibido por SMS: ",
            secret=True,
            max_length=6
        ).strip()

        if hmac.compare_digest(entered, code):
            config["recovery_phone"] = number
            config["recovery_phone_verified_at"] = (
                datetime.now().isoformat(timespec="seconds")
            )

            try:
                write_json(CONFIG_FILE, config)
            except (OSError, ValueError, TypeError):
                error_animation("No se pudo guardar el numero.")
                pause()
                return

            print(f"\n{GREEN}Telefono registrado correctamente.{RESET}")
            pause()
            return

        remaining = 2 - attempt
        error_animation("Codigo incorrecto.")

        if remaining > 0:
            print(f"{YELLOW}Intentos restantes: {remaining}{RESET}")

    error_animation("Verificacion bloqueada.")
    pause()


def main_menu():
    while True:
        header()

        print(f"{GREEN}  [1] Cambiar contrasena")
        print("  [2] Renovar codigos de recuperacion")
        print("  [3] Registrar telefono de recuperacion")
        print("  [4] Cerrar sesion")

        option = secure_prompt("Selecciona una opcion: ", max_length=2).strip()

        if option == "1":
            change_password()
        elif option == "2":
            regenerate_recovery_codes()
        elif option == "3":
            configure_recovery_phone()
        elif option == "4":
            return
        else:
            error_animation("Opcion no valida.")
            pause()


# ==============================
# INICIO
# ==============================


def main():
    if os.name != "posix":
        print("Este programa esta pensado para Termux y Unix.")
        return 1

    try:
        prepare_storage()

        if not CONFIG_FILE.exists():
            if RECOVERY_FILE.exists():
                print(
                    f"{RED}Falta la configuracion, "
                    f"pero existen codigos.{RESET}"
                )
                print("No se reinicializara automaticamente.")
                return 1

            first_setup()

        
        while True:
            auth_result = login()

            if not auth_result:
                print(f"\n{RED}Sesion no autorizada.{RESET}")
                print("Volviendo al inicio de sesion...\n")
                time.sleep(1)
                continue

            if auth_result == "recovered":
                print(
                    f"\n{GREEN}Recuperacion completada.{RESET}"
                )
                main_menu()
                return 0

            print(
                f"\n{GREEN}Acceso concedido. "
                f"Terminal disponible.{RESET}"
            )
            time.sleep(0.5)
            os.system("clear")
            return 0

    except (OSError, ValueError, TypeError):
        print(f"\n{RED}Error del sistema. Acceso denegado.{RESET}")
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Operacion cancelada.{RESET}")
        raise SystemExit(1)
    except EOFError:
        print(f"\n\n{YELLOW}Entrada finalizada.{RESET}")
        raise SystemExit(1)

