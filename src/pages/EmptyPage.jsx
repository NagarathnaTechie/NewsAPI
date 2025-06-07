// src/pages/EmptyPage.js
import React from "react";
import { Container } from "react-bootstrap";

function EmptyPage({ title }) {
  return (
    <Container className="text-center mt-5">
      <h2>{title}</h2>
      <p>Content for the {title} page will go here.</p>
    </Container>
  );
}

export default EmptyPage;
