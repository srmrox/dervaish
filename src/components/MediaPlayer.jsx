import React, { useState, useEffect } from 'react';
import ReactPlayer from 'react-player/file';
import axios from 'axios'; // Import Axios

import './MediaPlayer.css';

const GITHUB_REPO_OWNER = 'srmrox'; // Replace with the GitHub repository owner's username
const GITHUB_REPO_NAME = 'dervaish-media'; // Replace with the GitHub repository name
const GITHUB_API_BASE_URL = 'https://api.github.com';

const MediaPlayer = () => {
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [mediaFiles, setMediaFiles] = useState([]);

  useEffect(() => {
    // Fetch the list of media files from the public GitHub repository
    axios
      .get(`${GITHUB_API_BASE_URL}/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/contents/media`)
      .then((response) => {
        const files = response.data.filter((file) => file.type === 'file');
        const fileUrls = files.map((file) => file.download_url);
        setMediaFiles(fileUrls);
      })
      .catch((error) => console.error('Error fetching media files from GitHub:', error));
  }, []);

  const handleMediaClick = (mediaUrl) => {
    setSelectedMedia(mediaUrl);
  };

  return (
    <div>
      <h1>Media Player</h1>
      <div className="media-list">
        {mediaFiles.map((mediaUrl, index) => (
          <div
            key={index}
            className={`media-item ${selectedMedia === mediaUrl ? 'active' : ''}`}
            onClick={() => handleMediaClick(mediaUrl)}
          >
            <span className="media-title">{mediaUrl.split('/').pop()}</span>
          </div>
        ))}
      </div>
      {selectedMedia && (
        <div className="media-player">
          <ReactPlayer url={selectedMedia} controls playing />
        </div>
      )}
    </div>
  );
};

export default MediaPlayer;
