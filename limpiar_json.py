import codecs

with codecs.open("respaldo_utf8.json", "r", "utf-8-sig") as f:
    contenido = f.read()

with open("respaldo_limpio.json", "w", encoding="utf-8") as f:
    f.write(contenido)

print("Archivo limpio creado correctamente")
