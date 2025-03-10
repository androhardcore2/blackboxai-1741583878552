from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os
from typing import Optional, List, Dict, Callable, Any
import time

class BloggerAPIHandler:
    def __init__(self, logger_callback: Optional[Callable] = None):
        """Initialize the Blogger API handler.
        
        Args:
            logger_callback (callable, optional): Function to call for logging
        """
        self.SCOPES = ['https://www.googleapis.com/auth/blogger']
        self.credentials: Optional[Credentials] = None
        self.service = None
        self.blogs: List[Dict] = []
        self.logger = logger_callback or print
        self.token_file = 'token.pickle'

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message using the provided callback."""
        if self.logger:
            self.logger(message, level)

    def authenticate(self, credentials_file: str) -> bool:
        """Authenticate with the Blogger API.
        
        Args:
            credentials_file (str): Path to the client secrets file
            
        Returns:
            bool: True if authentication was successful
        """
        try:
            self.credentials = None
            
            # Try to load existing credentials
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)

            # Check if credentials are valid
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.log("Refreshing access token...", level="INFO")
                    self.credentials.refresh(Request())
                else:
                    self.log("Starting new authentication flow...", level="INFO")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, self.SCOPES)
                    self.credentials = flow.run_local_server(port=0)

                # Save credentials
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)

            # Build the service
            self.service = build('blogger', 'v3', credentials=self.credentials)
            self.log("Successfully authenticated with Blogger API", level="SUCCESS")
            
            return True

        except Exception as e:
            self.log(f"Authentication error: {str(e)}", level="ERROR")
            return False

    def refresh_blogs(self) -> List[Dict]:
        """Refresh the list of available blogs.
        
        Returns:
            List[Dict]: List of blog information dictionaries
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            # Get the blogs
            blogs = self.service.blogs().listByUser(userId='self').execute()
            
            # Store and return blog information
            self.blogs = [{
                'id': blog['id'],
                'name': blog['name'],
                'url': blog.get('url', ''),
                'description': blog.get('description', ''),
                'posts': blog.get('posts', {}).get('totalItems', 0)
            } for blog in blogs.get('items', [])]
            
            self.log(f"Found {len(self.blogs)} blogs", level="INFO")
            return self.blogs

        except Exception as e:
            self.log(f"Error refreshing blogs: {str(e)}", level="ERROR")
            return []

    def get_selected_blog_id(self, blog_name: str) -> Optional[str]:
        """Get the ID of a blog by its name.
        
        Args:
            blog_name (str): Name of the blog
            
        Returns:
            str: Blog ID or None if not found
        """
        try:
            for blog in self.blogs:
                if blog['name'] == blog_name:
                    return blog['id']
            return None
        except Exception as e:
            self.log(f"Error getting blog ID: {str(e)}", level="ERROR")
            return None

    def post_article(self, blog_id: str, title: str, content: str, 
                    is_draft: bool = False, labels: Optional[List[str]] = None) -> bool:
        """Post an article to a blog.
        
        Args:
            blog_id (str): ID of the blog to post to
            title (str): Article title
            content (str): Article content (HTML)
            is_draft (bool): Whether to save as draft
            labels (List[str], optional): List of labels/tags
            
        Returns:
            bool: True if posting was successful
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            # Prepare the post body
            post_body = {
                'kind': 'blogger#post',
                'blog': {'id': blog_id},
                'title': title,
                'content': content,
            }

            # Add labels if provided
            if labels:
                post_body['labels'] = labels

            # Attempt to post with retries
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Create the post
                    request = self.service.posts().insert(
                        blogId=blog_id,
                        body=post_body,
                        isDraft=is_draft
                    )
                    
                    post = request.execute()
                    
                    self.log(f"Successfully posted article: {title}", level="SUCCESS")
                    return True
                    
                except HttpError as e:
                    if e.resp.status in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        self.log(f"API error, retrying in {wait_time} seconds...", level="WARNING")
                        time.sleep(wait_time)
                        continue
                    raise

        except Exception as e:
            self.log(f"Error posting article: {str(e)}", level="ERROR")
            return False

    def get_blog_info(self, blog_id: str) -> Optional[Dict]:
        """Get detailed information about a blog.
        
        Args:
            blog_id (str): ID of the blog
            
        Returns:
            Dict: Blog information or None if not found
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            blog = self.service.blogs().get(blogId=blog_id).execute()
            
            return {
                'id': blog['id'],
                'name': blog['name'],
                'url': blog.get('url', ''),
                'description': blog.get('description', ''),
                'posts': blog.get('posts', {}).get('totalItems', 0),
                'created': blog.get('published', ''),
                'updated': blog.get('updated', '')
            }

        except Exception as e:
            self.log(f"Error getting blog info: {str(e)}", level="ERROR")
            return None

    def delete_post(self, blog_id: str, post_id: str) -> bool:
        """Delete a blog post.
        
        Args:
            blog_id (str): ID of the blog
            post_id (str): ID of the post to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            self.service.posts().delete(blogId=blog_id, postId=post_id).execute()
            self.log(f"Successfully deleted post {post_id}", level="SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error deleting post: {str(e)}", level="ERROR")
            return False

    def update_post(self, blog_id: str, post_id: str, title: str, 
                   content: str, labels: Optional[List[str]] = None) -> bool:
        """Update an existing blog post.
        
        Args:
            blog_id (str): ID of the blog
            post_id (str): ID of the post to update
            title (str): New title
            content (str): New content
            labels (List[str], optional): New labels/tags
            
        Returns:
            bool: True if update was successful
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            # Prepare the update body
            post_body = {
                'kind': 'blogger#post',
                'id': post_id,
                'blog': {'id': blog_id},
                'title': title,
                'content': content
            }

            if labels:
                post_body['labels'] = labels

            # Update the post
            self.service.posts().update(
                blogId=blog_id,
                postId=post_id,
                body=post_body
            ).execute()

            self.log(f"Successfully updated post: {title}", level="SUCCESS")
            return True

        except Exception as e:
            self.log(f"Error updating post: {str(e)}", level="ERROR")
            return False

    def get_posts(self, blog_id: str, max_results: int = 10, 
                 status: str = 'live') -> List[Dict]:
        """Get recent posts from a blog.
        
        Args:
            blog_id (str): ID of the blog
            max_results (int): Maximum number of posts to return
            status (str): Post status ('live', 'draft', or 'scheduled')
            
        Returns:
            List[Dict]: List of post information dictionaries
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            posts = self.service.posts().list(
                blogId=blog_id,
                maxResults=max_results,
                status=status
            ).execute()

            return [{
                'id': post['id'],
                'title': post['title'],
                'url': post.get('url', ''),
                'published': post.get('published', ''),
                'updated': post.get('updated', ''),
                'labels': post.get('labels', [])
            } for post in posts.get('items', [])]

        except Exception as e:
            self.log(f"Error getting posts: {str(e)}", level="ERROR")
            return []

    def check_api_quota(self) -> Dict[str, Any]:
        """Check the current API quota usage.
        
        Returns:
            Dict: Quota information
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Please authenticate first.")

            # Get quota information from the API
            quota = self.service._http.request.credentials.get_quota()
            
            return {
                'queries_used': quota.get('queries', {}).get('used', 0),
                'queries_limit': quota.get('queries', {}).get('limit', 0),
                'quota_reset_time': quota.get('reset_time', ''),
                'remaining': quota.get('remaining', 0)
            }

        except Exception as e:
            self.log(f"Error checking API quota: {str(e)}", level="ERROR")
            return {
                'queries_used': 0,
                'queries_limit': 0,
                'quota_reset_time': '',
                'remaining': 0
            }
