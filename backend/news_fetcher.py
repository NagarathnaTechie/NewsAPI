import requests
import json
import os
from datetime import datetime
import logging
from newspaper import Article
import nltk
import hashlib
import nltk

try:
    nltk.data.find('tokenizers/punkt_tab/english')
except LookupError:
    nltk.download('punkt_tab')


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create directories
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Download NLTK packages if needed
try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt')

def fetch_news(api_key, category='general', country='us', page_size=10):
    base_url = "https://newsapi.org/v2/top-headlines"
    
    params = {
        'country': country,
        'category': category,
        'pageSize': page_size,
        'apiKey': api_key
    }
    
    try:
        logging.info(f"Fetching news for category: {category}, country: {country}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        news_data = response.json()
        
        # Create simplified version with only needed fields
        simplified_news = {
            "status": news_data.get("status"),
            "totalResults": news_data.get("totalResults"),
            "category": category,
            "country": country,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "articles": []
        }
        
        # Process and enrich each article
        for article in news_data.get('articles', []):
            article_url = article.get('url', '')
            if not article_url:
                continue
                
            try:
                # Extract full content using newspaper3k
                full_content = extract_article_content(article_url)
                
                # Create article ID for reference
                article_id = hashlib.md5(article_url.encode()).hexdigest()
                
                # Add to simplified news data
                simplified_news['articles'].append({
                    "id": article_id,
                    "title": article.get('title', 'No Title'),
                    "url": article_url,
                    "publishedAt": article.get('publishedAt', ''),
                    "urlToImage": article.get('urlToImage', ''),
                    "source": article.get('source', {}).get('name', ''),
                    "description": article.get('description', ''),
                    "content": article.get('content', ''),
                    "full_content": full_content if full_content else article.get('content', article.get('description', ''))
                })
            except Exception as e:
                logging.error(f"Error processing article {article_url}: {str(e)}")
        
        # Save the fetched and enhanced data with a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_DIR}/news_{category}_{country}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(simplified_news, f, indent=4, ensure_ascii=False)
        
        logging.info(f"News data saved to {filename}")
        return simplified_news, filename
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news: {str(e)}")
        return None, None

def extract_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Check if we got meaningful content
        if article.text and len(article.text) > 100:
            return article.text
        return None
    except Exception as e:
        logging.error(f"Failed to extract content from {url}: {str(e)}")
        return None

def get_latest_news_file():
    news_files = [f for f in os.listdir(DATA_DIR) if f.startswith('news_') and f.endswith('.json')]
    if not news_files:
        return None
    
    # Get the latest news file
    latest_file = max(news_files, key=lambda f: os.path.getmtime(os.path.join(DATA_DIR, f)))
    return os.path.join(DATA_DIR, latest_file)