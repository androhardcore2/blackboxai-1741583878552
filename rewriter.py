import re
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests

class ArticleRewriterEngine:
    def __init__(self, api_key=None, logger_callback=None):
        """Initialize the article rewriter engine.
        
        Args:
            api_key (str): Google API key for the Generative AI service
            logger_callback (callable): Function to call for logging messages
        """
        self.api_key = api_key
        self.logger = logger_callback or print
        self._configure_ai()

    def log(self, message, level="INFO"):
        """Log a message using the provided logger callback."""
        if self.logger:
            self.logger(message, level)

    def _configure_ai(self):
        """Configure the Google Generative AI service."""
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.log("Configured Google AI service", level="INFO")
            except Exception as e:
                self.log(f"Error configuring AI service: {str(e)}", level="ERROR")

    def set_api_key(self, api_key):
        """Set or update the API key.
        
        Args:
            api_key (str): The new API key to use
        """
        self.api_key = api_key
        self._configure_ai()

    def fetch_article(self, url):
        """Fetch article content from a URL.
        
        Args:
            url (str): The URL to fetch content from
            
        Returns:
            str: The article content, or None if fetching failed
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find the main content
            content = ""
            
            # Common content selectors
            content_selectors = [
                'article',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '#content',
                '.post',
                '.article',
                '.blog-post'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # Remove unwanted elements
                    for element in content_element.select('script, style, iframe, .comments, .sidebar, .nav, .menu, .advertisement'):
                        element.decompose()
                    content = content_element.get_text(separator='\n\n').strip()
                    break
            
            if not content:
                # Fallback to body text
                body = soup.body
                if body:
                    for element in body.select('script, style, iframe, header, footer, nav, .comments, .sidebar, .menu, .advertisement'):
                        element.decompose()
                    content = body.get_text(separator='\n\n').strip()
            
            return content
            
        except Exception as e:
            self.log(f"Error fetching article: {str(e)}", level="ERROR")
            return None

    def rewrite_article(self, article_text, title=None):
        """Rewrite an article using AI.
        
        Args:
            article_text (str): The original article text
            title (str): Optional original title
            
        Returns:
            dict: Dictionary containing the rewritten article and metadata
        """
        try:
            if not self.api_key:
                raise ValueError("API key is required for article rewriting")

            if not article_text or not isinstance(article_text, str):
                raise ValueError("Invalid article text provided")

            # Split into sections for better processing
            sections = self.split_into_sections(article_text)
            
            # Generate new title if needed
            new_title = self.generate_new_title(sections[0] if sections else article_text)
            if not new_title and title:
                new_title = title

            # Prepare rewriting prompt
            prompt = self._create_rewrite_prompt(article_text)
            
            # Call AI for rewriting
            rewritten_content = self._call_ai_api(prompt)
            
            if not rewritten_content:
                raise ValueError("Failed to generate rewritten content")

            # Ensure proper HTML structure
            if not re.search(r'<h2>|<h3>|<p>', rewritten_content):
                self.log("AI response missing HTML structure, applying formatting...", level="WARNING")
                rewritten_content = self.format_html_content(rewritten_content, new_title)
            
            # Clean and structure the HTML
            rewritten_content = self.sanitize_html(rewritten_content)
            
            return {
                'title': new_title,
                'content': rewritten_content,
                'original_title': title,
                'original_content': article_text
            }

        except Exception as e:
            self.log(f"Error in article rewriting: {str(e)}", level="ERROR")
            return None

    def _create_rewrite_prompt(self, article_text):
        """Create the prompt for article rewriting."""
        return f"""Tulis ulang artikel berikut dalam format HTML yang terstruktur.

Artikel Asli:
{article_text}

INSTRUKSI FORMAT (WAJIB DIIKUTI):
1. Buat heading utama menggunakan tag <h2> untuk setiap bagian baru
2. Buat sub-heading menggunakan tag <h3> untuk detail bagian
3. SETIAP paragraf harus dibungkus dalam tag <p>
4. Setiap paragraf harus dipisahkan dengan tag <p></p> kosong
5. Daftar harus menggunakan format:
  <ul>
    <li>Item pertama</li>
    <li>Item kedua</li>
  </ul>

