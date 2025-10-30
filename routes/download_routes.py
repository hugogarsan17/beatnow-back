from fastapi import APIRouter, HTTPException, requests
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
import paramiko
import requests  # Importación correcta

from config.security import SSH_HOST_RES, SSH_PASSWORD_RES, SSH_USERNAME_RES

# Iniciar router
router = APIRouter()

APK_DIRECTORY= "/res/android/"

@router.get("/android-apk")
async def download_android_apk():
    apk_url = "http://172.203.251.28/res/android/beatnow_app.apk"
    try:
        # Haz la petición al URL y asegúrate de hacer stream para manejar grandes archivos
        response = requests.get(apk_url, stream=True)
        return StreamingResponse(response.iter_content(32 * 1024), media_type="application/vnd.android.package-archive", headers={"Content-Disposition": "attachment; filename=beatnow_app.apk"})
    except requests.RequestException as e:
        # Maneja posibles errores en la petición
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-apk")
async def download_latest_apk():
    # Iniciar la conexión SSH
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

        # Comando para listar archivos y obtener el más reciente
        stdin, stdout, stderr = ssh.exec_command(f"ls -t {APK_DIRECTORY}/*")
        latest_apk = stdout.readline().strip()  

        if latest_apk:
            full_path = f"http://{SSH_HOST_RES}{APK_DIRECTORY}/{latest_apk}"
            return FileResponse(full_path, media_type='application/vnd.android.package-archive', filename=latest_apk)
        else:
            return {"error": "No APK found"}