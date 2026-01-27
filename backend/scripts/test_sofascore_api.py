print("HOLA - El script está corriendo")
print("=" * 50)

try:
    from curl_cffi import requests
    print("✓ curl_cffi importado correctamente")
    
    print("Realizando petición...")
    r = requests.get('https://api.sofascore.com/api/v1/unique-tournament/8', impersonate='chrome', timeout=10)
    
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        print('✅ Sofascore accesible!')
        data = r.json()
        print(f'Liga: {data.get("uniqueTournament", {}).get("name", "?")}')
    else:
        print(f'❌ Error: {r.status_code}')
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("=" * 50)
print("FIN DEL SCRIPT")