import React, { useEffect, useState } from 'react';
import { Container, Card, Button, Modal, Spinner } from 'react-bootstrap';
import '../styles/Health.css';

const apiKey = 'a8ec1a5af3df487e97ae426b8321bf0c';

function Health() {
  const [articles, setArticles] = useState([]);
  const [error, setError] = useState('');
  const [showSummary, setShowSummary] = useState(false);
  const [currentSummary, setCurrentSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(null);

  useEffect(() => {
    fetch(`https://newsapi.org/v2/top-headlines?country=us&category=health&apiKey=${apiKey}`)
      .then(response => {
        if (response.status === 429) {
          setError('Too many requests. Please try again later.');
          return;
        }
        return response.json();
      })
      .then(data => {
        if (data && data.articles) {
          setArticles(data.articles);
        } else {
          setError('No articles found.');
        }
      })
      .catch(err => {
        setError('An error occurred while fetching articles.');
      });
  }, []);

  const handleSummaryClick = async (article) => {
    setIsLoading(true);
    setSummaryError(null);
    setShowSummary(true);

    try {
      const response = await fetch('http://localhost:5000/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          article_url: article.url,
          title: article.title,
          urlToImage: article.urlToImage
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentSummary(data);
      } else {
        const errorData = await response.json();
        setSummaryError(errorData.error || 'Failed to get summary');
        setCurrentSummary({
          title: article.title,
          urlToImage: article.urlToImage,
          summary: `Error: ${errorData.error || 'Failed to get summary'}`
        });
      }
    } catch (error) {
      setSummaryError('Failed to fetch summary. Please try again.');
      setCurrentSummary({
        title: article.title,
        urlToImage: article.urlToImage,
        summary: 'Error: Failed to fetch summary. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseSummary = () => {
    setShowSummary(false);
    setCurrentSummary(null);
    setSummaryError(null);
  };

  return (
    <Container className="health">
      <h1 className="health-title">Health and Wellness Highlights</h1>
      {error && <div className="alert alert-danger">{error}</div>}
      <div className="news-row">
        {articles.length > 0 ? articles.map((article, i) => (
          <Card key={i} className="news-card">
            <div className="news-image-container">
              <Card.Img
                variant="top"
                src={article.urlToImage || '/Images/Health.jpeg'}
                className="news-image"
                onError={(e) => { e.target.onerror = null; e.target.src = '/Images/Health.jpeg'; }}
              />
            </div>
            <div className="info-section">
              <Card.Body>
                <Card.Title className="card-title">{article.title || 'No Title Available'}</Card.Title>
                <Button variant="outline-light" href={article.url} target="_blank" className="read-more-button">Read More</Button>
                <Button variant="outline-info" onClick={() => handleSummaryClick(article)} className="summary-button">Summary</Button>
              </Card.Body>
            </div>
          </Card>
        )) : (
          <p>No articles available.</p>
        )}
      </div>

      <Modal show={showSummary} onHide={handleCloseSummary} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>Article Summary</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {isLoading ? (
            <div className="text-center">
              <Spinner animation="border" role="status" />
              <p className="mt-2">Generating summary...</p>
            </div>
          ) : summaryError ? (
            <div className="alert alert-danger">{summaryError}</div>
          ) : currentSummary ? (
            <div className="summary-content">
              <h3>{currentSummary.title}</h3>
              {currentSummary.urlToImage && (
                <img
                  src={currentSummary.urlToImage}
                  alt={currentSummary.title}
                  className="summary-image"
                  style={{ maxWidth: '100%', height: 'auto', marginBottom: '15px' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              )}
              <div className="summary-text">
                <h4>Summary:</h4>
                <p>{currentSummary.summary}</p>
              </div>
              {currentSummary.url && (
                <div className="mt-3">
                  <a href={currentSummary.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                    Read Full Article
                  </a>
                </div>
              )}
            </div>
          ) : (
            <p>No summary available</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseSummary}>Close</Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default Health;
