import React, { useState } from "react";
import axios from "axios";

function App() {
  const [videoURL, setVideoURL] = useState("");
  const [summaryFormat, setSummaryFormat] = useState("Any format");
  const [refinementRequest, setRefinementRequest] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const extractVideoID = (url) => {
    try {
      const urlObj = new URL(url);
      if (urlObj.hostname === "www.youtube.com" || urlObj.hostname === "youtube.com") {
        return urlObj.searchParams.get("v");
      } else if (urlObj.hostname === "youtu.be") {
        return urlObj.pathname.substring(1);
      } else {
        return null;
      }
    } catch (error) {
      console.error("Invalid YouTube URL:", error);
      return null;
    }
  };

  const fetchSummary = async () => {
    const videoID = extractVideoID(videoURL);

    if (!videoID) {
      setSummary("Invalid YouTube URL. Please enter a valid YouTube video URL.");
      return;
    }
 
    setLoading(true);
    try {
      // // AWS API
      // const response = await axios.post(
      //   "https://1mx27lhv57.execute-api.us-east-2.amazonaws.com/summarizer",
      //   {
      //     video_id: videoID,
      //     summary_format: summaryFormat,
      //     refinement_request: refinementRequest || null,
      //   }
      // );

      // Local API
      const response = await axios.post("http://localhost:5000/summarize", {
        video_id: videoID,
        summary_format: summaryFormat,
        refinement_request: refinementRequest || null,
      });
      const data = response.data;
      setSummary(data.summary || "No summary generated.");
    } catch (error) {
      console.error("Error fetching summary:", error);
      setSummary("An error occurred while fetching the summary.");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>YouTube Summarizer</h1>
      <input
        type="text"
        placeholder="Enter YouTube video URL"
        value={videoURL}
        onChange={(e) => setVideoURL(e.target.value)}
        style={{ width: "300px", padding: "10px" }}
      />
      <br />
      <label>Select Summary Format:</label>
      <select
        value={summaryFormat}
        onChange={(e) => setSummaryFormat(e.target.value)}
        style={{ margin: "10px", padding: "10px" }}
      >
        <option value="Any format">Any format</option>
        <option value="Bullet points">Bullet points</option>
        <option value="Detailed explanations">Detailed explanations</option>
        <option value="Short/concise summaries">Short/concise summaries</option>
      </select>
      <br />
      <button onClick={fetchSummary} style={{ margin: "10px", padding: "10px" }}>
        Generate Summary
      </button>
      {loading ? <p>Loading...</p> : <p>{summary}</p>}

      {summary && (
        <div>
          <h3>Refine Summary:</h3>
          <input
            type="text"
            placeholder="Enter refinement request"
            value={refinementRequest}
            onChange={(e) => setRefinementRequest(e.target.value)}
            style={{ width: "300px", padding: "10px" }}
          />
          <button onClick={fetchSummary} style={{ margin: "10px", padding: "10px" }}>
            Refine Summary
          </button>
        </div>
      )}
    </div>
  );
}

export default App;