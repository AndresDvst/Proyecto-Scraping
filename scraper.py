import requests
import time
import sys
import json

# Uso: python scraper.py <sessionid> <username>
if len(sys.argv) < 3:
    print("Uso: python scraper.py <sessionid> <username>")
    sys.exit(1)

sessionid = sys.argv[1]
target_username = sys.argv[2]

headers = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"sessionid={sessionid}",
    "X-IG-App-ID": "936619743392459"
}

LIMIT_SEGUIDORES = 5000
PAUSA_CADA = 2500
TIEMPO_ESPERA = 60  # segundos

def get_user_id(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        try:
            return res.json()["data"]["user"]["id"]
        except Exception:
            print("❌ ERROR: No se pudo extraer el ID del perfil.", file=sys.stderr)
            return None
    elif res.status_code in [401, 403]:
        print("❌ ERROR: Session ID inválido o expirado al obtener el ID del usuario.", file=sys.stderr)
        return None
    else:
        print(f"❌ ERROR {res.status_code}: No se pudo obtener información del perfil.", file=sys.stderr)
        return None

def get_followers(user_id):
    followers = []
    next_max_id = ""
    total_descansos = 0

    while len(followers) < LIMIT_SEGUIDORES:
        url = f"https://i.instagram.com/api/v1/friendships/{user_id}/followers/"
        params = {
            "count": 50,
        }
        if next_max_id:
            params["max_id"] = next_max_id

        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 200:
            data = res.json()
            nuevos_seguidores = [{"username": user["username"]} for user in data.get("users", [])]
            followers.extend(nuevos_seguidores)

            if len(followers) >= LIMIT_SEGUIDORES:
                followers = followers[:LIMIT_SEGUIDORES]
                print(f"✅ Límite de {LIMIT_SEGUIDORES} seguidores alcanzado.")
                break

            if len(followers) >= (PAUSA_CADA * (total_descansos + 1)):
                total_descansos += 1
                print(f"⏸️ Descansando {TIEMPO_ESPERA} segundos... llevamos {len(followers)} seguidores")
                time.sleep(TIEMPO_ESPERA)

            next_max_id = data.get("next_max_id")
            if not next_max_id:
                break
            time.sleep(2)

        elif res.status_code in [401, 403]:
            print("❌ ERROR: Session ID inválido o expirado al obtener seguidores.", file=sys.stderr)
            return []
        else:
            print(f"⚠️ ADVERTENCIA {res.status_code}: Error al obtener seguidores.", file=sys.stderr)
            return []

    return followers

if __name__ == "__main__":
    user_id = get_user_id(target_username)
    if user_id:
        followers = get_followers(user_id)
        if followers:
            print(json.dumps({"followers": followers}, ensure_ascii=False, indent=4))
        else:
            print(json.dumps({"error": "No se pudieron obtener seguidores. Verifica el Session ID."}, ensure_ascii=False, indent=4))
    else:
        print(json.dumps({"error": "No se pudo obtener el ID del usuario. Verifica el username o Session ID."}, ensure_ascii=False, indent=4))
