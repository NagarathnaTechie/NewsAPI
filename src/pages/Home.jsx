import React, { useEffect, useState } from 'react';
import { Container, Card, Button, Modal, Spinner } from 'react-bootstrap';
import '../styles/Home.css';

const categories = [
  { name: 'Business', title: 'Top Business Headlines', defaultImage: 'Images/Business.jpg' },
  { name: 'Entertainment', title: 'Latest Entertainment Buzz', defaultImage: 'Images/Entertainment.jpeg' },
  { name: 'Health', title: 'Health and Wellness Highlights', defaultImage: 'Images/Health.jpeg' },
  { name: 'Science', title: 'Scientific Discoveries', defaultImage: 'Images/Science.png' },
  { name: 'Sports', title: 'Current Sports Events', defaultImage: 'Images/Sport.png' },
  { name: 'Technology', title: 'Tech Innovations', defaultImage: 'Images/Technology.webp' },
];

const apiKey = "a8ec1a5af3df487e97ae426b8321bf0c";

function Home() {
  const [newsByCategory, setNewsByCategory] = useState({});
  const [showSummary, setShowSummary] = useState(false);
  const [currentSummary, setCurrentSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNews = async () => {
      for (const { name } of categories) {
        try {
          const response = await fetch(`https://newsapi.org/v2/top-headlines?country=us&category=${name.toLowerCase()}&apiKey=${apiKey}`);
          const data = await response.json();
          if (data.articles) {
            setNewsByCategory(prevState => ({
              ...prevState,
              [name]: data.articles,
            }));
          }
        } catch (error) {
          console.error(`Error fetching news for category ${name}:`, error);
        }
      }
    };
    fetchNews();
  }, []);

  const handleSummaryClick = async (article) => {
    setIsLoading(true);
    setError(null);
    setShowSummary(true);
    
    try {
      const response = await fetch('http://localhost:5000/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
        setError(errorData.error || 'Failed to get summary');
        setCurrentSummary({ 
          title: article.title,
          urlToImage: article.urlToImage,
          summary: `Error: ${errorData.error || 'Failed to get summary'}`
        });
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
      setError('Failed to fetch summary. Please try again.');
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
    setError(null);
  };

  return (
    <Container className="home">
      {categories.map(({ name, defaultImage, title }, index) => (
        <div key={index} className="category-section">
          <div className="category-header">
            <h5 className="category-title">{title}</h5>
            <Button className="more-info-button" href={`/${name.toLowerCase()}`}>
              More {name} Info
            </Button>
          </div>
          <div className="category-divider"></div>
          <div className="news-row">
            {newsByCategory[name] && newsByCategory[name].length > 0
              ? newsByCategory[name].slice(0, 3).map((article, i) => (
                  <Card key={i} className="news-card">
                    <div className="news-image-container">
                      <Card.Img
                        variant="top"
                        src={article.urlToImage || defaultImage}
                        className="news-image"
                        onError={(e) => { e.target.onerror = null; e.target.src = defaultImage; }}
                      />
                    </div>
                    <div className="info-section">
                      <Card.Body>
                        <Card.Title className="card-title">{article.title || 'No Title Available'}</Card.Title>
                        <div className="button-group">
                          <Button variant="outline-light" href={article.url} target="_blank" className="read-more-button">
                            Read More
                          </Button>
                          <Button 
                            variant="outline-info" 
                            className="summary-button"
                            onClick={() => handleSummaryClick(article)}
                          >
                            Summary
                          </Button>
                        </div>
                      </Card.Body>
                    </div>
                  </Card>
                ))
              : (
                <p>No articles available.</p>
              )}
          </div>
        </div>
      ))}

      {/* Summary Modal */}
      <Modal show={showSummary} onHide={handleCloseSummary} size="lg" centered>
        <Modal.Header closeButton>
          <Modal.Title>Article Summary</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {isLoading ? (
            <div className="text-center">
              <Spinner animation="border" role="status">
                <span className="sr-only">Loading...</span>
              </Spinner>
              <p className="mt-2">Generating summary...</p>
            </div>
          ) : error ? (
            <div className="alert alert-danger">
              {error}
            </div>
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
          <Button variant="secondary" onClick={handleCloseSummary}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default Home;