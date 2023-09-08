import logo from './logo.svg';
import './App.css';
import React from 'react'
import MediaPlayer from './components/MediaPlayer';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <a
          className="App-link"
          href="https://dervaish.com"
          target="_blank"
          rel="noopener noreferrer"
        >
          Dervaish
        </a>
        <p>
          Insights in Faith
        </p>
        <div>
          <MediaPlayer></MediaPlayer>
        </div>
      </header>
    </div>
  );
}

export default App;
