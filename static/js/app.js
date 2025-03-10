class ArticleRewriter {
    constructor() {
        this.apiKey = '';
        this.articles = [];
        this.selectedArticle = null;
        
        // Initialize event listeners after DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeEventListeners();
            // Show settings tab by default
            this.switchTab('settings');
        });
    }

    initializeEventListeners() {
        // API Key handling
        document.getElementById('saveApiKey')?.addEventListener('click', () => {
            this.apiKey = document.getElementById('apiKey').value;
            this.showNotification('API key saved successfully', 'success');
        });

        document.getElementById('toggleApiKey')?.addEventListener('click', () => {
            const input = document.getElementById('apiKey');
            if (input) {
                input.type = input.type === 'password' ? 'text' : 'password';
            }
        });

        // Blog refresh
        document.getElementById('refreshBlogs')?.addEventListener('click', () => this.refreshBlogs());

        // Article actions
        document.getElementById('fetchArticles')?.addEventListener('click', () => this.fetchArticles());
        document.getElementById('rewriteArticles')?.addEventListener('click', () => this.rewriteSelectedArticles());
        document.getElementById('scheduleArticles')?.addEventListener('click', () => this.scheduleSelectedArticles());
        document.getElementById('postArticles')?.addEventListener('click', () => this.postSelectedArticles());

        // Tab switching
        document.querySelectorAll('.tab-link').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const href = e.currentTarget.getAttribute('href');
                if (href) {
                    const tabId = href.replace('#', '');
                    this.switchTab(tabId);
                }
            });
        });
    }

    switchTab(tabId) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected tab content
        const selectedContent = document.getElementById(tabId);
        if (selectedContent) {
            selectedContent.classList.remove('hidden');
        }

        // Update tab styles
        document.querySelectorAll('.tab-link').forEach(tab => {
            tab.classList.remove('bg-blue-50', 'text-blue-600');
            tab.classList.add('text-gray-600', 'hover:bg-gray-50');
        });

        const selectedTab = document.querySelector(`[href="#${tabId}"]`);
        if (selectedTab) {
            selectedTab.classList.add('bg-blue-50', 'text-blue-600');
            selectedTab.classList.remove('text-gray-600', 'hover:bg-gray-50');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white ${
            type === 'error' ? 'bg-red-500' : 
            type === 'success' ? 'bg-green-500' : 
            'bg-blue-500'
        }`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    showLoading(message) {
        const loading = document.createElement('div');
        loading.id = 'loadingOverlay';
        loading.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center';
        loading.innerHTML = `
            <div class="bg-white p-4 rounded-lg flex items-center space-x-3">
                <div class="animate-spin rounded-full h-6 w-6 border-4 border-blue-500 border-t-transparent"></div>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(loading);
    }

    hideLoading() {
        const loading = document.getElementById('loadingOverlay');
        if (loading) {
            loading.remove();
        }
    }

    async refreshBlogs() {
        try {
            if (!this.apiKey) {
                throw new Error('Please set your API key first');
            }

            this.showLoading('Refreshing blogs...');

            const response = await fetch('/api/blogs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    api_key: this.apiKey
                })
            });

            const data = await response.json();
            if (data.blogs) {
                const blogSelect = document.getElementById('blogSelect');
                if (blogSelect) {
                    blogSelect.innerHTML = '';
                    data.blogs.forEach(blog => {
                        const option = document.createElement('option');
                        option.value = blog.id;
                        option.textContent = blog.name;
                        blogSelect.appendChild(option);
                    });
                }
                this.showNotification('Blogs refreshed successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to fetch blogs');
            }
        } catch (error) {
            this.showNotification(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async fetchArticles() {
        try {
            const sitemapUrl = document.getElementById('sitemapUrl')?.value || 'https://blog.google/sitemap.xml';
            if (!sitemapUrl) {
                throw new Error('Please enter a sitemap URL');
            }

            // Validate URL format
            try {
                new URL(sitemapUrl);
            } catch (e) {
                throw new Error('Please enter a valid URL');
            }

            this.showLoading('Fetching articles...');

            // Build full API URL using window.location.origin
            const apiEndpoint = `${window.location.origin}/api/fetch-articles`;
            
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sitemap_url: sitemapUrl
                })
            });

            let data;
            try {
                data = await response.json();
            } catch (e) {
                throw new Error('Invalid response from server');
            }

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch articles');
            }

            if (data.articles?.length > 0) {
                this.articles = data.articles;
                this.updateArticlesTable();
                this.showNotification(`Successfully fetched ${data.articles.length} articles`, 'success');
            } else {
                throw new Error('No articles found in the sitemap');
            }
        } catch (error) {
            console.error('Error fetching articles:', error);
            this.showNotification(error.message, 'error');
            // Clear articles on error
            this.articles = [];
            this.updateArticlesTable();
        } finally {
            this.hideLoading();
        }
    }

    updateArticlesTable() {
        const tbody = document.querySelector('#articlesTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        this.articles.forEach(article => {
            const row = document.createElement('tr');
            row.className = 'article-row hover:bg-gray-50 cursor-pointer';
            row.dataset.id = article.id;
            
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${article.title}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${article.schedule || 'Not scheduled'}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        Pending
                    </span>
                </td>
            `;

            row.addEventListener('click', () => {
                this.toggleArticleSelection(row);
                this.showPreview(article);
            });
            tbody.appendChild(row);
        });
    }

    toggleArticleSelection(row) {
        row.classList.toggle('selected');
        row.classList.toggle('bg-blue-50');
    }

    showPreview(article) {
        const preview = document.getElementById('articlePreview');
        if (preview) {
            preview.innerHTML = article.rewritten ? article.rewritten.content : article.content;
        }
    }
}

// Initialize the application
const app = new ArticleRewriter();