ATURAN WAJIB:
- Artikel harus dibagi menjadi beberapa bagian dengan heading <h2>
- Setiap bagian harus memiliki minimal 2-3 paragraf
- Setiap paragraf harus dibungkus tag <p>
- Wajib ada tag <p></p> kosong antara elemen
- Gunakan Bahasa Indonesia yang baik dan benar
- Jangan hilangkan informasi penting dari artikel asli

Mohon tulis ulang artikel dengan format di atas:"""

    def _call_ai_api(self, prompt, max_retries=3):
        """Call the Google Generative AI API with retries."""
        try:
            # Configure the model
            model = genai.GenerativeModel('gemini-pro')
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            ]
            
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                    
                    if response.text:
                        return response.text.strip()
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    continue
            
            raise Exception("Failed to get valid response after multiple attempts")
            
        except Exception as e:
            self.log(f"Error calling Gen AI API: {str(e)}", level="ERROR")
            return None

    def generate_new_title(self, content):
        """Generate a new title for the article using AI."""
        try:
            if not content or not isinstance(content, str):
                return None

            # Truncate content if too long
            content = content[:2000]

            prompt = f"""Buat judul artikel dalam Bahasa Indonesia yang menarik dan informatif berdasarkan konten berikut:

Konten:
{content}

Pedoman:
- WAJIB dalam Bahasa Indonesia
- Buat judul yang mencerminkan isi konten dengan akurat
- Buat judul yang menarik dan mendorong pembaca untuk membaca
- Gunakan kata-kata seperti "Panduan", "Cara", "Rahasia", "Tips"
- Panjang judul antara 40-60 karakter
- Hindari judul yang berlebihan atau menyesatkan

Judul dalam Bahasa Indonesia:"""

            title = self._call_ai_api(prompt, max_tokens=50)
            if title:
                return title.strip('"\'').capitalize()[:255]
            return None

        except Exception as e:
            self.log(f"Error generating title: {str(e)}", level="ERROR")
            return None

    def split_into_sections(self, text):
        """Split text into logical sections."""
        text = re.sub(r'\s+', ' ', text)
        sections = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        min_section_length = 200
        grouped_sections = []
        current_section = []
        
        for section in sections:
            current_section.append(section)
            if sum(len(s) for s in current_section) >= min_section_length:
                grouped_sections.append(' '.join(current_section))
                current_section = []
        
        if current_section:
            grouped_sections.append(' '.join(current_section))
        
        return grouped_sections

    def sanitize_html(self, html_content):
        """Clean and structure HTML content."""
        try:
            # Remove problematic elements
            html_content = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style.*?>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
            
            # Clean up whitespace
            html_content = html_content.replace('&nbsp;', ' ')
            html_content = re.sub(r'\s+', ' ', html_content)
            
            # Ensure proper spacing between elements
            html_content = re.sub(r'</h2>\s*<h2>', '</h2>\n<p></p>\n<h2>', html_content)
            html_content = re.sub(r'</h3>\s*<h3>', '</h3>\n<p></p>\n<h3>', html_content)
            html_content = re.sub(r'</p>\s*<p>', '</p>\n<p></p>\n<p>', html_content)
            html_content = re.sub(r'</ul>\s*<', '</ul>\n<p></p>\n<', html_content)
            
            # Process paragraphs
            paragraphs = re.split(r'\n|<br\s*/?>|</div>', html_content)
            formatted_parts = []
            
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                
                if re.match(r'^<(h2|h3|p|ul|/ul|li|/li)>', p):
                    formatted_parts.append(p)
                else:
                    formatted_parts.append(f'<p>{p}</p>')
                    formatted_parts.append('<p></p>')
            
            # Join and clean up
            html_content = '\n'.join(formatted_parts)
            html_content = re.sub(r'(<p></p>\s*){2,}', '<p></p>\n', html_content)
            
            # Ensure there's at least one heading
            if not re.search(r'<h[23][^>]*>', html_content):
                html_content = f'<h2>Artikel</h2>\n<p></p>\n{html_content}'
            
            return html_content.strip()
            
        except Exception as e:
            self.log(f"Error sanitizing HTML: {str(e)}", level="ERROR")
            return f'<h2>Error</h2>\n<p></p>\n<p>Failed to process article: {str(e)}</p>'

    def generate_tags(self, content):
        """Generate tags for the article content."""
        try:
            if not self.api_key:
                return []

            prompt = f"""Generate 3-5 relevant tags for the following article content. Return only the tags as a comma-separated list:

