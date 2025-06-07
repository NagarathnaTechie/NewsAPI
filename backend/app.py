from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import logging
import threading
import time

from news_fetcher import fetch_news, get_latest_news_file, extract_article_content
from news_summarizer import summarize_news_file, summarize_article, get_latest_summary_file, DATA_DIR, SUMMARY_DIR

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='build')
CORS(app)

# Configuration
NEWS_API_KEY = "a8ec1a5af3df487e97ae426b8321bf0c"
DEFAULT_CATEGORY = 'technology'
DEFAULT_COUNTRY = 'us'
UPDATE_INTERVAL = 3600  # Fetch new news every hour

# Background news fetching and summarization
def background_news_update():
    """Background task to periodically fetch and summarize news"""
    while True:
        try:
            for category in ['business', 'entertainment', 'health', 'science', 'sports', 'technology']:
                country = DEFAULT_COUNTRY
                
                # Fetch news
                logging.info(f"Fetching news for {category} category...")
                news_data, news_file = fetch_news(
                    NEWS_API_KEY, 
                    category=category, 
                    country=country
                )
                
                if news_file:
                    # Summarize news
                    logging.info(f"Summarizing news from {news_file}...")
                    summary_file = summarize_news_file(news_file)
                    logging.info(f"News summarized and saved to {summary_file}")
        except Exception as e:
            logging.error(f"Error in background news update: {str(e)}")
        
        # Sleep until next update
        time.sleep(UPDATE_INTERVAL)

# Start background task
news_thread = threading.Thread(target=background_news_update, daemon=True)
news_thread.start()

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        category = request.args.get('category', DEFAULT_CATEGORY)
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if refresh:
            news_data, _ = fetch_news(NEWS_API_KEY, category=category, country=DEFAULT_COUNTRY)
            if news_data:
                return jsonify(news_data)
        else:
            latest_file = get_latest_news_file()
            if latest_file:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    news_data = json.load(f)
                return jsonify(news_data)
        
        return jsonify({'error': 'No news data available'}), 404
    except Exception as e:
        logging.error(f"Error in get_news: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/summaries', methods=['GET'])
def get_summaries():
    try:
        category = request.args.get('category', DEFAULT_CATEGORY)
        latest_file = get_latest_summary_file()
        if latest_file:
            with open(latest_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            return jsonify(summary_data)
        
        return jsonify({'error': 'No summary data available'}), 404
    except Exception as e:
        logging.error(f"Error in get_summaries: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize_single_article():
    data = request.json
    
    if not data or 'article_url' not in data:
        return jsonify({'error': 'Article URL is required'}), 400
    
    try:
        article_url = data['article_url']
        article_title = data.get('title', '')
        article_image = data.get('urlToImage', '')
        
        # Extract article content
        content = extract_article_content(article_url)
        if not content:
            return jsonify({'error': 'Could not extract article content'}), 404
            
        # Create a simplified article object for summarization
        article = {
            'title': article_title,
            'url': article_url,
            'urlToImage': article_image,
            'full_content': content
        }
        
        # Log the process
        logging.info(f"Summarizing article: {article_title[:50]}...")
        
        # Summarize the article using our custom model
        summary = summarize_article(article)
        
        # Return the summarized result
        return jsonify({
            'url': article_url,
            'title': article_title,
            'urlToImage': article_image,
            'summary': summary
        })
    
    except Exception as e:
        logging.error(f"Error in summarize_single_article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)