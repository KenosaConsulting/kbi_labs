#!/usr/bin/env python3
"""
Simple SPA (Single Page Application) server that serves index.html for all routes
"""
import http.server
import socketserver
import os
from urllib.parse import urlparse

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # If requesting a file that exists, serve it normally
        if os.path.exists(self.translate_path(self.path)) and os.path.isfile(self.translate_path(self.path)):
            return super().do_GET()
        
        # For all other routes (like /government-contractor), serve index.html
        self.path = '/index.html'
        return super().do_GET()

if __name__ == "__main__":
    PORT = 9001
    os.chdir("/Users/oogwayuzumaki/Desktop/Work/BI/kbi_labs/KBILabs-main 2/kbi_dashboard/dist")
    
    with socketserver.TCPServer(("", PORT), SPAHandler) as httpd:
        print(f"🚀 SPA Server running at http://localhost:{PORT}")
        print(f"📂 Serving from: {os.getcwd()}")
        print(f"🔗 Dashboard: http://localhost:{PORT}/government-contractor")
        httpd.serve_forever()