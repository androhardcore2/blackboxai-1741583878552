from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import socket
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import sys

class CustomRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Call parent constructor
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/':
                self.path = '/index.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        except Exception as e:
            logger.error(f"GET request failed: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body first to avoid sending headers if body read fails
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Enable CORS and set response headers
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response_data = {}

            if self.path == '/api/blogs':
                # Get list of blogs
                blogs = [
                    {'id': '1', 'name': 'Test Blog 1'},
                    {'id': '2', 'name': 'Test Blog 2'},
                    {'id': '3', 'name': 'Test Blog 3'}
                ]
                response_data = {'blogs': blogs}

            elif self.path == '/api/rewrite':
                # Simulate article rewriting
                content = data.get('content', '')
                title = data.get('title', '')
                response_data = {
                    'result': {
                        'title': f'Rewritten: {title}',
                        'content': f'Rewritten content for: {content}'
                    }
                }

            elif self.path == '/api/fetch-articles':
                sitemap_url = data.get('sitemap_url')
                if not sitemap_url:
                    raise ValueError("Sitemap URL is required")

                try:
                    import requests
                    from bs4 import BeautifulSoup
                    import hashlib
                    
                    # Fetch the sitemap
                    response = requests.get(sitemap_url, timeout=10)
                    response.raise_for_status()
                    
                    # Parse the XML
                    soup = BeautifulSoup(response.content, 'xml')
                    urls = soup.find_all('url')
                    
                    articles = []
                    for i, url in enumerate(urls):
                        loc = url.find('loc')
                        if loc:
                            article_url = loc.text
                            # Generate a unique ID based on URL
                            article_id = hashlib.md5(article_url.encode()).hexdigest()
                            
                            # Try to fetch article title
                            try:
                                article_response = requests.get(article_url, timeout=5)
                                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                                title = article_soup.title.string if article_soup.title else f"Article {i+1}"
                                content = article_soup.get_text()[:500] + "..."  # Get first 500 chars
                            except Exception as e:
                                logger.warning(f"Could not fetch article content: {str(e)}")
                                title = f"Article {i+1}"
                                content = "Content not available"
                            
                            articles.append({
                                'id': article_id,
                                'title': title,
                                'url': article_url,
                                'content': content
                            })
                    
                    response_data = {'articles': articles}
                    logger.info(f"Successfully fetched {len(articles)} articles from sitemap")
                    
                except requests.RequestException as e:
                    logger.error(f"Failed to fetch sitemap: {str(e)}")
                    raise ValueError(f"Failed to fetch sitemap: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing sitemap: {str(e)}")
                    raise ValueError(f"Error processing sitemap: {str(e)}")

            elif self.path == '/api/post':
                # Simulate posting to blog
                response_data = {'success': True}

            # Send response
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            # Log the error
            logger.error(f"POST request failed: {str(e)}")
            
            # Send error response with 500 status
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'error': str(e),
                'status': 'error',
                'message': 'Internal server error occurred'
            }
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except Exception as e:
            logger.error(f"OPTIONS request failed: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")

def check_port_availability(port):
    """Check if the port is available for use"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except socket.error:
        return False

def run_server(port=8000):
    """Run the HTTP server"""
    try:
        # Check if port is available
        if not check_port_availability(port):
            error_msg = f"Port {port} is already in use. Please free the port or use a different one."
            logger.error(error_msg)
            print(error_msg)
            sys.exit(1)
        
        server_address = ('', port)
        httpd = HTTPServer(server_address, CustomRequestHandler)
        
        startup_msg = f"Server running on http://localhost:{port}"
        logger.info(startup_msg)
        print(startup_msg)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            shutdown_msg = "Server shutdown requested by user"
            logger.info(shutdown_msg)
            print(shutdown_msg)
            httpd.server_close()
            sys.exit(0)
        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            httpd.server_close()
            sys.exit(1)
            
    except Exception as e:
        error_msg = f"Failed to start server: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == '__main__':
    run_server()
