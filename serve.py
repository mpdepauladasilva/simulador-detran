#!/usr/bin/env python3
"""
Servidor local para o Simulador DETRAN.
Execute: python serve.py
Depois abra: http://localhost:8080
"""
import http.server
import socketserver
import webbrowser
import os

PORT = 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))

handler = http.server.SimpleHTTPRequestHandler
handler.extensions_map.update({'.js': 'application/javascript', '.json': 'application/json'})

print(f'Simulador DETRAN rodando em: http://localhost:{PORT}')
print('Pressione Ctrl+C para encerrar.\n')

with socketserver.TCPServer(('', PORT), handler) as httpd:
    webbrowser.open(f'http://localhost:{PORT}')
    httpd.serve_forever()
