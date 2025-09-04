import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatContainer from './components/chat/ChatContainer';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<ChatContainer />} />
            <Route path="/chat" element={<ChatContainer />} />
            <Route path="*" element={<ChatContainer />} />
          </Routes>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