{content[:5000]}"""

            response = self._call_ai_api(prompt)
            if response:
                tags = [tag.strip() for tag in response.split(',')]
                return [tag for tag in tags if tag][:5]
            
            return []

        except Exception as e:
            self.log(f"Error generating tags: {str(e)}", level="ERROR")
            return []

    def format_html_content(self, content, title=None):
        """Format plain text content into structured HTML.
        
        Args:
            content (str): The content to format
            title (str): Optional title to include
            
        Returns:
            str: Formatted HTML content
        """
        try:
            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Split into paragraphs
            paragraphs = content.split('\n\n')
            if len(paragraphs) == 1:
                # If no paragraph breaks, split on sentences
                paragraphs = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
            
            # Start with title if provided
            formatted_parts = []
            if title:
                formatted_parts.append(f'<h2>{title}</h2>')
                formatted_parts.append('<p></p>')
            
            # Process each paragraph
            current_section = []
            for i, p in enumerate(paragraphs):
                p = p.strip()
                if not p:
                    continue
                
                # Start new section every few paragraphs
                if i > 0 and i % 3 == 0 and current_section:
                    # Join current section
                    section_text = ' '.join(current_section)
                    
                    # Generate section heading
                    heading = self.generate_section_heading(section_text)
                    if heading:
                        formatted_parts.append(f'<h2>{heading}</h2>')
                        formatted_parts.append('<p></p>')
                    
                    # Add section paragraphs
                    for section_p in current_section:
                        formatted_parts.append(f'<p>{section_p}</p>')
                        formatted_parts.append('<p></p>')
                    
                    current_section = []
                
                current_section.append(p)
            
            # Add remaining paragraphs
            if current_section:
                for p in current_section:
                    formatted_parts.append(f'<p>{p}</p>')
                    formatted_parts.append('<p></p>')
            
            # Join all parts
            html_content = '\n'.join(formatted_parts)
            
            # Clean up multiple empty paragraphs
            html_content = re.sub(r'(<p></p>\s*){2,}', '<p></p>\n', html_content)
            
            return html_content.strip()
            
        except Exception as e:
            self.log(f"Error formatting HTML content: {str(e)}", level="ERROR")
            return f'<h2>Error</h2>\n<p></p>\n<p>Failed to format content: {str(e)}</p>'

    def generate_section_heading(self, section_text):
        """Generate a heading for a section of text using AI.
        
        Args:
            section_text (str): The section text to generate a heading for
            
        Returns:
            str: Generated heading or None if generation fails
        """
        try:
            if not section_text or not isinstance(section_text, str):
                return None

            # Truncate text if too long
            section_text = section_text[:1000]

            prompt = f"""Generate a short, descriptive heading (3-6 words) in Bahasa Indonesia for this section of text:

{section_text}

Requirements:
- Must be in Bahasa Indonesia
- Should be 3-6 words
- Should accurately describe the section content
- Should be engaging but not clickbait

Heading only:"""

            heading = self._call_ai_api(prompt, max_retries=2)
            if heading:
                # Clean up the heading
                heading = heading.strip('"\'').strip()
                heading = re.sub(r'\s+', ' ', heading)
                heading = heading[:100]  # Limit length
                return heading.capitalize()
            
            return None

        except Exception as e:
            self.log(f"Error generating section heading: {str(e)}", level="ERROR")
            return None
