#!/usr/bin/env python3
"""Simple HTTP server for frontend"""
import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = "src"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving frontend on http://localhost:{PORT}")
    httpd.serve_forever()
