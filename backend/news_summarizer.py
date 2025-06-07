import os
import json
import logging
import hashlib
import time
from datetime import datetime
import nltk
import re
import numpy as np
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create directories
DATA_DIR = 'data'
SUMMARY_DIR = 'summaries'
CACHE_DIR = 'cache'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Download NLTK packages if needed
try:
    nltk.data.find('punkt')
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Initialize NLP components
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logging.info("Downloading spaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load('en_core_web_sm')

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def enhanced_preprocess(text):
    """Advanced text preprocessing"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    doc = nlp(text)
    # Keep nouns/proper nouns/verbs and lemmatize
    tokens = [token.lemma_.lower() for token in doc 
              if token.pos_ in ['NOUN', 'PROPN', 'VERB'] 
              and not token.is_stop]
    return ' '.join(tokens)

def hybrid_summarize(text, num_sentences=3, method='hybrid'):
    """Custom hybrid summarization algorithm"""
    if not text or len(text) < 100:
        return text
    
    sentences = sent_tokenize(text)
    if len(sentences) < 2:
        return text
    
    try:
        # Enhanced features
        tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        tfidf_matrix = tfidf_vectorizer.fit_transform(sentences)
        
        features = {
            'tfidf': tfidf_matrix,
            'position': np.linspace(0.1, 1, len(sentences))[:, None],  # Favor later sentences
            'length': np.array([len(sent) for sent in sentences])[:, None],
            'ner': np.array([len(nlp(sent).ents) for sent in sentences])[:, None],
            'semantic': model.encode(sentences)
        }
        
        # Combine features based on method
        if method == 'hybrid':
            weights = {'tfidf': 0.4, 'position': 0.2, 'semantic': 0.4}
            combined = np.hstack([
                weights['tfidf'] * features['tfidf'].toarray(),
                weights['position'] * features['position'],
                weights['semantic'] * features['semantic']
            ])
        elif method == 'semantic':
            combined = features['semantic']
        else:  # Basic textrank
            combined = features['tfidf'].toarray()
        
        # Create similarity matrix with diversity penalty
        similarity_matrix = cosine_similarity(combined)
        np.fill_diagonal(similarity_matrix, 0)  # Remove self-similarity
        
        # Apply graph-based ranking
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph, weight='weight')
        
        # Select top sentences with redundancy check
        ranked = sorted(((scores[i], sent) for i, sent in enumerate(sentences)), reverse=True)
        summary = []
        added_embeddings = []
        
        for score, sent in ranked:
            if len(summary) >= num_sentences:
                break
            # Check for similarity with existing sentences
            sent_embedding = model.encode([sent])[0]
            if any(cosine_similarity([e], [sent_embedding])[0][0] > 0.7 for e in added_embeddings):
                continue
            summary.append(sent)
            added_embeddings.append(sent_embedding)
        
        return ' '.join(summary)
    except Exception as e:
        logging.error(f"Error in hybrid_summarize: {str(e)}")
        return sentences[0] if sentences else text

def get_cache_key(text):
    return hashlib.md5(text.encode()).hexdigest()

def get_cached_summary(text):
    cache_key = get_cache_key(text)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                return cache_data.get('summary')
        except Exception as e:
            logging.error(f"Error reading cache: {str(e)}")
            return None
    return None

def set_cached_summary(text, summary):
    cache_key = get_cache_key(text)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'text_length': len(text),
                'summary': summary,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f)
    except Exception as e:
        logging.error(f"Error caching summary: {str(e)}")

def calculate_summary_length(text_length):
    """Calculate appropriate summary length based on text length"""
    if text_length < 100:
        return text_length, text_length
    elif text_length < 300:
        return min(50, text_length // 2), min(30, text_length // 3)
    elif text_length < 1000:
        return min(100, text_length // 3), min(50, text_length // 5)
    else:
        return 150, 75

def summarize_text(text):
    if not text or len(text) < 100:
        return text
        
    # Check cache first
    cached_summary = get_cached_summary(text)
    if cached_summary:
        logging.info("Using cached summary")
        return cached_summary
    
    try:
        start_time = time.time()
        
        # Get appropriate summary length based on text length
        num_sentences = max(3, len(sent_tokenize(text)) // 5)
        
        # Use our custom hybrid summarization algorithm
        result = hybrid_summarize(text, num_sentences=num_sentences, method='hybrid')
        
        # Cache the result
        set_cached_summary(text, result)
        
        processing_time = time.time() - start_time
        logging.info(f"Summarized text of {len(text)} chars in {processing_time:.2f} seconds")
        
        return result
    except Exception as e:
        logging.error(f"Error during summarization: {str(e)}")
        return f"Error generating summary: {str(e)}"

def summarize_article(article_data):
    content = article_data.get('full_content', article_data.get('content', article_data.get('description', '')))
    
    if not content or len(content) < 100:
        return "Content too short to summarize"
    
    return summarize_text(content)

def summarize_news_file(input_file, output_dir=SUMMARY_DIR):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error reading news file {input_file}: {str(e)}")
        return None
    
    # Prepare summary data
    summary_data = {
        "source": input_file,
        "original_category": news_data.get("category", "unknown"),
        "original_country": news_data.get("country", "unknown"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "articles": []
    }
    
    total_articles = len(news_data.get('articles', []))
    logging.info(f"Starting summarization of {total_articles} articles")
    
    for idx, article in enumerate(news_data.get('articles', []), 1):
        title = article.get('title', 'No Title')
        logging.info(f"Processing article {idx}/{total_articles}: {title[:50]}...")
        
        summary = summarize_article(article)
        
        # Add to summary data
        summary_data['articles'].append({
            "id": article.get('id', f"article-{idx}"),
            "title": title,
            "url": article.get('url', ''),
            "urlToImage": article.get('urlToImage', ''),
            "source": article.get('source', ''),
            "summary": summary
        })
    
    # Generate output filename
    input_filename = os.path.basename(input_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = input_filename.replace('.json', '')
    output_file = os.path.join(output_dir, f"summary_{base_name}_{timestamp}.json")
    
    # Save the summaries
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)
    
    logging.info(f"Summaries saved to {output_file}")
    return output_file

def get_latest_summary_file():
    summary_files = [f for f in os.listdir(SUMMARY_DIR) if f.startswith('summary_') and f.endswith('.json')]
    if not summary_files:
        return None
    
    latest_file = max(summary_files, key=lambda f: os.path.getmtime(os.path.join(SUMMARY_DIR, f)))
    return os.path.join(SUMMARY_DIR, latest_file)

# Validate the summary quality
def validate_summary(article, generated_summary):
    """Basic summary validation"""
    validation_results = {}
    
    # Length check
    validation_results['length_ratio'] = len(generated_summary) / len(article) if article else 0
    
    # Named Entity Consistency
    try:
        article_doc = nlp(article[:10000])  # Limit to avoid memory issues
        summary_doc = nlp(generated_summary)
        
        article_ents = set([ent.text.lower() for ent in article_doc.ents])
        summary_ents = set([ent.text.lower() for ent in summary_doc.ents])
        validation_results['entity_coverage'] = len(summary_ents & article_ents) / len(summary_ents) if summary_ents else 0
    except Exception as e:
        logging.error(f"Error in entity validation: {str(e)}")
        validation_results['entity_coverage'] = 0
    
    return validation_results

def evaluate_summary_quality(validation_results):
    """Evaluate summary quality based on validation metrics"""
    quality_report = []
    
    # Length check
    if 0.1 <= validation_results['length_ratio'] <= 0.3:
        quality_report.append("Good summary length")
    else:
        quality_report.append(f"Unusual length ratio: {validation_results['length_ratio']:.2f}")
    
    # Entity coverage
    if validation_results['entity_coverage'] > 0.7:
        quality_report.append("Good entity coverage")
    else:
        quality_report.append(f"Low entity coverage: {validation_results['entity_coverage']:.2f}")
    
    return quality_report