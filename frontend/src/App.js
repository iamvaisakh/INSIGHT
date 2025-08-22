import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [fileKey, setFileKey] = useState('');
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('initial');

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first!');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    setStatus('uploading');
    setMessages([{ sender: 'bot', text: `Uploading "${file.name}"...` }]);

    try {
      const uploadResponse = await axios.post(`${API_URL}/upload/`, formData);
      setStatus('processing');
      setMessages(prev => [...prev, { sender: 'bot', text: 'Processing document... This may take a moment.' }]);
      
      setFileKey(uploadResponse.data.file_key);
      setStatus('ready');
      setMessages(prev => [...prev, { sender: 'bot', text: `Document processed! You can now ask questions about "${uploadResponse.data.file_key}".` }]);
    } catch (error) {
      console.error('Error uploading file:', error);
      setStatus('initial');
      setMessages([{ sender: 'bot', text: 'Error uploading or processing file. Please try again.' }]);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query || !fileKey) return;

    const userMessage = { sender: 'user', text: query };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setStatus('querying');

    try {
      const queryData = new FormData();
      queryData.append('file_key', fileKey);
      queryData.append('question', query);

      const response = await axios.post(`${API_URL}/query/`, queryData);
      
      const botMessage = { sender: 'bot', text: response.data.answer };
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error('Error querying:', error);
      const errorMessage = { sender: 'bot', text: 'Sorry, I encountered an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setStatus('ready');
    }
  };

  return (
    <div className="bg-gray-900 text-white min-h-screen flex flex-col items-center p-4 font-sans">
      <div className="w-full max-w-3xl flex flex-col h-screen bg-gray-800 rounded-lg shadow-xl">
        <header className="p-4 border-b border-gray-700">
          <h1 className="text-2xl font-bold text-center">📄 DocuMentor</h1>
          <p className="text-center text-gray-400">Upload a PDF and ask it questions.</p>
        </header>

        {status === 'initial' && (
          <div className="flex-grow flex flex-col items-center justify-center p-8">
            <div className="w-full max-w-md bg-gray-700 p-8 rounded-lg text-center">
              <h2 className="text-xl mb-4">Step 1: Upload Your PDF</h2>
              <input 
                type="file" 
                onChange={handleFileChange} 
                accept=".pdf" 
                className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              />
              <button 
                onClick={handleUpload} 
                disabled={!file}
                className="mt-6 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg transition-colors"
              >
                Upload & Process
              </button>
            </div>
          </div>
        )}

        {status !== 'initial' && (
          <main className="flex-grow p-4 overflow-y-auto">
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-prose p-3 rounded-lg ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                  </div>
                </div>
              ))}
              { (status === 'uploading' || status === 'processing' || status === 'querying') && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse [animation-delay:0.2s]"></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse [animation-delay:0.4s]"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </main>
        )}

        {status === 'ready' && (
           <footer className="p-4 border-t border-gray-700">
            <form onSubmit={handleQuery} className="flex space-x-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about the document..."
                className="flex-grow bg-gray-700 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors">
                Send
              </button>
            </form>
          </footer>
        )}

      </div>
    </div>
  );
}

export default App;